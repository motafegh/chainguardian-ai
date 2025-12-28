"""
AST Feature Extractor - FIXED v3


Extracts 19 code structure features from Solidity AST.


FIXES APPLIED:
1. Added fuzzy matching for contract names (22_empty_contract → EmptyContract)
2. Added fallback to first non-interface contract
3. Better error logging and handling
4. Consistent with graph_extractor.py behavior
5. CRITICAL FIX: Calculate complexity from CODE STRUCTURE, not detector results
   - Eliminates target leakage (was using severity counts)
   - Now uses: function count, cyclomatic complexity, LOC, state vars


Author: Ali - ChainGuardian AI Project
"""


from pathlib import Path
from typing import Dict, Tuple
import logging


logger = logging.getLogger(__name__)


# NOTE: Slither is imported LAZILY inside __init__ to make this module testable
# without Slither installed. This allows fast unit tests with mocks.



class ASTFeatureExtractor:
    """
    Extract code structure features from Solidity AST.
    
    Features extracted (19 total):
    - Function counts (total, payable, high complexity)
    - Call metrics (external calls, low-level calls, library calls)
    - Code quality (LOC, comments, comment ratio)
    - Structure (state vars, modifiers, contracts in file)
    - Complexity (cyclomatic, avg complexity, complexity category)
    - Inheritance depth
    
    IMPORTANT: Complexity is calculated from CODE STRUCTURE ONLY,
    not from vulnerability detector results (no target leakage).
    """
    
    def __init__(self, contract_path: Path, slither_obj=None):
        """
        Initialize AST extractor.
        
        Args:
            contract_path: Path to .sol file
            slither_obj: Pre-compiled Slither object (recommended to avoid re-compilation)
        """
        self.contract_path = contract_path
        
        if slither_obj is not None:
            self.slither = slither_obj
            logger.debug(f"Using pre-compiled Slither for {contract_path.name}")
        else:
            # LAZY IMPORT: Only import Slither when actually compiling
            # This allows tests to import this module without Slither installed
            from slither import Slither
            
            logger.warning(
                f"Compiling {contract_path.name} in AST extractor - "
                f"consider passing slither_obj to avoid re-compilation"
            )
            self.slither = Slither(
                str(contract_path),
                solc="solc",
                solc_disable_warnings=True
            )
        
        logger.info(f"Initialized AST extractor for {contract_path.name}")


    def extract_features(self, contract_name: str) -> Dict[str, int]:
        """
        Extract all 19 AST features for a contract.
        
        FIXED: Now handles contract name mismatches with fuzzy matching.
        FIXED: Calculates complexity from code structure (no target leakage).
        
        Args:
            contract_name: Name of contract to analyze (e.g., "EmptyContract")
        
        Returns:
            Dict with 19 features:
            - 17 original features (all integers/floats)
            - complexity_level (0-3: simple, moderate, complex, critical)
            - contract_complexity_category (string: for logging)
        """
        # Initialize feature dict with default values
        features = {
            'num_functions': 0,
            'num_external_calls': 0,
            'num_state_vars': 0,
            'num_modifiers': 0,
            'max_cyclomatic_complexity': 0,
            'num_low_level_calls': 0,
            'lines_of_code': 0,
            'num_contracts_in_file': 1,
            'num_dependencies': 0,
            'avg_function_complexity': 0.0,
            'num_functions_high_complexity': 0,
            'num_comments': 0,
            'comment_to_code_ratio': 0.0,
            'num_payable_functions': 0,
            'num_library_calls': 0,
            'inheritance_depth': 0,
            'num_unused_functions': 0,
            'complexity_level': 0,  # NEW: 0-3 integer for ML
            'contract_complexity_category': 'simple',  # NEW: String for logging
        }


        # ================================================================
        # FIXED: ROBUST CONTRACT LOOKUP (3-stage fallback)
        # ================================================================
        
        # Stage 1: Exact match
        contract = None
        for c in self.slither.contracts:
            if c.name == contract_name:
                contract = c
                logger.debug(f"✓ Exact match: '{contract_name}'")
                break


        # Stage 2: Fuzzy match (case-insensitive, ignore underscores/dashes)
        if not contract:
            logger.info(
                f"Exact match failed for '{contract_name}', trying fuzzy match..."
            )
            name_clean = contract_name.lower().replace('_', '').replace('-', '')
            
            for c in self.slither.contracts:
                c_clean = c.name.lower().replace('_', '').replace('-', '')
                # Check if either name contains the other
                if c_clean in name_clean or name_clean in c_clean:
                    contract = c
                    logger.info(f"✓ Fuzzy matched '{contract_name}' → '{c.name}'")
                    break
        
        # Stage 3: Fallback to first non-interface contract
        if not contract and self.slither.contracts:
            logger.info(
                f"Fuzzy match failed for '{contract_name}', "
                f"using first non-interface contract..."
            )
            for c in self.slither.contracts:
                # Skip interfaces and libraries
                if not c.is_interface and not c.is_library:
                    contract = c
                    logger.info(f"✓ Using first contract '{c.name}' for '{contract_name}'")
                    break


        # Final check: No suitable contract found
        if not contract:
            logger.error(
                f"❌ No suitable contract found for '{contract_name}' "
                f"in {self.contract_path.name}"
            )
            logger.debug(
                f"Available contracts: "
                f"{[c.name for c in self.slither.contracts]}"
            )
            return features  # Return zeros


        # ================================================================
        # EXTRACT FEATURES (Original logic - unchanged)
        # ================================================================
        
        # Basic counts
        features['num_functions'] = len(contract.functions_declared)
        features['num_state_vars'] = len(contract.state_variables_declared)
        features['num_modifiers'] = len(contract.modifiers_declared)


        # Function analysis
        complexity_scores = []
        payable_count = 0
        high_complexity_count = 0


        for func in contract.functions_declared:
            # Count external calls
            features['num_external_calls'] += len(func.external_calls_as_expressions)
            
            # Count low-level calls
            features['num_low_level_calls'] += len(func.low_level_calls)
            
            # Calculate complexity
            complexity = self._calculate_complexity(func)
            complexity_scores.append(complexity)
            
            # Track max complexity
            features['max_cyclomatic_complexity'] = max(
                features['max_cyclomatic_complexity'],
                complexity
            )
            
            # Count high complexity functions (>10)
            if complexity > 10:
                high_complexity_count += 1
            
            # Count payable functions
            if func.payable:
                payable_count += 1


        # Average complexity
        if complexity_scores:
            features['avg_function_complexity'] = sum(complexity_scores) / len(complexity_scores)


        features['num_functions_high_complexity'] = high_complexity_count
        features['num_payable_functions'] = payable_count


        # ================================================================
        # CODE QUALITY METRICS (LOC, comments)
        # ================================================================
        
        logger.debug(f"Extracting code quality metrics for {contract_name}...")


        try:
            source_code = self.contract_path.read_text(encoding='utf-8')
            lines = source_code.split('\n')
            
            # Count non-empty lines
            non_empty_lines = [line for line in lines if line.strip()]
            features['lines_of_code'] = len(non_empty_lines)
            
            # Count comment lines
            comment_lines = 0
            in_block_comment = False


            for line in lines:
                stripped = line.strip()
                
                # Handle block comments /* ... */
                if '/*' in stripped:
                    in_block_comment = True
                    comment_lines += 1
                    if '*/' in stripped:
                        in_block_comment = False
                    continue
                
                if in_block_comment:
                    comment_lines += 1
                    if '*/' in stripped:
                        in_block_comment = False
                    continue
                
                # Handle line comments //
                if stripped.startswith('//'):
                    comment_lines += 1


            features['num_comments'] = comment_lines
            
            # Calculate comment ratio
            if features['lines_of_code'] > 0:
                features['comment_to_code_ratio'] = comment_lines / features['lines_of_code']


        except Exception as e:
            logger.warning(f"Failed to count LOC for {contract_name}: {e}")


        # ================================================================
        # FILE-LEVEL METRICS
        # ================================================================
        
        # Count contracts in file
        features['num_contracts_in_file'] = len(self.slither.contracts)


        # Count dependencies (imports)
        try:
            features['num_dependencies'] = len(
                self.slither.crytic_compile.compilation_units
            )
        except (AttributeError, TypeError):
            features['num_dependencies'] = 0


        # Count library calls
        library_calls = 0
        for func in contract.functions_declared:
            try:
                library_calls += len(func.library_calls)
            except (AttributeError, TypeError):
                pass
        features['num_library_calls'] = library_calls


        # ================================================================
        # INHERITANCE DEPTH
        # ================================================================
        
        depth = 0
        current = contract
        visited = set()


        while current and current not in visited:
            visited.add(current)
            if current.inheritance:
                depth += 1
                current = current.inheritance[0]
            else:
                break


        features['inheritance_depth'] = depth
        
        # Unused functions (placeholder - complex to detect accurately)
        features['num_unused_functions'] = 0


        # ================================================================
        # NEW: CALCULATE COMPLEXITY FROM CODE STRUCTURE (NO TARGET LEAKAGE!)
        # ================================================================
        
        complexity_score, complexity_category = self._calculate_code_complexity(features)
        features['complexity_level'] = complexity_score  # 0-3 for ML
        features['contract_complexity_category'] = complexity_category  # String for logging
        
        # ================================================================
        # LOGGING
        # ================================================================
        
        logger.info(
            f"✓ AST features for '{contract.name}': "
            f"{features['lines_of_code']} LOC, "
            f"{features['num_functions']} functions, "
            f"complexity={complexity_category}, "
            f"{features['num_comments']} comments "
            f"({features['comment_to_code_ratio']:.2%} ratio)"
        )


        return features


    def _calculate_complexity(self, function) -> int:
        """
        Calculate cyclomatic complexity for a function.
        
        Complexity = 1 + number of decision points (if, require, loop)
        
        Args:
            function: Slither Function object
        
        Returns:
            Integer complexity score
        """
        complexity = 1  # Base complexity
        
        for node in function.nodes:
            node_type = str(node.type)
            # Increment for each decision point
            if any(keyword in node_type.lower() for keyword in ['if', 'require', 'loop']):
                complexity += 1
        
        return complexity


    def _calculate_code_complexity(self, features: Dict) -> Tuple[int, str]:
        """
        Calculate contract complexity from CODE STRUCTURE ONLY.
        
        CRITICAL: Does NOT use detector results (no target leakage).
        Uses only code metrics extracted from AST.
        
        Metrics used (weights in parentheses):
        - Number of functions (30%)
        - Cyclomatic complexity (25%)
        - Lines of code (20%)
        - State variables (15%)
        - External calls (10%)
        
        Args:
            features: Dict with extracted AST features
            
        Returns:
            Tuple of (complexity_level: int 0-3, category: str)
            - 0 = 'simple' (score 0-24)
            - 1 = 'moderate' (score 25-49)
            - 2 = 'complex' (score 50-74)
            - 3 = 'critical' (score 75-100)
        """
        score = 0
        
        # ================================================================
        # 1. FUNCTION COUNT (0-30 points)
        # ================================================================
        # More functions = more complexity
        num_functions = features.get('num_functions', 0)
        
        if num_functions > 20:
            score += 30
        elif num_functions > 10:
            score += 20
        elif num_functions > 5:
            score += 10
        elif num_functions > 2:
            score += 5
        
        # ================================================================
        # 2. CYCLOMATIC COMPLEXITY (0-25 points)
        # ================================================================
        # Measures control flow complexity (if/else/loops)
        max_complexity = features.get('max_cyclomatic_complexity', 0)
        avg_complexity = features.get('avg_function_complexity', 0)
        
        if max_complexity > 20:
            score += 25
        elif max_complexity > 15:
            score += 20
        elif max_complexity > 10:
            score += 15
        elif max_complexity > 5:
            score += 10
        elif avg_complexity > 3:
            score += 5
        
        # ================================================================
        # 3. LINES OF CODE (0-20 points)
        # ================================================================
        # More code = more surface area for bugs
        loc = features.get('lines_of_code', 0)
        
        if loc > 1000:
            score += 20
        elif loc > 500:
            score += 15
        elif loc > 200:
            score += 10
        elif loc > 100:
            score += 5
        
        # ================================================================
        # 4. STATE MANAGEMENT (0-15 points)
        # ================================================================
        # More state variables = more state management complexity
        state_vars = features.get('num_state_vars', 0)
        
        if state_vars > 20:
            score += 15
        elif state_vars > 15:
            score += 12
        elif state_vars > 10:
            score += 10
        elif state_vars > 5:
            score += 5
        
        # ================================================================
        # 5. EXTERNAL INTERACTIONS (0-10 points)
        # ================================================================
        # External calls = interaction with other contracts (risky)
        external_calls = features.get('num_external_calls', 0)
        low_level_calls = features.get('num_low_level_calls', 0)
        
        if external_calls > 15 or low_level_calls > 5:
            score += 10
        elif external_calls > 10 or low_level_calls > 3:
            score += 7
        elif external_calls > 5 or low_level_calls > 0:
            score += 5
        
        # ================================================================
        # BONUS FACTORS (0-5 points each)
        # ================================================================
        
        # High complexity functions
        if features.get('num_functions_high_complexity', 0) > 3:
            score += 5
        
        # Deep inheritance (can hide complexity)
        if features.get('inheritance_depth', 0) > 3:
            score += 5
        
        # Many contracts in one file (architectural complexity)
        if features.get('num_contracts_in_file', 1) > 5:
            score += 5
        
        # Payable functions (handle money = higher stakes)
        if features.get('num_payable_functions', 0) > 2:
            score += 5
        
        # ================================================================
        # MAP SCORE TO CATEGORY
        # ================================================================
        # Score range: 0-100+ (but capped at 100 for practical purposes)
        score = min(score, 100)
        
        if score >= 75:
            return (3, 'critical')
        elif score >= 50:
            return (2, 'complex')
        elif score >= 25:
            return (1, 'moderate')
        else:
            return (0, 'simple')
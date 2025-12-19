"""
Semantic Security Pattern Analyzer
Detects safety patterns and anti-patterns using Slither's analysis
"""

from typing import Dict, Any, Set, List
from slither.core.declarations import Function, Contract
from slither.core.cfg.node import Node, NodeType
from slither.slithir.operations import (
    HighLevelCall, LowLevelCall, Transfer, Send,
    Assignment, Binary, Index
)
import logging

logger = logging.getLogger(__name__)


class SemanticAnalyzer:
    """Analyze semantic security patterns in smart contracts."""
    
    def __init__(self, contract: Contract):
        self.contract = contract
        
    def analyze(self) -> Dict[str, Any]:
        """Extract all semantic security features."""
        return {
            # CEI Pattern Analysis
            'cei_violations': self._count_cei_violations(),
            'cei_safe_functions': self._count_cei_safe_functions(),
            'cei_pattern_score': self._calculate_cei_score(),
            
            # Reentrancy Protection
            'has_reentrancy_guard': self._detect_reentrancy_guard(),
            'functions_with_reentrancy_guard': self._count_guarded_functions(),
            
            # State-Call Ordering
            'state_before_call_count': self._count_safe_state_modifications(),
            'state_after_call_count': self._count_unsafe_state_modifications(),
            
            # Return Value Handling
            'unchecked_calls_in_critical_context': self._count_dangerous_unchecked_calls(),
        }
    
    def _count_cei_violations(self) -> int:
        """
        Count functions that violate CEI pattern:
        State modification AFTER external call = violation
        """
        violations = 0
        
        for func in self.contract.functions:
            if func.is_constructor or func.view or func.pure:
                continue
                
            # Get all nodes in function
            nodes = func.nodes
            
            # Track if we've seen external call
            seen_external_call = False
            
            for node in nodes:
                # Check if this node is external call
                if self._is_external_call(node):
                    seen_external_call = True
                
                # Check if this node modifies state AFTER external call
                if seen_external_call and self._modifies_state(node):
                    violations += 1
                    break  # Count once per function
        
        return violations
    
    def _count_cei_safe_functions(self) -> int:
        """Count functions that properly follow CEI pattern."""
        safe_count = 0
        
        for func in self.contract.functions:
            if func.is_constructor or func.view or func.pure:
                continue
            
            has_external_call = False
            has_state_mod = False
            state_before_call = True
            
            for node in func.nodes:
                if self._modifies_state(node):
                    has_state_mod = True
                    if has_external_call:
                        state_before_call = False
                
                if self._is_external_call(node):
                    has_external_call = True
            
            # Safe if: (no calls) OR (state modified before calls)
            if has_external_call and has_state_mod and state_before_call:
                safe_count += 1
        
        return safe_count
    
    def _calculate_cei_score(self) -> float:
        """
        CEI safety score (0-1):
        1.0 = perfect CEI compliance
        0.0 = all functions violate CEI
        """
        violations = self._count_cei_violations()
        safe = self._count_cei_safe_functions()
        
        total = violations + safe
        if total == 0:
            return 1.0  # No risky functions
        
        return safe / total
    
    def _detect_reentrancy_guard(self) -> bool:
        """
        Detect if contract uses ReentrancyGuard pattern:
        - Has 'nonReentrant' modifier, OR
        - Has mutex/lock state variable
        """
        # Check for nonReentrant modifier
        for modifier in self.contract.modifiers:
            if 'nonreentrant' in modifier.name.lower():
                return True
        
        # Check for mutex pattern
        for var in self.contract.state_variables:
            name_lower = var.name.lower()
            if any(pattern in name_lower for pattern in ['lock', 'mutex', 'guard', 'entered']):
                return True
        
        return False
    
    def _count_guarded_functions(self) -> int:
        """Count functions protected by reentrancy guard."""
        if not self._detect_reentrancy_guard():
            return 0
        
        guarded = 0
        for func in self.contract.functions:
            if func.is_constructor or func.view or func.pure:
                continue
            
            # Check if function has nonReentrant modifier
            for modifier in func.modifiers:
                if 'nonreentrant' in modifier.name.lower():
                    guarded += 1
                    break
        
        return guarded
    
    def _count_safe_state_modifications(self) -> int:
        """Count state modifications that occur BEFORE external calls."""
        safe_count = 0
        
        for func in self.contract.functions:
            if func.is_constructor or func.view or func.pure:
                continue
            
            seen_state_mod = False
            seen_call = False
            
            for node in func.nodes:
                if self._modifies_state(node):
                    seen_state_mod = True
                
                if self._is_external_call(node):
                    seen_call = True
                    if seen_state_mod:
                        safe_count += 1
                    break
        
        return safe_count
    
    def _count_unsafe_state_modifications(self) -> int:
        """Count state modifications that occur AFTER external calls."""
        return self._count_cei_violations()
    
    def _count_dangerous_unchecked_calls(self) -> int:
        """
        Count unchecked low-level calls in critical context:
        - Before state update (money could be lost)
        - Return value not checked
        """
        dangerous = 0
        
        for func in self.contract.functions:
            if func.view or func.pure:
                continue
            
            for node in func.nodes:
                if not self._is_low_level_call(node):
                    continue
                
                # Check if return value is used
                if not self._return_value_checked(node):
                    # Check if followed by state modification
                    if self._has_state_modification_after(func, node):
                        dangerous += 1
        
        return dangerous
    
    # === Helper Methods ===
    
    def _is_external_call(self, node: Node) -> bool:
        """Check if node contains external call."""
        for ir in node.irs:
            if isinstance(ir, (HighLevelCall, LowLevelCall, Transfer, Send)):
                return True
        return False
    
    def _is_low_level_call(self, node: Node) -> bool:
        """Check if node contains low-level call."""
        for ir in node.irs:
            if isinstance(ir, LowLevelCall):
                return True
        return False
    
    def _modifies_state(self, node: Node) -> bool:
        """Check if node modifies contract state."""
        # Check for state variable writes
        for var in node.state_variables_written:
            return True
        return False
    
    def _return_value_checked(self, node: Node) -> bool:
        """Check if call's return value is checked."""
        # Simple heuristic: look for require/assert/if in same or next node
        # In production, would need more sophisticated analysis
        for ir in node.irs:
            if isinstance(ir, LowLevelCall):
                # Check if assigned to variable
                if hasattr(ir, 'lvalue') and ir.lvalue:
                    return True
        return False
    
    def _has_state_modification_after(self, func: Function, call_node: Node) -> bool:
        """Check if state is modified after this call node."""
        found_call = False
        
        for node in func.nodes:
            if node == call_node:
                found_call = True
                continue
            
            if found_call and self._modifies_state(node):
                return True
        
        return False


def extract_semantic_features(contract: Contract) -> Dict[str, Any]:
    """Convenience function to extract all semantic features."""
    analyzer = SemanticAnalyzer(contract)
    return analyzer.analyze()

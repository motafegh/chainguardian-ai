"""
Graph Feature Extractor - CFG, Call Graph, DFG Analysis
Extracts 25 graph-theoretic features from smart contracts.
"""
from typing import Dict, Set
import networkx as nx
from slither import Slither
from slither.core.declarations import Contract, Function
from slither.core.cfg.node import NodeType
import logging

logger = logging.getLogger(__name__)

class GraphFeatureExtractor:
    """Extract 25 graph-based features from smart contracts."""
    
    def __init__(self, slither_obj: Slither):
        """Initialize with pre-compiled Slither object."""
        self.slither = slither_obj
    
    def extract_features(self, contract_name: str) -> Dict:
        """Extract all 25 graph features."""
        # Find target contract with fuzzy matching
        target_contract = None
        
        # Try exact match first
        for contract in self.slither.contracts:
            if contract.name == contract_name:
                target_contract = contract
                break
        
        # Fuzzy match: case-insensitive, ignore underscores/dashes
        if not target_contract:
            name_clean = contract_name.lower().replace('_', '').replace('-', '')
            for contract in self.slither.contracts:
                contract_clean = contract.name.lower().replace('_', '').replace('-', '')
                if contract_clean in name_clean or name_clean in contract_clean:
                    target_contract = contract
                    logger.info(f"Fuzzy matched '{contract_name}' -> '{contract.name}'")
                    break
        
        # Use first non-interface contract if nothing matched
        if not target_contract and self.slither.contracts:
            for contract in self.slither.contracts:
                if not contract.is_interface and not contract.is_library:
                    target_contract = contract
                    logger.info(f"Using first contract '{contract.name}' for '{contract_name}'")
                    break
        
        if not target_contract:
            logger.warning(f"No suitable contract found for {contract_name}")
            return self._default_features()
        
        try:
            cfg_features = self._extract_cfg_features(target_contract)
            call_features = self._extract_call_graph_features(target_contract)
            df_features = self._extract_dataflow_features(target_contract)
            
            combined = {**cfg_features, **call_features, **df_features}
            
            logger.debug(
                f"Graph features: {combined['cfg_num_cycles']} cycles, "
                f"{combined['cg_num_external_calls']} ext calls"
            )
            
            return combined
        
        except Exception as e:
            logger.error(f"Graph extraction failed: {e}")
            return self._default_features()
    
    def _extract_cfg_features(self, contract: Contract) -> Dict:
        """Extract Control Flow Graph features (8 features)."""
        features = {
            'cfg_num_nodes': 0,
            'cfg_num_edges': 0,
            'cfg_num_cycles': 0,
            'cfg_max_depth': 0,
            'cfg_avg_branching': 0.0,
            'cfg_has_complex_loops': False,
            'cfg_num_exit_points': 0,
            'cfg_cyclomatic_total': 0
        }
        
        total_nodes = 0
        total_edges = 0
        total_complexity = 0
        max_depth = 0
        has_complex = False
        exit_points = 0
        
        for func in contract.functions_declared:
            if not func.nodes:
                continue
            
            # Build CFG as NetworkX graph
            G = nx.DiGraph()
            
            for node in func.nodes:
                G.add_node(node)
                total_nodes += 1
                
                # Count edges
                for son in node.sons:
                    G.add_edge(node, son)
                    total_edges += 1
                
                # Count exit points (return, revert, throw)
                node_type_str = str(node.type)
                if any(kw in node_type_str.lower() for kw in ['return', 'throw']):
                    exit_points += 1
            
            # Detect cycles in this function
            try:
                cycles = list(nx.simple_cycles(G))
                features['cfg_num_cycles'] += len(cycles)
                
                # Complex loops: nested loops (cycle within cycle)
                if len(cycles) > 1:
                    has_complex = True
            except:
                pass
            
            # Calculate max depth (longest path)
            try:
                if len(G.nodes) > 0:
                    # Find entry node (usually first node)
                    entry = func.entry_point if func.entry_point else list(G.nodes)[0]
                    # Calculate longest path from entry
                    lengths = nx.single_source_shortest_path_length(G, entry)
                    func_max_depth = max(lengths.values()) if lengths else 0
                    max_depth = max(max_depth, func_max_depth)
            except:
                pass
            
            # Cyclomatic complexity for this function
            complexity = 1  # Base
            for node in func.nodes:
                node_type = str(node.type)
                if any(kw in node_type.lower() for kw in ['if', 'loop', 'require']):
                    complexity += 1
            total_complexity += complexity
        
        features['cfg_num_nodes'] = total_nodes
        features['cfg_num_edges'] = total_edges
        features['cfg_max_depth'] = max_depth
        features['cfg_has_complex_loops'] = has_complex
        features['cfg_num_exit_points'] = exit_points
        features['cfg_cyclomatic_total'] = total_complexity
        
        # Average branching factor
        if total_nodes > 0:
            features['cfg_avg_branching'] = total_edges / total_nodes
        
        return features
    
    def _extract_call_graph_features(self, contract: Contract) -> Dict:
        """Extract Call Graph features (10 features)."""
        features = {
            'cg_num_nodes': 0,
            'cg_num_edges': 0,
            'cg_max_call_depth': 0,
            'cg_num_external_calls': 0,
            'cg_external_call_ratio': 0.0,
            'cg_has_cyclic_calls': False,
            'cg_num_public_entry_points': 0,
            'cg_num_internal_functions': 0,
            'cg_avg_calls_per_function': 0.0,
            'cg_num_leaf_functions': 0
        }
        
        functions = contract.functions_declared
        if not functions:
            return features
        
        # Build call graph
        G = nx.DiGraph()
        
        for func in functions:
            G.add_node(func.name)
            features['cg_num_nodes'] += 1
            
            # Count visibility
            if func.visibility in ['public', 'external']:
                features['cg_num_public_entry_points'] += 1
            else:
                features['cg_num_internal_functions'] += 1
            
            # Count calls
            internal_calls = func.internal_calls
            external_calls = func.external_calls_as_expressions
            
            # Add edges for internal calls
            for called_func in internal_calls:
                if hasattr(called_func, 'name'):
                    G.add_edge(func.name, called_func.name)
                    features['cg_num_edges'] += 1
            
            # Count external calls
            features['cg_num_external_calls'] += len(external_calls)
        
        # Calculate call depth (longest path in call graph)
        try:
            if len(G.nodes) > 0:
                # Find all paths from public functions
                public_funcs = [f for f in functions if f.visibility in ['public', 'external']]
                max_depth = 0
                for pub_func in public_funcs:
                    try:
                        lengths = nx.single_source_shortest_path_length(G, pub_func.name)
                        if lengths:
                            max_depth = max(max_depth, max(lengths.values()))
                    except:
                        pass
                features['cg_max_call_depth'] = max_depth
        except:
            pass
        
        # Detect cyclic calls (recursion)
        try:
            cycles = list(nx.simple_cycles(G))
            features['cg_has_cyclic_calls'] = len(cycles) > 0
        except:
            pass
        
        # Leaf functions (no outgoing calls)
        for node in G.nodes:
            if G.out_degree(node) == 0:
                features['cg_num_leaf_functions'] += 1
        
        # External call ratio
        total_calls = features['cg_num_edges'] + features['cg_num_external_calls']
        if total_calls > 0:
            features['cg_external_call_ratio'] = features['cg_num_external_calls'] / total_calls
        
        # Average calls per function
        if features['cg_num_nodes'] > 0:
            features['cg_avg_calls_per_function'] = features['cg_num_edges'] / features['cg_num_nodes']
        
        return features
    
    def _extract_dataflow_features(self, contract: Contract) -> Dict:
        """Extract Data Flow Graph features (7 features)."""
        features = {
            'dfg_num_state_vars': 0,
            'dfg_num_tainted_flows': 0,
            'dfg_has_cross_function_flow': False,
            'dfg_num_sensitive_sinks': 0,
            'dfg_num_external_sources': 0,
            'dfg_taint_to_sink_ratio': 0.0,
            'dfg_num_unvalidated_inputs': 0
        }
        
        # Count state variables
        features['dfg_num_state_vars'] = len(contract.state_variables_declared)
        
        # Analyze each function for data flows
        state_writers = set()
        state_readers = set()
        
        for func in contract.functions_declared:
            # State variable usage
            vars_written = func.state_variables_written
            vars_read = func.state_variables_read
            
            for var in vars_written:
                state_writers.add(var.name)
            for var in vars_read:
                state_readers.add(var.name)
            
            # External sources (taint sources)
            if func.parameters:
                features['dfg_num_external_sources'] += len(func.parameters)
            
            # Sensitive sinks
            for call in func.external_calls_as_expressions:
                call_str = str(call)
                if any(sink in call_str.lower() for sink in ['transfer', 'send', 'call', 'delegatecall', 'selfdestruct']):
                    features['dfg_num_sensitive_sinks'] += 1
            
            # Tainted flows (simplified: parameters used in sensitive operations)
            if func.parameters and (func.external_calls_as_expressions or vars_written):
                features['dfg_num_tainted_flows'] += 1
        
        # Cross-function flows (state vars both read and written)
        cross_flows = state_writers.intersection(state_readers)
        features['dfg_has_cross_function_flow'] = len(cross_flows) > 0
        
        # Taint-to-sink ratio
        if features['dfg_num_sensitive_sinks'] > 0:
            features['dfg_taint_to_sink_ratio'] = features['dfg_num_tainted_flows'] / features['dfg_num_sensitive_sinks']
        
        # Unvalidated inputs (functions with params but no require/assert)
        for func in contract.functions_declared:
            if func.parameters:
                has_validation = False
                for node in func.nodes:
                    node_type = str(node.type)
                    if 'require' in node_type.lower() or 'assert' in node_type.lower():
                        has_validation = True
                        break
                if not has_validation:
                    features['dfg_num_unvalidated_inputs'] += 1
        
        return features
    
    def _default_features(self) -> Dict:
        """Return default (zero) features."""
        return {
            # CFG
            'cfg_num_nodes': 0, 'cfg_num_edges': 0, 'cfg_num_cycles': 0,
            'cfg_max_depth': 0, 'cfg_avg_branching': 0.0, 'cfg_has_complex_loops': False,
            'cfg_num_exit_points': 0, 'cfg_cyclomatic_total': 0,
            # Call Graph
            'cg_num_nodes': 0, 'cg_num_edges': 0, 'cg_max_call_depth': 0,
            'cg_num_external_calls': 0, 'cg_external_call_ratio': 0.0,
            'cg_has_cyclic_calls': False, 'cg_num_public_entry_points': 0,
            'cg_num_internal_functions': 0, 'cg_avg_calls_per_function': 0.0,
            'cg_num_leaf_functions': 0,
            # Data Flow
            'dfg_num_state_vars': 0, 'dfg_num_tainted_flows': 0,
            'dfg_has_cross_function_flow': False, 'dfg_num_sensitive_sinks': 0,
            'dfg_num_external_sources': 0, 'dfg_taint_to_sink_ratio': 0.0,
            'dfg_num_unvalidated_inputs': 0
        }

"""
Fixed feature extraction with correct Slither API
"""
from pathlib import Path
import subprocess
import re
import logging
from slither import Slither
import pandas as pd
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze_contract_with_version_switch(contract_path: Path, contract_name: str) -> dict:
    """Analyze contract with proper version switching"""
    
    # Detect version
    try:
        content = contract_path.read_text(encoding="utf-8", errors='ignore')
        match = re.search(r'pragma\s+solidity\s+[\^=~]?([\d.]+)', content)
        version = match.group(1) if match else "0.8.20"
    except Exception as e:
        logger.error(f"Failed to read {contract_name}: {e}")
        version = "0.8.20"
    
    # Switch version
    try:
        subprocess.run(['solc-select', 'use', version], 
                       capture_output=True, check=True, stderr=subprocess.DEVNULL)
    except:
        pass
    
    result = {
        'contract_name': contract_name,
        'file_path': str(contract_path),
        'has_reentrancy': False,
        'has_access_control_issues': False,
        'has_timestamp_dependency': False,
        'has_unchecked_call': False,
        'high_severity_count': 0,
        'medium_severity_count': 0,
        'low_severity_count': 0,
        'num_functions': 0,
        'num_external_calls': 0,
        'num_state_vars': 0,
        'num_modifiers': 0,
        'max_cyclomatic_complexity': 0,
        'num_low_level_calls': 0,
    }
    
    try:
        # Run Slither
        slither = Slither(str(contract_path), solc='solc', solc_disable_warnings=True)
        
        # Extract features from contracts
        for contract in slither.contracts:
            if contract.is_interface or contract.is_library:
                continue
                
            result['num_functions'] += len(contract.functions)
            result['num_state_vars'] += len(contract.state_variables)
            result['num_modifiers'] += len(contract.modifiers)
            
            # Count external calls
            for func in contract.functions:
                for call in func.external_calls_as_expressions:
                    result['num_external_calls'] += 1
                for call in func.low_level_calls:
                    result['num_low_level_calls'] += 1
                
                # Calculate cyclomatic complexity
                if hasattr(func, 'cyclomatic_complexity'):
                    complexity = func.cyclomatic_complexity
                    if complexity > result['max_cyclomatic_complexity']:
                        result['max_cyclomatic_complexity'] = complexity
        
        # ✅ FIX: Register and run detectors properly
        try:
            # Import all detectors
            import slither.detectors.all_detectors as all_detectors
            
            # Get detector classes
            detector_classes = [
                getattr(all_detectors, name)
                for name in dir(all_detectors)
                if name[0].isupper()
            ]
            
            # Register detectors
            for detector_class in detector_classes:
                slither.register_detector(detector_class)
            
            # Run detectors
            slither.run_detectors()
            
            # ✅ FIX: Use correct attribute name
            # Try different possible attribute names
            if hasattr(slither, 'results_detectors'):
                findings = slither.results_detectors
            elif hasattr(slither, 'results'):
                findings = slither.results
            elif hasattr(slither, 'detector_results'):
                findings = slither.detector_results
            else:
                # Fallback: get findings from detectors directly
                findings = []
                for detector in slither.detectors:
                    if hasattr(detector, 'results'):
                        findings.extend(detector.results)
            
            # Process findings
            for finding in findings:
                impact = finding.get('impact', 'Low')
                
                if impact == 'High':
                    result['high_severity_count'] += 1
                elif impact == 'Medium':
                    result['medium_severity_count'] += 1
                else:
                    result['low_severity_count'] += 1
                
                # Check specific vulnerabilities
                check = finding.get('check', '')
                if 'reentrancy' in check.lower():
                    result['has_reentrancy'] = True
                if 'access' in check.lower():
                    result['has_access_control_issues'] = True
                if 'timestamp' in check.lower():
                    result['has_timestamp_dependency'] = True
                if 'unchecked' in check.lower() or 'return-value' in check.lower():
                    result['has_unchecked_call'] = True
        
        except Exception as e:
            logger.debug(f"Detector error for {contract_name}: {e}")
        
        if result['num_functions'] > 0:
            logger.info(f"✅ {contract_name}: {result['num_functions']} functions, "
                       f"{result['high_severity_count']}H {result['medium_severity_count']}M "
                       f"{result['low_severity_count']}L")
        
    except Exception as e:
        logger.error(f"❌ {contract_name} failed: {e}")
        result['analysis_error'] = str(e)
    
    return result


if __name__ == "__main__":
    contracts_dir = Path('blockchain/contracts/collected')
    contract_files = list(contracts_dir.glob('*.sol'))
    
    print(f"Found {len(contract_files)} contracts\n")
    
    results = []
    
    for file in tqdm(contract_files, desc="Analyzing contracts"):
        name = file.stem.split('_')[0]
        result = analyze_contract_with_version_switch(file, name)
        results.append(result)
    
    # Save results
    df = pd.DataFrame(results)
    df.to_csv('data/ml_dataset_fixed.csv', index=False)
    
    # Create clean version
    numeric_cols = [c for c in df.columns 
                   if c not in ['contract_name', 'file_path', 'has_reentrancy', 'analysis_error']]
    df_clean = df[(df[numeric_cols] != 0).any(axis=1)]
    df_clean.to_csv('data/ml_dataset_clean.csv', index=False)
    
    print(f"\n{'='*70}")
    print("EXTRACTION COMPLETE")
    print(f"{'='*70}")
    print(f"Total contracts: {len(df)}")
    print(f"Clean contracts: {len(df_clean)} ({len(df_clean)/len(df)*100:.1f}% success)")
    
    if len(df_clean) > 0:
        print(f"\nVulnerability distribution:")
        print(df_clean['has_reentrancy'].value_counts())
        
        # Count all vulnerability types
        vuln_cols = ['has_reentrancy', 'has_access_control_issues', 
                     'has_timestamp_dependency', 'has_unchecked_call']
        for col in vuln_cols:
            if col in df_clean.columns:
                count = df_clean[col].sum()
                if count > 0:
                    print(f"  {col}: {count} contracts")
        
        print(f"\nSeverity distribution:")
        print(f"  High: {df_clean['high_severity_count'].sum()} total")
        print(f"  Medium: {df_clean['medium_severity_count'].sum()} total")
        print(f"  Low: {df_clean['low_severity_count'].sum()} total")
        
        print(f"\nFeature statistics:")
        for col in ['num_functions', 'num_external_calls', 'high_severity_count']:
            if col in df_clean.columns:
                print(f"  {col}: mean={df_clean[col].mean():.1f}, max={df_clean[col].max()}")
    else:
        print("\n⚠️  No contracts with features!")
    
    print(f"{'='*70}\n")


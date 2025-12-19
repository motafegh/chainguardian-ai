"""
Import SmartBugs Curated contracts with ground truth labels.
"""
from pathlib import Path
from chainguardian.feature_extraction.pipeline import FeaturePipeline
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SMARTBUGS_CURATED = Path("data/smartbugs_curated/dataset")

# Vulnerability type mapping
VULN_CATEGORIES = {
    'access_control': 'access_control',
    'arithmetic': 'arithmetic',
    'bad_randomness': 'randomness',
    'denial_of_service': 'dos',
    'front_running': 'front_running',
    'reentrancy': 'reentrancy',
    'short_addresses': 'short_address',
    'time_manipulation': 'timestamp',
    'unchecked_low_level_calls': 'unchecked_call',
}

def import_smartbugs_curated():
    """Import all SmartBugs curated contracts."""
    
    pipeline = FeaturePipeline()
    
    for vuln_category_dir in SMARTBUGS_CURATED.iterdir():
        if not vuln_category_dir.is_dir():
            continue
        
        vuln_type = VULN_CATEGORIES.get(vuln_category_dir.name)
        if not vuln_type:
            continue
        
        logger.info(f"\n{'='*70}")
        logger.info(f"Processing: {vuln_category_dir.name} ({vuln_type})")
        logger.info(f"{'='*70}")
        
        contracts = list(vuln_category_dir.glob("*.sol"))
        logger.info(f"Found {len(contracts)} contracts")
        
        for contract_file in contracts:
            contract_name = contract_file.stem
            
            try:
                # Extract features
                metadata = {
                    'data_source': 'smartbugs_curated',
                    'ground_truth_label': 'vulnerable',
                    'ground_truth_vuln_type': vuln_type,
                }

                features = pipeline.analyze_contract(contract_file, contract_name, metadata=metadata)
                # Add ground truth label
                features['ground_truth_label'] = 'vulnerable'
                features['ground_truth_vuln_type'] = vuln_type
                features['data_source'] = 'smartbugs_curated'
                
                # Save to database (already done in pipeline)
                logger.info(f"✓ {contract_name}: Extracted + Labeled")
                
            except Exception as e:
                logger.error(f"✗ {contract_name}: {e}")
    
    # Print summary
    pipeline.print_diagnostic_summary()

if __name__ == "__main__":
    import_smartbugs_curated()

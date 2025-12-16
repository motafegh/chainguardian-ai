"""
Test pipeline with database integration using YOUR actual contracts
"""
from pathlib import Path
from chainguardian.feature_extraction.pipeline import FeaturePipeline
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_single_contract():
    """Test analyzing one contract and saving to database."""
    
    # Initialize pipeline (now connects to database)
    logger.info("Initializing pipeline...")
    pipeline = FeaturePipeline()
    
    # Test with DSToken (single-file contract from your data)
    # 🎓 This is the actual path from your CSV
    test_contract = Path("/home/motafeq/projects/chainguardian-ai/blockchain/contracts/collected/DSToken_0x9f8F72aA.sol")
    
    if not test_contract.exists():
        logger.error(f"❌ Contract not found: {test_contract}")
        logger.info("💡 Trying alternative contracts...")
        
        # Try the multi-file contract
        test_contract = Path("/home/motafeq/projects/chainguardian-ai/blockchain/contracts/collected/Synari_0x1bd1bc78")
        
        if not test_contract.exists():
            logger.error("❌ No test contracts found!")
            logger.info("📁 Please check your blockchain/contracts/collected/ directory")
            return
    
    contract_name = test_contract.stem.split('_')[0]  # Extract "DSToken" or "Synari"
    logger.info(f"🔍 Testing with: {test_contract.name}")
    logger.info(f"📝 Contract name: {contract_name}")
    logger.info("")
    
    # ================================================================
    # ANALYZE CONTRACT (will save to database automatically)
    # ================================================================
    logger.info("="*70)
    logger.info("STEP 1: Analyzing contract and extracting features")
    logger.info("="*70)
    
    features = pipeline.analyze_contract(test_contract, contract_name)
    
    logger.info("")
    logger.info("✅ Analysis complete!")
    logger.info(f"📊 Features extracted: {len(features)} fields")
    
    # Show some key features
    logger.info("")
    logger.info("Key features:")
    logger.info(f"  - Has reentrancy: {features.get('has_reentrancy')}")
    logger.info(f"  - Number of functions: {features.get('num_functions')}")
    logger.info(f"  - High severity count: {features.get('high_severity_count')}")
    logger.info(f"  - Max complexity: {features.get('max_cyclomatic_complexity')}")
    
    # ================================================================
    # CHECK DATABASE
    # ================================================================
    logger.info("")
    logger.info("="*70)
    logger.info("STEP 2: Checking database")
    logger.info("="*70)
    
    contract_count = pipeline.db.get_contract_count()
    logger.info(f"📊 Total contracts in database: {contract_count}")
    
    stats = pipeline.db.get_stats()
    logger.info(f"📈 Database statistics:")
    for key, value in stats.items():
        logger.info(f"  - {key}: {value}")
    
    # ================================================================
    # EXPORT TO CSV
    # ================================================================
    logger.info("")
    logger.info("="*70)
    logger.info("STEP 3: Exporting to CSV")
    logger.info("="*70)
    
    output_path = Path("data/test_database_export.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pipeline.save_dataset(output_path)
    
    logger.info("")
    logger.info("="*70)
    logger.info("✅ TEST COMPLETE!")
    logger.info("="*70)
    logger.info(f"📁 Check output: {output_path}")
    logger.info("")
    logger.info("🎯 What happened:")
    logger.info("  1. ✅ Analyzed contract with Slither + AST")
    logger.info("  2. ✅ Saved to PostgreSQL database")
    logger.info("  3. ✅ Exported from database to CSV")
    logger.info("")
    logger.info("💡 Next: Run your full pipeline to populate database with all contracts!")

def test_multiple_contracts():
    """Test with 3 contracts to see batch processing."""
    logger.info("="*70)
    logger.info("TESTING BATCH PROCESSING (3 contracts)")
    logger.info("="*70)
    logger.info("")
    
    pipeline = FeaturePipeline()
    
    # Find some contracts from your collected directory
    contracts_dir = Path("/home/motafeq/projects/chainguardian-ai/blockchain/contracts/collected")
    
    if not contracts_dir.exists():
        logger.error(f"❌ Directory not found: {contracts_dir}")
        return
    
    # Get first 3 .sol files
    sol_files = list(contracts_dir.glob("*.sol"))[:3]
    
    if not sol_files:
        logger.warning("⚠️ No .sol files found, trying directories...")
        sol_files = [d for d in contracts_dir.iterdir() if d.is_dir()][:3]
    
    logger.info(f"Found {len(sol_files)} contracts to test")
    logger.info("")
    
    for i, contract_path in enumerate(sol_files, 1):
        contract_name = contract_path.stem.split('_')[0]
        logger.info(f"[{i}/{len(sol_files)}] Analyzing {contract_name}...")
        
        try:
            features = pipeline.analyze_contract(contract_path, contract_name)
            logger.info(f"  ✅ {contract_name}: {features.get('num_functions')} functions, {features.get('high_severity_count')} high severity")
        except Exception as e:
            logger.error(f"  ❌ {contract_name}: Failed - {e}")
        
        logger.info("")
    
    # Check database
    contract_count = pipeline.db.get_contract_count()
    logger.info(f"📊 Total contracts in database: {contract_count}")
    
    # Export
    output_path = Path("data/batch_test_export.csv")
    pipeline.save_dataset(output_path)
    logger.info(f"✅ Exported to: {output_path}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "batch":
        test_multiple_contracts()
    else:
        test_single_contract()
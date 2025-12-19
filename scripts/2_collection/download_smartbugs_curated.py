"""
Download SmartBugs Curated dataset

🎓 This is the PERFECT dataset for us:
- 143 high-quality contracts
- Pre-labeled vulnerabilities
- Already analyzed by 6 tools
- Used in academic research
"""

import subprocess
from pathlib import Path
import logging
import shutil

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def download_smartbugs_curated():
    """
    Clone SmartBugs Curated repository.
    
    🎓 This gives us:
    - Solidity source files (143 contracts)
    - Analysis results from 6 tools (JSON files)
    - Ground truth labels (folder structure)
    """
    
    target_dir = Path("data/smartbugs_curated")
    
    logger.info("="*70)
    logger.info("📥 DOWNLOADING SMARTBUGS CURATED DATASET")
    logger.info("="*70)
    logger.info("")
    logger.info("🎯 What we're getting:")
    logger.info("  • 143 hand-picked vulnerable contracts")
    logger.info("  • Pre-analyzed by 6 security tools")
    logger.info("  • Labeled by vulnerability type")
    logger.info("  • Research-grade quality")
    logger.info("")
    
    # Check if already exists
    if target_dir.exists():
        logger.info(f"⚠️  Directory already exists: {target_dir}")
        response = input("   Delete and re-download? (y/n): ")
        if response.lower() == 'y':
            shutil.rmtree(target_dir)
            logger.info("   🗑️  Deleted existing directory")
        else:
            logger.info("   ✅ Using existing data")
            show_dataset_stats(target_dir)
            return
    
    logger.info("📦 Cloning repository...")
    logger.info("   This may take 2-3 minutes...")
    logger.info("")
    
    try:
        # Clone the repository
        subprocess.run([
            'git', 'clone',
            'https://github.com/smartbugs/smartbugs-curated.git',
            str(target_dir)
        ], check=True)
        
        logger.info("")
        logger.info("="*70)
        logger.info("✅ DOWNLOAD COMPLETE!")
        logger.info("="*70)
        logger.info("")
        
        show_dataset_stats(target_dir)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Git clone failed: {e}")
        logger.info("")
        logger.info("💡 Manual download:")
        logger.info("   git clone https://github.com/smartbugs/smartbugs-curated.git data/smartbugs_curated")
    except FileNotFoundError:
        logger.error("❌ Git not found!")
        logger.info("   Install git: sudo apt install git")


def show_dataset_stats(dataset_dir: Path):
    """Show statistics about the downloaded dataset."""
    
    logger.info("📊 DATASET STATISTICS")
    logger.info("-"*70)
    
    # Check dataset folder
    dataset_path = dataset_dir / "dataset"
    results_path = dataset_dir / "results"
    
    if not dataset_path.exists():
        logger.error(f"❌ Dataset folder not found: {dataset_path}")
        return
    
    # Count contracts by vulnerability type
    vuln_types = [
        'access_control',
        'arithmetic', 
        'denial_of_service',
        'front_running',
        'reentrancy',
        'time_manipulation',
        'unchecked_low_level_calls',
        'other'
    ]
    
    total_contracts = 0
    
    logger.info("")
    logger.info("📁 Contracts by vulnerability type:")
    
    for vuln_type in vuln_types:
        vuln_dir = dataset_path / vuln_type
        if vuln_dir.exists():
            contracts = list(vuln_dir.glob("*.sol"))
            count = len(contracts)
            total_contracts += count
            
            # Emoji for different types
            emoji = {
                'access_control': '🔒',
                'arithmetic': '🔢',
                'denial_of_service': '🚫',
                'front_running': '🏃',
                'reentrancy': '🔄',
                'time_manipulation': '⏰',
                'unchecked_low_level_calls': '📞',
                'other': '✅'
            }.get(vuln_type, '📄')
            
            logger.info(f"   {emoji} {vuln_type:30s}: {count:3d} contracts")
    
    logger.info(f"   {'─'*45}")
    logger.info(f"   {'TOTAL':30s}: {total_contracts:3d} contracts")
    logger.info("")
    
    # Check if results exist
    if results_path.exists():
        result_dirs = list(results_path.rglob("result.json"))
        logger.info(f"📋 Pre-analyzed results: {len(result_dirs)} contracts")
        
        # Sample one to show structure
        if result_dirs:
            sample_result = result_dirs[0].parent
            logger.info(f"")
            logger.info(f"📂 Example result folder:")
            logger.info(f"   {sample_result.relative_to(dataset_dir)}/")
            
            tool_files = list(sample_result.glob("*.json"))
            for tool_file in sorted(tool_files):
                size_kb = tool_file.stat().st_size / 1024
                logger.info(f"      • {tool_file.name:20s} ({size_kb:.1f} KB)")
    
    logger.info("")
    logger.info("="*70)
    logger.info("🎯 NEXT STEPS")
    logger.info("="*70)
    logger.info("")
    logger.info("1. Examine the contracts:")
    logger.info(f"   ls {dataset_path}/reentrancy/")
    logger.info("")
    logger.info("2. Examine analysis results:")
    logger.info(f"   ls {results_path}/reentrancy/*/")
    logger.info("")
    logger.info("3. Parse results and extract features!")
    logger.info("")


if __name__ == "__main__":
    download_smartbugs_curated()
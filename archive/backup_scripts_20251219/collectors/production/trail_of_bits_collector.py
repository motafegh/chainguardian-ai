"""
Trail of Bits Not So Smart Contracts Collector

These are curated vulnerable contract examples from Trail of Bits.
All have source code and are categorized by vulnerability type.
"""

from pathlib import Path
import shutil
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrailOfBitsCollector:
    """Collect vulnerable contracts from Trail of Bits repo."""
    
    def __init__(self):
        self.source_dir = Path("data/vulnerable_complex/trail_of_bits")
        self.output_dir = Path("data/production/vulnerable/raw")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def collect(self):
        """Copy Trail of Bits contracts to production directory."""
        
        logger.info("="*70)
        logger.info("🔥 TRAIL OF BITS COLLECTOR")
        logger.info("="*70)
        
        if not self.source_dir.exists():
            logger.error(f"❌ Trail of Bits repo not found: {self.source_dir}")
            logger.error("   Run: git clone https://github.com/crytic/not-so-smart-contracts.git data/vulnerable_complex/trail_of_bits")
            return []
        
        # Find all .sol files
        contracts = list(self.source_dir.rglob("*.sol"))
        
        # Filter out test files and specific problematic patterns
        contracts = [c for c in contracts 
                    if 'test' not in c.parts 
                    and 'node_modules' not in c.parts
                    and not c.name.startswith('.')
                    and c.stat().st_size > 0]  # Skip empty files
        
        logger.info(f"📊 Found {len(contracts)} vulnerable contracts")
        logger.info("")
        
        # Copy to production directory
        copied = 0
        skipped = 0
        
        for contract in contracts:
            try:
                # Create unique name from path
                # e.g., reentrancy/DAO.sol -> tob_reentrancy_DAO.sol
                vuln_type = contract.parent.name
                new_name = f"tob_{vuln_type}_{contract.name}"
                
                dest = self.output_dir / new_name
                
                # Skip if already exists
                if dest.exists():
                    skipped += 1
                    continue
                
                shutil.copy(contract, dest)
                copied += 1
                
                logger.info(f"   [{copied}/{len(contracts)}] {vuln_type:25s} -> {contract.name}")
            except Exception as e:
                logger.error(f"   ❌ Failed to copy {contract.name}: {e}")
                skipped += 1
        
        logger.info("")
        logger.info("="*70)
        logger.info(f"✅ Copied {copied} Trail of Bits contracts")
        if skipped > 0:
            logger.info(f"⏭️  Skipped {skipped} (already exist or errors)")
        logger.info("="*70)
        
        return contracts


if __name__ == "__main__":
    collector = TrailOfBitsCollector()
    collector.collect()

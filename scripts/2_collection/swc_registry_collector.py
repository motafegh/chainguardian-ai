"""
SWC Registry Collector

Smart Contract Weakness Classification (SWC) registry examples.
Each SWC has example vulnerable contracts with source code.
"""

from pathlib import Path
import shutil
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SWCRegistryCollector:
    """Collect vulnerable contracts from SWC registry."""
    
    def __init__(self):
        self.source_dir = Path("data/vulnerable_complex/swc_registry")
        self.output_dir = Path("data/production/vulnerable/raw")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def collect(self):
        """Copy SWC examples to production directory."""
        
        logger.info("="*70)
        logger.info("🔥 SWC REGISTRY COLLECTOR")
        logger.info("="*70)
        
        if not self.source_dir.exists():
            logger.error(f"❌ SWC Registry not found: {self.source_dir}")
            logger.error("   Run: git clone https://github.com/SmartContractSecurity/SWC-registry.git data/vulnerable_complex/swc_registry")
            return []
        
        # Find all .sol files
        contracts = list(self.source_dir.rglob("*.sol"))
        
        # Filter
        contracts = [c for c in contracts 
                    if 'node_modules' not in c.parts
                    and not c.name.startswith('.')
                    and c.stat().st_size > 0]
        
        logger.info(f"📊 Found {len(contracts)} example contracts")
        logger.info("")
        
        # Copy to production directory
        copied = 0
        skipped = 0
        
        for contract in contracts:
            try:
                # Extract SWC number from path
                # e.g., entries/SWC-107/example.sol -> swc_107_example.sol
                parts = contract.parts
                swc_id = None
                for part in parts:
                    if part.startswith('SWC-'):
                        swc_id = part.replace('SWC-', 'swc_')
                        break
                
                if swc_id:
                    new_name = f"{swc_id}_{contract.name}"
                    dest = self.output_dir / new_name
                    
                    # Skip if already exists
                    if dest.exists():
                        skipped += 1
                        continue
                    
                    shutil.copy(contract, dest)
                    copied += 1
                    
                    logger.info(f"   [{copied}] {swc_id:15s} -> {contract.name}")
            except Exception as e:
                logger.error(f"   ❌ Failed to copy {contract.name}: {e}")
                skipped += 1
        
        logger.info("")
        logger.info("="*70)
        logger.info(f"✅ Copied {copied} SWC Registry contracts")
        if skipped > 0:
            logger.info(f"⏭️  Skipped {skipped} (already exist or errors)")
        logger.info("="*70)
        
        return contracts


if __name__ == "__main__":
    collector = SWCRegistryCollector()
    collector.collect()

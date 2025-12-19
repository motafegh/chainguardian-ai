"""
Master Production Collector

Orchestrates collection from all curated sources:
1. Rekt News exploits (vulnerable)
2. Audited DeFi protocols (safe)
3. Battle-tested tokens (safe)
4. SlowMist database (vulnerable)

🎓 Production pattern: Multi-source data collection for ML robustness
"""

from pathlib import Path
import json
import logging
from typing import List, Dict, Tuple
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from chainguardian.data_collection.etherscan_scraper import EtherscanScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MasterProductionCollector:
    """
    Master collector that orchestrates all production data sources.
    
    🎓 Strategy:
    1. Load metadata from curated JSON files
    2. Extract contract addresses
    3. Fetch source code via unified Etherscan collector
    4. Track provenance for each contract
    5. Generate collection report
    """
    
    def __init__(self):
        self.scraper = EtherscanScraper()
        
        # Metadata file paths
        self.vulnerable_sources = {
            "rekt_news": Path("data/metadata/vulnerable_sources/rekt_news_exploits.json"),
            "slowmist": Path("data/metadata/vulnerable_sources/slowmist_ethereum_hacks.json"),
            "verified_exploits": Path("data/metadata/vulnerable_sources/verified_exploits.json"),
        }
        
        self.safe_sources = {
            "audited_defi": Path("data/metadata/safe_sources/audited_defi_protocols.json"),
            "battle_tested_tokens": Path("data/metadata/safe_sources/battle_tested_tokens.json"),
        }
        
        # Output directories
        self.output_dir_vulnerable = Path("data/production/vulnerable/raw")
        self.output_dir_safe = Path("data/production/safe/raw")
        
        self.output_dir_vulnerable.mkdir(parents=True, exist_ok=True)
        self.output_dir_safe.mkdir(parents=True, exist_ok=True)
    
    def collect_vulnerable(self) -> Tuple[List[Path], Dict]:
        """
        Collect vulnerable contracts from all sources.
        
        Returns:
            Tuple of (scraped file paths, collection stats)
        """
        logger.info("")
        logger.info("="*70)
        logger.info("🔥 COLLECTING VULNERABLE CONTRACTS")
        logger.info("="*70)
        logger.info("")
        
        all_addresses = []
        address_metadata = {}  # Map address -> source info
        
        # Load from each source
        for source_name, source_file in self.vulnerable_sources.items():
            if not source_file.exists():
                logger.warning(f"⚠️  {source_name}: File not found - {source_file}")
                logger.warning(f"   Run the collector first!")
                continue
            
            logger.info(f"📂 Loading: {source_name}")
            
            with open(source_file) as f:
                data = json.load(f)
            
            # Extract addresses (handle different JSON structures)
            addresses = self._extract_addresses(data, source_name)
            
            # Store metadata
            for addr in addresses:
                address_metadata[addr] = {
                    'source': source_name,
                    'category': 'vulnerable'
                }
            
            all_addresses.extend(addresses)
            logger.info(f"   ✓ Found {len(addresses)} addresses")
        
        # Remove duplicates while preserving order
        unique_addresses = list(dict.fromkeys(all_addresses))
        
        logger.info("")
        logger.info(f"📊 Total unique addresses: {len(unique_addresses)}")
        logger.info(f"📊 Duplicates removed: {len(all_addresses) - len(unique_addresses)}")
        logger.info("")
        logger.info("🌐 Starting Etherscan scraping...")
        logger.info(f"   Using 5 parallel workers")
        logger.info(f"   Estimated time: ~{len(unique_addresses) * 0.21 / 5:.0f}s")
        logger.info("")
        
        # Scrape with unified collector
        scraped_files = self.scraper.scrape_batch(
            unique_addresses,
            output_dir=self.output_dir_vulnerable,
            max_workers=5,
            save_metadata=True
        )
        
        stats = {
            'total_addresses': len(unique_addresses),
            'scraped_successfully': len(scraped_files),
            'failed': len(unique_addresses) - len(scraped_files),
            'success_rate': len(scraped_files) / len(unique_addresses) * 100,
            'by_source': {}
        }
        
        # Calculate per-source stats
        for source_name in self.vulnerable_sources.keys():
            source_addrs = [a for a, m in address_metadata.items() if m['source'] == source_name]
            stats['by_source'][source_name] = len(source_addrs)
        
        logger.info("")
        logger.info("="*70)
        logger.info(f"✅ VULNERABLE COLLECTION COMPLETE")
        logger.info("="*70)
        logger.info(f"   Success: {stats['scraped_successfully']}/{stats['total_addresses']} ({stats['success_rate']:.1f}%)")
        logger.info(f"   Saved to: {self.output_dir_vulnerable}")
        logger.info("="*70)
        
        return scraped_files, stats
    
    def collect_safe(self) -> Tuple[List[Path], Dict]:
        """
        Collect safe contracts from all sources.
        
        Returns:
            Tuple of (scraped file paths, collection stats)
        """
        logger.info("")
        logger.info("="*70)
        logger.info("🔒 COLLECTING SAFE CONTRACTS")
        logger.info("="*70)
        logger.info("")
        
        all_addresses = []
        address_metadata = {}
        
        # Load from each source
        for source_name, source_file in self.safe_sources.items():
            if not source_file.exists():
                logger.warning(f"⚠️  {source_name}: File not found - {source_file}")
                logger.warning(f"   Run the collector first!")
                continue
            
            logger.info(f"📂 Loading: {source_name}")
            
            with open(source_file) as f:
                data = json.load(f)
            
            # Extract addresses
            addresses = self._extract_addresses(data, source_name)
            
            # Store metadata
            for addr in addresses:
                address_metadata[addr] = {
                    'source': source_name,
                    'category': 'safe'
                }
            
            all_addresses.extend(addresses)
            logger.info(f"   ✓ Found {len(addresses)} addresses")
        
        # Remove duplicates
        unique_addresses = list(dict.fromkeys(all_addresses))
        
        logger.info("")
        logger.info(f"📊 Total unique addresses: {len(unique_addresses)}")
        logger.info(f"📊 Duplicates removed: {len(all_addresses) - len(unique_addresses)}")
        logger.info("")
        logger.info("🌐 Starting Etherscan scraping...")
        logger.info(f"   Using 5 parallel workers")
        logger.info(f"   Estimated time: ~{len(unique_addresses) * 0.21 / 5:.0f}s")
        logger.info("")
        
        # Scrape with unified collector
        scraped_files = self.scraper.scrape_batch(
            unique_addresses,
            output_dir=self.output_dir_safe,
            max_workers=5,
            save_metadata=True
        )
        
        stats = {
            'total_addresses': len(unique_addresses),
            'scraped_successfully': len(scraped_files),
            'failed': len(unique_addresses) - len(scraped_files),
            'success_rate': len(scraped_files) / len(unique_addresses) * 100,
            'by_source': {}
        }
        
        # Calculate per-source stats
        for source_name in self.safe_sources.keys():
            source_addrs = [a for a, m in address_metadata.items() if m['source'] == source_name]
            stats['by_source'][source_name] = len(source_addrs)
        
        logger.info("")
        logger.info("="*70)
        logger.info(f"✅ SAFE COLLECTION COMPLETE")
        logger.info("="*70)
        logger.info(f"   Success: {stats['scraped_successfully']}/{stats['total_addresses']} ({stats['success_rate']:.1f}%)")
        logger.info(f"   Saved to: {self.output_dir_safe}")
        logger.info("="*70)
        
        return scraped_files, stats
    
    def collect_all(self):
        """Run complete production data collection."""
        logger.info("")
        logger.info("╔"+"="*68+"╗")
        logger.info("║" + " "*15 + "PRODUCTION DATASET COLLECTION" + " "*24 + "║")
        logger.info("╚"+"="*68+"╝")
        
        # Collect vulnerable
        vuln_files, vuln_stats = self.collect_vulnerable()
        
        # Collect safe
        safe_files, safe_stats = self.collect_safe()
        
        # Final summary
        logger.info("")
        logger.info("")
        logger.info("╔"+"="*68+"╗")
        logger.info("║" + " "*20 + "COLLECTION SUMMARY" + " "*30 + "║")
        logger.info("╚"+"="*68+"╝")
        logger.info("")
        logger.info(f"🔥 VULNERABLE CONTRACTS:")
        logger.info(f"   Total: {vuln_stats['scraped_successfully']}")
        logger.info(f"   By source:")
        for source, count in vuln_stats['by_source'].items():
            logger.info(f"      {source:20s}: {count:3d}")
        
        logger.info("")
        logger.info(f"🔒 SAFE CONTRACTS:")
        logger.info(f"   Total: {safe_stats['scraped_successfully']}")
        logger.info(f"   By source:")
        for source, count in safe_stats['by_source'].items():
            logger.info(f"      {source:20s}: {count:3d}")
        
        total = vuln_stats['scraped_successfully'] + safe_stats['scraped_successfully']
        logger.info("")
        logger.info(f"📊 TOTAL DATASET: {total} contracts")
        logger.info(f"   Vulnerable: {vuln_stats['scraped_successfully']} ({vuln_stats['scraped_successfully']/total*100:.1f}%)")
        logger.info(f"   Safe: {safe_stats['scraped_successfully']} ({safe_stats['scraped_successfully']/total*100:.1f}%)")
        
        logger.info("")
        logger.info("="*70)
        logger.info("🎉 PRODUCTION COLLECTION COMPLETE!")
        logger.info("="*70)
        logger.info("")
        logger.info("📋 NEXT STEPS:")
        logger.info("   1. Run feature extraction:")
        logger.info("      poetry run python scripts/import/import_production_dataset.py")
        logger.info("")
        logger.info("   2. Verify dataset diversity:")
        logger.info("      poetry run python scripts/analysis/verify_dataset.py")
        logger.info("")
        logger.info("   3. Start ML training (Day 3)!")
        logger.info("="*70)
    
    def _extract_addresses(self, data: List[Dict], source_name: str) -> List[str]:
        """
        Extract addresses from JSON data (handles different structures).
        
        Args:
            data: JSON data (list of dicts)
            source_name: Name of source for error messages
            
        Returns:
            List of Ethereum addresses
        """
        addresses = []
        
        if isinstance(data, list):
            for item in data:
                # Direct address field
                if 'address' in item:
                    addresses.append(item['address'])
                
                # Nested contracts list (for protocols)
                elif 'contracts' in item:
                    for contract in item['contracts']:
                        if isinstance(contract, dict) and 'address' in contract:
                            addresses.append(contract['address'])
                        elif isinstance(contract, str):
                            addresses.append(contract)
        
        return addresses


def main():
    """Run master production collector."""
    collector = MasterProductionCollector()
    collector.collect_all()


if __name__ == "__main__":
    main()
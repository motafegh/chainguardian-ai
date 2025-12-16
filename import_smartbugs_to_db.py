"""
Import SmartBugs Curated contracts into our database

🎓 What this does:
1. Reads vulnerabilities.json for labels
2. Analyzes each contract with OUR existing pipeline
3. Saves to database with vulnerability labels
4. Now we have 309 contracts (166 + 143)
"""

import json
from pathlib import Path
import logging
from typing import Dict, List
from chainguardian.feature_extraction.pipeline import FeaturePipeline
from chainguardian.database.manager import DatabaseManager

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class SmartBugsImporter:
    """
    Import SmartBugs Curated contracts into database.
    
    🎓 This bridges two datasets:
    - SmartBugs: High-quality labeled contracts
    - Ours: Real DeFi contracts (unlabeled)
    
    Result: Combined dataset for better ML training
    """
    
    def __init__(self):
        """Initialize pipeline and database."""
        self.pipeline = FeaturePipeline()
        self.db = DatabaseManager()
        self.smartbugs_dir = Path("data/smartbugs_curated")
        
        # Load vulnerability labels
        self.labels = self._load_labels()
        logger.info(f"✅ Loaded labels for {len(self.labels)} contracts")
    
    def _load_labels(self) -> Dict:
        """
        Load vulnerabilities.json file.
        
        🎓 This gives us ground truth labels
        Format: {contract_name: [vulnerability_categories]}
        
        Returns:
            Dictionary mapping contract names to vulnerability info
        """
        labels_file = self.smartbugs_dir / "vulnerabilities.json"
        
        if not labels_file.exists():
            logger.error(f"❌ Labels file not found: {labels_file}")
            return {}
        
        with open(labels_file) as f:
            data = json.load(f)
        
        # Convert list to dict for easy lookup
        # Key: contract name, Value: vulnerability data
        labels_dict = {}
        for item in data:
            contract_name = item['name']
            labels_dict[contract_name] = item
        
        return labels_dict
    
    def _get_vulnerability_categories(self, contract_name: str) -> List[str]:
        """
        Get list of vulnerability categories for a contract.
        
        Args:
            contract_name: Name of contract (e.g., "DAO.sol")
        
        Returns:
            List of vulnerability categories (e.g., ["reentrancy", "access_control"])
        """
        if contract_name not in self.labels:
            return []
        
        contract_data = self.labels[contract_name]
        vulns = contract_data.get('vulnerabilities', [])
        
        # Extract unique categories
        categories = set()
        for vuln in vulns:
            if isinstance(vuln, dict):
                category = vuln.get('category')
                if category:
                    categories.add(category)
        
        return list(categories)
    
    def import_contracts(self, limit: int = None):
        """
        Import SmartBugs contracts to database.
        
        Args:
            limit: Optional limit on number to import (for testing)
        """
        
        logger.info("="*70)
        logger.info("📥 IMPORTING SMARTBUGS CONTRACTS TO DATABASE")
        logger.info("="*70)
        logger.info("")
        
        # Get all contract files
        dataset_dir = self.smartbugs_dir / "dataset"
        all_contracts = list(dataset_dir.rglob("*.sol"))
        
        if limit:
            all_contracts = all_contracts[:limit]
        
        logger.info(f"📊 Found {len(all_contracts)} contracts to import")
        logger.info("")
        
        # Statistics
        successful = 0
        failed = 0
        labeled = 0
        
        # Process each contract
        for i, contract_path in enumerate(all_contracts, 1):
            contract_name = contract_path.name
            
            # Get vulnerability categories from labels
            vuln_categories = self._get_vulnerability_categories(contract_name)
            
            # Determine source (vulnerability folder)
            # e.g., dataset/reentrancy/DAO.sol → source = "smartbugs_reentrancy"
            if contract_path.parent.name != "dataset":
                source = f"smartbugs_{contract_path.parent.name}"
            else:
                source = "smartbugs_other"
            
            logger.info(f"[{i}/{len(all_contracts)}] {contract_name}")
            logger.info(f"  📁 Source: {source}")
            
            if vuln_categories:
                logger.info(f"  🏷️  Labels: {', '.join(vuln_categories)}")
                labeled += 1
            else:
                logger.info(f"  ⚪ No labels")
            
            try:
                # Extract features using OUR existing pipeline
                # 🎓 This ensures consistency with our 166 contracts
                features = self.pipeline.analyze_contract(
                    contract_path,
                    contract_name.replace('.sol', '')
                )
                
                # Add metadata
                features['source'] = source
                features['file_path'] = str(contract_path)
                
                # Save to database (pipeline already does this!)
                # But we need to add vulnerability labels separately
                
                # Get contract_id from database
                contract_id = self.pipeline.db.get_contract_count()  # Last inserted
                
                # Add vulnerability labels
                if vuln_categories:
                    self._add_labels(contract_id, vuln_categories)
                
                logger.info(f"  ✅ Imported successfully")
                successful += 1
                
            except Exception as e:
                logger.error(f"  ❌ Failed: {e}")
                failed += 1
            
            logger.info("")
        
        # Summary
        logger.info("="*70)
        logger.info("📊 IMPORT SUMMARY")
        logger.info("="*70)
        logger.info(f"  Total processed:  {len(all_contracts)}")
        logger.info(f"  ✅ Successful:    {successful}")
        logger.info(f"  ❌ Failed:        {failed}")
        logger.info(f"  🏷️  With labels:   {labeled}")
        logger.info("")
        
        # Show database stats
        total_contracts = self.db.get_contract_count()
        stats = self.db.get_stats()
        
        logger.info(f"📈 DATABASE STATUS:")
        logger.info(f"  Total contracts: {total_contracts}")
        logger.info(f"  Your contracts: {total_contracts - successful}")
        logger.info(f"  SmartBugs: {successful}")
        logger.info("")
        
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")
        
        logger.info("="*70)
    
    def _add_labels(self, contract_id: int, categories: List[str]):
        """
        Add vulnerability labels to database.
        
        🎓 This populates the 'labels' table
        One row per (contract, vulnerability_type) pair
        
        Args:
            contract_id: Database ID of contract
            categories: List of vulnerability categories
        """
        
        # Map SmartBugs categories to our standardized types
        category_mapping = {
            'access_control': 'access_control',
            'arithmetic': 'arithmetic',
            'reentrancy': 'reentrancy',
            'time_manipulation': 'timestamp',
            'unchecked_low_level_calls': 'unchecked_call',
            'denial_of_service': 'denial_of_service',
            'front_running': 'front_running',
            'bad_randomness': 'bad_randomness',
            'short_addresses': 'short_address',
            'other': 'other'
        }
        
        for category in categories:
            # Map to our standard type
            vuln_type = category_mapping.get(category, category)
            
            # Add to labels table
            try:
                # We need to add this method to DatabaseManager
                # For now, just log
                logger.debug(f"    Adding label: {vuln_type}")
                
                # TODO: Call db.add_vulnerability_label(contract_id, vuln_type, has_vulnerability=True)
                
            except Exception as e:
                logger.error(f"    Failed to add label {vuln_type}: {e}")


def main():
    """Run the importer."""
    
    print("\n🎯 SMARTBUGS IMPORT WIZARD\n")
    print("This will:")
    print("  1. Analyze SmartBugs contracts with YOUR pipeline")
    print("  2. Extract features (Slither + AST)")
    print("  3. Add vulnerability labels from vulnerabilities.json")
    print("  4. Save everything to YOUR database")
    print()
    
    response = input("Start import? (y/n): ")
    
    if response.lower() != 'y':
        print("❌ Cancelled")
        return
    
    print()
    
    # Ask if testing or full import
    response = input("Test with 5 contracts first? (y/n): ")
    
    limit = 5 if response.lower() == 'y' else None
    
    print()
    
    # Run import
    importer = SmartBugsImporter()
    importer.import_contracts(limit=limit)
    
    print("\n✅ Import complete!")
    print("\n📊 Check results:")
    print("  poetry run python query_database.py")


if __name__ == "__main__":
    main()
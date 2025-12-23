# Save as: scripts/integrate_new_dataset_fixed.py
import yaml
from pathlib import Path
from chainguardian.feature_extraction.pipeline import FeaturePipeline
from chainguardian.database.manager import DatabaseManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_contract_name(file_path: Path) -> str:
    """Extract contract name from file content or filename"""
    try:
        content = file_path.read_text()
        # Look for contract definition in first 1000 chars
        import re
        content_preview = content[:1000]
        matches = re.findall(r'contract\s+(\w+)', content_preview)
        if matches:
            return matches[0]  # First contract found
    except:
        pass
    # Fallback: use filename without extension
    return file_path.stem

def process_vulnerable_contracts(pipeline):
    """Process vulnerable contracts - flat structure"""
    vulnerable_path = Path("blockchain/contracts/new_vulnerable")
    
    # Map folder names to vulnerability types
    vuln_map = {
        "Re-entrancy": "reentrancy",
        "Timestamp-Dependency": "timestamp_dependency", 
        "Overflow-Underflow": "arithmetic",
        "TOD": "tod",
        "Unchecked-Send": "unchecked_call",
        "Unhandled-Exceptions": "exception_handling",
        "tx.origin": "tx_origin",
    }
    
    processed = 0
    for vuln_dir in vulnerable_path.iterdir():
        if vuln_dir.is_dir():
            vuln_type = vuln_map.get(vuln_dir.name, vuln_dir.name.lower().replace('-', '_'))
            
            print(f"Processing {vuln_dir.name} -> {vuln_type}")
            
            # Find ALL .sol files in this directory (including subdirectories)
            sol_files = list(vuln_dir.rglob("*.sol"))
            
            for sol_file in sol_files:
                if sol_file.is_file():
                    try:
                        contract_name = extract_contract_name(sol_file)
                        
                        # Get relative path for tracking
                        rel_path = sol_file.relative_to(vuln_dir)
                        
                        metadata = {
                            'ground_truth_label': 'vulnerable',
                            'ground_truth_vuln_type': vuln_type,
                            'data_source': 'solidifi_benchmark',
                            'original_category': vuln_dir.name,
                            'file_path': str(sol_file),
                            'relative_path': str(rel_path)
                        }
                        
                        pipeline.analyze_contract(
                            contract_path=sol_file,
                            contract_name=contract_name,
                            metadata=metadata
                        )
                        processed += 1
                        
                        if processed % 10 == 0:
                            print(f"  Processed {processed} vulnerable contracts...")
                            
                    except Exception as e:
                        logger.error(f"Failed {sol_file.name}: {e}")
    
    print(f"\n✓ Processed {processed} vulnerable contracts")
    return processed

def process_safe_contracts(pipeline):
    """Process safe contracts with nested structure"""
    safe_path = Path("blockchain/contracts/new_safe")
    processed = 0
    
    # Walk through all subdirectories
    for sol_file in safe_path.rglob("*.sol"):
        if sol_file.is_file():
            try:
                contract_name = extract_contract_name(sol_file)
                
                # Get the source hierarchy
                rel_path = sol_file.relative_to(safe_path)
                parts = rel_path.parts
                
                # Determine data source from path structure
                if len(parts) > 1:
                    # e.g., consensys_audited/compound/SomeContract.sol
                    data_source = f"{parts[0]}_{parts[1]}"
                else:
                    # e.g., erc_standards/SomeContract.sol
                    data_source = parts[0]
                
                metadata = {
                    'ground_truth_label': 'safe',
                    'ground_truth_vuln_type': 'none',
                    'data_source': data_source,
                    'file_path': str(sol_file),
                    'relative_path': str(rel_path)
                }
                
                pipeline.analyze_contract(
                    contract_path=sol_file,
                    contract_name=contract_name,
                    metadata=metadata
                )
                processed += 1
                
                if processed % 5 == 0:
                    print(f"  Processed {processed} safe contracts...")
                    
            except Exception as e:
                logger.error(f"Failed {sol_file.name}: {e}")
    
    print(f"\n✓ Processed {processed} safe contracts")
    return processed

def count_contracts():
    """Count contracts in the new structure"""
    print("\n📊 CONTRACT COUNT")
    print("="*50)
    
    # Vulnerable contracts
    vulnerable_path = Path("blockchain/contracts/new_vulnerable")
    vuln_counts = {}
    total_vuln = 0
    
    for vuln_dir in vulnerable_path.iterdir():
        if vuln_dir.is_dir():
            count = len(list(vuln_dir.rglob("*.sol")))
            vuln_counts[vuln_dir.name] = count
            total_vuln += count
    
    print("\n🔴 VULNERABLE CONTRACTS:")
    for category, count in vuln_counts.items():
        print(f"  {category}: {count} contracts")
    print(f"  Total vulnerable: {total_vuln}")
    
    # Safe contracts
    safe_path = Path("blockchain/contracts/new_safe")
    safe_counts = {}
    total_safe = 0
    
    for sol_file in safe_path.rglob("*.sol"):
        rel_path = sol_file.relative_to(safe_path)
        parent = rel_path.parts[0] if len(rel_path.parts) > 0 else "unknown"
        safe_counts[parent] = safe_counts.get(parent, 0) + 1
        total_safe += 1
    
    print("\n🟢 SAFE CONTRACTS:")
    for source, count in safe_counts.items():
        print(f"  {source}: {count} contracts")
    print(f"  Total safe: {total_safe}")
    
    print("\n" + "="*50)
    print(f"📈 GRAND TOTAL: {total_vuln + total_safe} new contracts")
    
    return total_vuln, total_safe

def main():
    print("\n" + "="*70)
    print("🧠 DATASET EXPANSION - FIXED FOR NESTED STRUCTURE")
    print("="*70)
    
    # First, count what we have
    total_vuln, total_safe = count_contracts()
    
    # Get current database count
    db = DatabaseManager()
    current_count = db.get_contract_count()
    print(f"\nCurrent database: {current_count} contracts")
    
    # Ask for confirmation
    proceed = input(f"\nProceed with integrating {total_vuln + total_safe} new contracts? (y/n): ")
    if proceed.lower() != 'y':
        print("Integration cancelled.")
        return
    
    # Initialize pipeline
    pipeline = FeaturePipeline()
    
    # Process vulnerable contracts
    print("\n" + "="*70)
    print("📥 PROCESSING VULNERABLE CONTRACTS...")
    print("="*70)
    vuln_count = process_vulnerable_contracts(pipeline)
    
    # Process safe contracts
    print("\n" + "="*70)
    print("📥 PROCESSING SAFE CONTRACTS...")
    print("="*70)
    safe_count = process_safe_contracts(pipeline)
    
    # Get new total
    new_count = db.get_contract_count()
    added = new_count - current_count
    
    print("\n" + "="*70)
    print("✅ INTEGRATION COMPLETE")
    print("="*70)
    print(f"\n📊 RESULTS:")
    print(f"  Previously in database: {current_count} contracts")
    print(f"  Expected to add:        {total_vuln + total_safe}")
    print(f"  Actually added:         {added}")
    print(f"  New database total:     {new_count}")
    
    if added < (total_vuln + total_safe):
        print(f"  ⚠️  Some contracts failed to process: {total_vuln + total_safe - added}")
    
    # Export updated dataset
    print(f"\n💾 Exporting dataset...")
    output_path = Path("data/dataset_v2_expanded.csv")
    pipeline.save_dataset(output_path)
    print(f"  Saved to: {output_path}")
    
    # Show final distribution
    print(f"\n📈 FINAL DISTRIBUTION:")
    print(f"  Original dataset: 440 contracts")
    print(f"  New contracts:    {added} contracts")
    print(f"  Expanded total:   {new_count} contracts")
    print(f"  Growth:           {new_count/440:.1f}x larger!")

if __name__ == "__main__":
    main()
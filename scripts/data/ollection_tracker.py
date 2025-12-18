# scripts/data/collectors/collection_tracker.py

"""
Track collection progress for balanced dataset.
"""
import csv
from pathlib import Path
from typing import Dict, List
from datetime import datetime

class CollectionTracker:
    """Track which contracts have been collected and their metadata."""
    
    def __init__(self, log_path: str = "data/vulnerable_complex/collection_log.csv"):
        self.log_path = Path(log_path)
        self._init_log()
    
    def _init_log(self):
        """Initialize log file with headers."""
        if not self.log_path.exists():
            with open(self.log_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'source', 'contract_name', 'address',
                    'vulnerability_type', 'complexity', 'lines_of_code',
                    'file_path', 'collection_status', 'notes'
                ])
    
    def log_contract(self, metadata: Dict):
        """
        Log a collected contract.
        
        Args:
            metadata: Dict with keys:
                - source: 'rekt_news', 'slowmist', etc.
                - contract_name: Name of contract
                - address: Ethereum address (if available)
                - vulnerability_type: 'reentrancy', 'access_control', etc.
                - complexity: 'high', 'medium', 'low'
                - lines_of_code: Estimated LOC
                - file_path: Where .sol file is saved
                - collection_status: 'success', 'failed', 'pending'
                - notes: Any additional info
        """
        with open(self.log_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                metadata.get('source', ''),
                metadata.get('contract_name', ''),
                metadata.get('address', ''),
                metadata.get('vulnerability_type', ''),
                metadata.get('complexity', ''),
                metadata.get('lines_of_code', 0),
                metadata.get('file_path', ''),
                metadata.get('collection_status', 'pending'),
                metadata.get('notes', '')
            ])
    
    def get_stats(self) -> Dict:
        """Get collection statistics."""
        stats = {
            'total': 0,
            'by_source': {},
            'by_vuln_type': {},
            'by_status': {},
            'avg_loc': 0
        }
        
        if not self.log_path.exists():
            return stats
        
        with open(self.log_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            stats['total'] = len(rows)
            
            for row in rows:
                # Count by source
                source = row['source']
                stats['by_source'][source] = stats['by_source'].get(source, 0) + 1
                
                # Count by vulnerability type
                vuln = row['vulnerability_type']
                stats['by_vuln_type'][vuln] = stats['by_vuln_type'].get(vuln, 0) + 1
                
                # Count by status
                status = row['collection_status']
                stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            
            # Calculate average LOC
            locs = [int(row['lines_of_code']) for row in rows if row['lines_of_code'].isdigit()]
            stats['avg_loc'] = sum(locs) / len(locs) if locs else 0
        
        return stats
    
    def print_progress(self):
        """Print collection progress."""
        stats = self.get_stats()
        
        print("="*70)
        print("COLLECTION PROGRESS")
        print("="*70)
        print(f"Total contracts collected: {stats['total']}")
        print(f"Average LOC: {stats['avg_loc']:.0f}")
        print()
        
        print("By Source:")
        for source, count in sorted(stats['by_source'].items()):
            print(f"  {source:20s} {count:3d}")
        print()
        
        print("By Vulnerability Type:")
        for vuln, count in sorted(stats['by_vuln_type'].items()):
            print(f"  {vuln:20s} {count:3d}")
        print()
        
        print("By Status:")
        for status, count in sorted(stats['by_status'].items()):
            print(f"  {status:20s} {count:3d}")
        print("="*70)


if __name__ == "__main__":
    tracker = CollectionTracker()
    tracker.print_progress()
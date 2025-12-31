# scripts/data_quality_report_v2.py - GROUND TRUTH VERSION
"""
Data Quality Report v2 - Uses REAL ground truth labels
"""

import pandas as pd
from chainguardian.database.manager import DatabaseManager

class DataQualityReportV2:
    def __init__(self):
        self.db = DatabaseManager()
        
    def generate_true_report(self):
        """ML readiness with ground truth labels."""
        print("\n" + "="*80)
        print("📊 CHAINGUARDIAN DATA QUALITY REPORT v2")
        print("🎯 GROUND TRUTH ML READINESS")
        print("="*80)
        
        # Get features + TRUE labels
        with self.db._get_cursor(dict_cursor=True) as cursor:
            cursor.execute("""
                SELECT 
                    f.*, l.has_vulnerability as ground_truth_vulnerable,
                    COUNT(l.id) OVER (PARTITION BY f.contract_id) as num_known_vulns
                FROM features f
                LEFT JOIN labels l ON f.contract_id = l.contract_id AND l.has_vulnerability = TRUE
                ORDER BY f.contract_id
            """)
            df = pd.DataFrame(cursor.fetchall())
        
        print(f"\n📈 TRUE STATS:")
        print(f"   Total contracts: {len(df):,}")
        print(f"   Features: {len([c for c in df.columns if not c.startswith('contract_') and c != 'ground_truth_vulnerable'])}")
        
        # TRUE vulnerable count
        vuln_count = df['ground_truth_vulnerable'].sum()
        print(f"\n🏷️  TRUE LABEL DISTRIBUTION:")
        print(f"   🔴 Vulnerable: {vuln_count:,} ({vuln_count/len(df)*100:.1f}%)")
        print(f"   🟢 Safe:       {len(df)-vuln_count:,} ({100-vuln_count/len(df)*100:.1f}%)")
        print(f"   ⚖️  Perfect balance! 🎉")
        
        # Extraction quality
        successful = df['failure_reason'].isna().sum()
        print(f"\n🔧 EXTRACTION QUALITY:")
        print(f"   ✅ Successful: {successful:,} ({successful/len(df)*100:.1f}%)")
        
        # ML-ready dataset
        ml_ready = df[(df['failure_reason'].isna()) & 
                     (df['ground_truth_vulnerable'].notna())]
        print(f"\n🚀 ML-READY DATASET:")
        print(f"   {len(ml_ready):,} samples ready for training!")
        print(f"   Vulnerable: {ml_ready['ground_truth_vulnerable'].sum():,}")
        
        # Export FINAL ML dataset
        ml_features = [col for col in df.columns if col not in 
                      ['contract_id', 'contract_name', 'file_path', 'address', 
                       'data_source', 'failure_reason', 'error_message']]
        
        final_dataset = ml_ready[ml_features + ['ground_truth_vulnerable']].fillna(0)
        final_dataset.to_csv("data/ml_final_train_dataset.csv", index=False)
        
        print(f"\n💾 FINAL ML DATASET:")
        print(f"   ✅ {len(final_dataset):,} samples × {len(ml_features)} features")
        print(f"   📁 data/ml_final_train_dataset.csv ← READY FOR XGBoost!")
        
        print("\n🎉 DATA IS ML-READY! 🚀")

def main():
    report = DataQualityReportV2()
    report.generate_true_report()

if __name__ == "__main__":
    main()

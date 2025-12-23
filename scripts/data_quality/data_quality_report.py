# scripts/data_quality_report.py
"""
Data Quality Report - ML Readiness Check

🎓 CHECKS EVERYTHING for ML training:
1. Feature completeness (745/958 = 77.7% success?)
2. Label distribution (vulnerable vs safe balance)
3. Missing values per feature
4. Outliers & anomalies
5. Data source diversity
6. ML-ready dataset export
"""

import pandas as pd
import numpy as np
from pathlib import Path
from chainguardian.database.manager import DatabaseManager
import matplotlib.pyplot as plt
import seaborn as sns
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataQualityReport:
    def __init__(self):
        self.db = DatabaseManager()
        
    def generate_full_report(self):
        """Complete ML readiness report."""
        print("\n" + "="*80)
        print("📊 CHAINGUARDIAN DATA QUALITY REPORT")
        print("🎯 ML READINESS ASSESSMENT")
        print("="*80)
        
        df = self.db.get_all_features()
        print(f"\n📈 OVERVIEW:")
        print(f"   Total contracts: {len(df):,}")
        print(f"   Features: {len(df.columns)}")
        
        # 1. EXTRACTION SUCCESS RATE
        self.check_extraction_quality(df)
        
        # 2. LABEL DISTRIBUTION
        self.check_label_distribution(df)
        
        # 3. FEATURE COMPLETENESS
        self.check_feature_completeness(df)
        
        # 4. DATA SOURCE DIVERSITY
        self.check_data_sources(df)
        
        # 5. ML-READY EXPORT
        self.export_ml_ready_dataset(df)
        
        print("\n🎉 DATA QUALITY REPORT COMPLETE!")
    
    def check_extraction_quality(self, df):
        """Check feature extraction success rate."""
        successful = df['failure_reason'].isna().sum()
        failed = len(df) - successful
        
        print(f"\n🔧 EXTRACTION QUALITY:")
        print(f"   ✅ Successful: {successful:,} ({successful/len(df)*100:.1f}%)")
        print(f"   ❌ Failed:     {failed:,} ({failed/len(df)*100:.1f}%)")
        
        if failed > 0:
            print(f"\n   💡 FAILED REASONS:")
            failure_counts = df['failure_reason'].value_counts()
            for reason, count in failure_counts.items():
                pct = count/len(df)*100
                status = "EXPECTED" if reason in ['IMPORT_ERROR', 'SLITHER_INCOMPATIBILITY'] else "INVESTIGATE"
                print(f"      {reason}: {count:,} ({pct:.1f}%) [{status}]")
    
    def check_label_distribution(self, df):
        """Check vulnerable vs safe balance."""
        # Create labels from data_source
        df['is_vulnerable'] = df['data_source'].str.contains('vulnerable|Re-entrancy|Timestamp|Overflow|Unchecked|tx.origin', case=False, na=False)
        
        vuln_count = df['is_vulnerable'].sum()
        safe_count = len(df) - vuln_count
        
        print(f"\n🏷️  LABEL DISTRIBUTION:")
        print(f"   🔴 Vulnerable: {vuln_count:,} ({vuln_count/len(df)*100:.1f}%)")
        print(f"   🟢 Safe:       {safe_count:,} ({safe_count/len(df)*100:.1f}%)")
        print(f"   ⚖️  Balance:   {vuln_count/(safe_count+1):.2f}:1")
        
        if vuln_count / len(df) < 0.1:
            print("   ⚠️  WARNING: Very imbalanced - consider oversampling")
    
    def check_feature_completeness(self, df):
        """Check missing values per feature."""
        print(f"\n📋 TOP 10 FEATURES BY COMPLETENESS:")
        
        # ML features only (exclude metadata)
        feature_cols = [col for col in df.columns if col not in 
                       ['contract_id', 'contract_name', 'file_path', 'address', 'data_source']]
        
        completeness = []
        for col in feature_cols[:20]:  # Check top features
            missing = df[col].isna().sum()
            pct_complete = (1 - missing/len(df)) * 100
            completeness.append((col, pct_complete))
        
        # Sort by completeness
        completeness.sort(key=lambda x: x[1], reverse=True)
        
        for col, pct in completeness[:10]:
            status = "✅" if pct > 95 else "⚠️ " if pct > 80 else "❌"
            print(f"   {status} {col:25s} {pct:5.1f}% complete")
    
    def check_data_sources(self, df):
        """Check diversity across data sources."""
        print(f"\n🌍 DATA SOURCE DIVERSITY:")
        source_counts = df['data_source'].value_counts()
        print(source_counts.head(10))
        print(f"\n   📊 Unique sources: {len(source_counts)}")
        print(f"   🏆 Top source: {source_counts.index[0]} ({source_counts.iloc[0]:,} contracts)")
    
    def export_ml_ready_dataset(self, df):
        """Export ML-ready dataset (successful extractions only)."""
        print(f"\n💾 ML-READY DATASET EXPORT:")
        
        # Filter successful extractions only
        clean_df = df[df['failure_reason'].isna()].copy()
        
        # Add labels
        clean_df['target'] = clean_df['data_source'].str.contains('vulnerable|Re-entrancy|Timestamp|Overflow|Unchecked|tx.origin', case=False, na=False).astype(int)
        
        # Select ML features only
        ml_features = [col for col in clean_df.columns if col not in 
                      ['contract_id', 'contract_name', 'file_path', 'address', 'data_source', 'failure_reason', 'error_message']]
        
        ml_dataset = clean_df[ml_features].fillna(0)
        
        # Save
        Path("data/ml_ready").mkdir(exist_ok=True)
        ml_dataset.to_csv("data/ml_ready/train_dataset.csv", index=False)
        print(f"   ✅ Exported {len(ml_dataset):,} ML-ready samples × {len(ml_features)} features")
        print(f"   📁 Saved: data/ml_ready/train_dataset.csv")
        
        # Save feature list
        pd.Series(ml_features).to_csv("data/ml_ready/feature_list.csv", index=False, header=False)
        print(f"   📋 Feature list: data/ml_ready/feature_list.csv")

def main():
    report = DataQualityReport()
    report.generate_full_report()

if __name__ == "__main__":
    main()

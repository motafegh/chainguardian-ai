import pandas as pd
from pathlib import Path

csv_files = list(Path('data').glob('*.csv'))

print("="*80)
print(f"SCANNING {len(csv_files)} CSV FILES FOR CEI DATA")
print("="*80)

for csv_file in sorted(csv_files):
    try:
        df = pd.read_csv(csv_file)
        
        # Find CEI-related columns
        cei_cols = [c for c in df.columns if 'cei' in c.lower()]
        reentrancy_cols = [c for c in df.columns if 'reentrancy' in c.lower()]
        
        if cei_cols or reentrancy_cols:
            print(f"\n📄 {csv_file.name}")
            print(f"   Rows: {len(df)}")
            
            for col in cei_cols:
                non_zero = (df[col] > 0).sum() if df[col].dtype in ['int64', 'float64'] else 0
                if non_zero > 0:
                    print(f"   ✅ {col}: {non_zero}/{len(df)} non-zero (max={df[col].max():.2f})")
                else:
                    print(f"   ⚠️  {col}: ALL ZERO")
            
            for col in reentrancy_cols:
                if df[col].dtype == 'bool':
                    true_count = df[col].sum()
                    if true_count > 0:
                        print(f"   ✅ {col}: {true_count}/{len(df)} TRUE")
                    else:
                        print(f"   ⚠️  {col}: ALL FALSE")
                        
    except Exception as e:
        print(f"\n❌ {csv_file.name}: {str(e)[:50]}")

print("\n" + "="*80)

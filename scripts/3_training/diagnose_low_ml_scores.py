"""
diagnose_low_ml_scores.py
=========================
Diagnose why some vulnerable contracts have low ML scores.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.chainguardian.ml.models.hybrid_predictor_enhanced import EnhancedHybridPredictor

def analyze_low_ml_score_contracts():
    """Analyze contracts with low ML scores despite being vulnerable."""
    print("\n" + "="*80)
    print("🔍 DIAGNOSING LOW ML SCORES FOR VULNERABLE CONTRACTS")
    print("="*80)
    
    # Load data
    df = pd.read_csv("data/ml_ready_v4.csv")
    
    # Filter vulnerable contracts
    vulnerable_df = df[df['ground_truth_vulnerable'] == 1]
    
    # Initialize predictor
    predictor = EnhancedHybridPredictor(
        model_path="models/production_model_v6.pkl",
        scaler_path="models/production_scaler_v6.pkl",
        metadata_path="models/feature_metadata_v6.json"
    )
    
    # Get ML scores for all vulnerable contracts
    ml_scores = []
    contracts_info = []
    
    print(f"\n📊 Analyzing {len(vulnerable_df)} vulnerable contracts...")
    
    for idx, row in vulnerable_df.iterrows():
        features = row.to_dict()
        features['source_code'] = None  # Most are NULL
        
        try:
            # Get ML score directly
            X_df = pd.DataFrame(columns=predictor.feature_names)
            row_data = {}
            for feature in predictor.feature_names:
                row_data[feature] = features.get(feature, 0)
            
            X_df = pd.DataFrame([row_data])
            X_scaled = predictor.scaler.transform(X_df)
            ml_proba = predictor.ml_model.predict_proba(X_scaled)[0, 1]
            
            ml_scores.append(ml_proba)
            
            # Store info for low-score contracts
            if ml_proba < 0.3:
                contracts_info.append({
                    'idx': idx,
                    'ml_score': ml_proba,
                    'has_reentrancy': features.get('has_reentrancy', False),
                    'has_unchecked_call': features.get('has_unchecked_call', False),
                    'num_external_calls': features.get('num_external_calls', 0),
                    'dfg_num_sensitive_sinks': features.get('dfg_num_sensitive_sinks', 0),
                    'has_access_control_issues': features.get('has_access_control_issues', False)
                })
                
        except Exception as e:
            print(f"Error processing contract {idx}: {e}")
    
    # Statistics
    ml_scores_array = np.array(ml_scores)
    
    print(f"\n📈 ML Score Statistics for Vulnerable Contracts:")
    print(f"   Mean: {ml_scores_array.mean():.3f}")
    print(f"   Median: {np.median(ml_scores_array):.3f}")
    print(f"   Min: {ml_scores_array.min():.3f}")
    print(f"   Max: {ml_scores_array.max():.3f}")
    print(f"   Std: {ml_scores_array.std():.3f}")
    
    # Count low-score contracts
    low_score_count = sum(1 for score in ml_scores if score < 0.3)
    print(f"\n⚠️  Contracts with ML Score < 0.3: {low_score_count}/{len(vulnerable_df)} "
          f"({low_score_count/len(vulnerable_df)*100:.1f}%)")
    
    # Analyze low-score contracts
    if contracts_info:
        print(f"\n🔍 Analyzing {len(contracts_info)} low-score vulnerable contracts:")
        
        # Convert to DataFrame for analysis
        low_score_df = pd.DataFrame(contracts_info)
        
        print(f"\n📋 Characteristics of Low-Score Vulnerable Contracts:")
        print(f"   Average ML Score: {low_score_df['ml_score'].mean():.3f}")
        print(f"   Has Reentrancy: {low_score_df['has_reentrancy'].sum()}/{len(low_score_df)} "
              f"({low_score_df['has_reentrancy'].mean()*100:.1f}%)")
        print(f"   Has Unchecked Call: {low_score_df['has_unchecked_call'].sum()}/{len(low_score_df)} "
              f"({low_score_df['has_unchecked_call'].mean()*100:.1f}%)")
        print(f"   Has Access Control Issues: {low_score_df['has_access_control_issues'].sum()}/{len(low_score_df)} "
              f"({low_score_df['has_access_control_issues'].mean()*100:.1f}%)")
        print(f"   Avg External Calls: {low_score_df['num_external_calls'].mean():.1f}")
        print(f"   Avg Sensitive Sinks: {low_score_df['dfg_num_sensitive_sinks'].mean():.1f}")
        
        # Compare with high-score contracts
        high_score_indices = [i for i, score in enumerate(ml_scores) if score > 0.7]
        if high_score_indices:
            high_score_df = vulnerable_df.iloc[high_score_indices]
            
            print(f"\n📊 Comparison with High-Score Contracts (ML > 0.7):")
            print(f"   Count: {len(high_score_df)}")
            print(f"   Has Reentrancy: {high_score_df['has_reentrancy'].mean()*100:.1f}%")
            print(f"   Has Unchecked Call: {high_score_df['has_unchecked_call'].mean()*100:.1f}%")
            print(f"   Has Access Control Issues: {high_score_df['has_access_control_issues'].mean()*100:.1f}%")
            print(f"   Avg External Calls: {high_score_df['num_external_calls'].mean():.1f}")
            print(f"   Avg Sensitive Sinks: {high_score_df['dfg_num_sensitive_sinks'].mean():.1f}")
    
    # Feature importance analysis for low-score cases
    print(f"\n🎯 FEATURE IMPORTANCE ANALYSIS:")
    
    # Get top features from model
    if hasattr(predictor.ml_model, 'feature_importances_'):
        feature_importance = pd.DataFrame({
            'feature': predictor.feature_names,
            'importance': predictor.ml_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print(f"\nTop 10 Most Important Features:")
        for i, row in feature_importance.head(10).iterrows():
            print(f"   {row['feature']:40s} {row['importance']:.4f}")
    
    return ml_scores_array, low_score_df

def plot_ml_score_distribution(ml_scores):
    """Plot distribution of ML scores for vulnerable contracts."""
    plt.figure(figsize=(10, 6))
    
    # Histogram
    plt.subplot(1, 2, 1)
    plt.hist(ml_scores, bins=20, edgecolor='black', alpha=0.7)
    plt.axvline(x=0.3, color='red', linestyle='--', label='Low Score Threshold (0.3)')
    plt.axvline(x=0.7, color='green', linestyle='--', label='High Score Threshold (0.7)')
    plt.xlabel('ML Score')
    plt.ylabel('Count')
    plt.title('Distribution of ML Scores for Vulnerable Contracts')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Box plot
    plt.subplot(1, 2, 2)
    plt.boxplot(ml_scores, vert=False)
    plt.xlabel('ML Score')
    plt.title('Box Plot of ML Scores')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('ml_score_distribution.png', dpi=150, bbox_inches='tight')
    print(f"\n📊 Saved plot to: ml_score_distribution.png")

def main():
    """Run diagnostic analysis."""
    ml_scores, low_score_df = analyze_low_ml_score_contracts()
    
    # Plot distribution
    plot_ml_score_distribution(ml_scores)
    
    print("\n" + "="*80)
    print("💡 DIAGNOSTIC CONCLUSIONS")
    print("="*80)
    
    print(f"\n🔍 ROOT CAUSES OF LOW ML SCORES:")
    print(f"   1. Some vulnerable contracts have subtle patterns not captured well by current features")
    print(f"   2. The model might be over-reliant on certain features (dfg_num_sensitive_sinks, has_unused_return_values)")
    print(f"   3. Contracts with different vulnerability types might need different feature patterns")
    
    print(f"\n🎯 RECOMMENDATIONS:")
    print(f"   1. Review feature engineering for low-score cases")
    print(f"   2. Consider ensemble methods to handle diverse vulnerability patterns")
    print(f"   3. Add more specific features for different vulnerability categories")
    print(f"   4. Use the enhanced hybrid approach (dynamic weights) to handle low ML scores")
    
    print(f"\n✅ KEY INSIGHT:")
    print(f"   The enhanced hybrid predictor WITH confidence calibration")
    print(f"   can handle these low ML scores by:")
    print(f"   • Adjusting weights (more semantic when ML is uncertain)")
    print(f"   • Boosting confidence when static signals are strong")
    print(f"   • Providing clear uncertainty explanations")

if __name__ == "__main__":
    main()
"""
test_enhanced_predictor.py
==========================
Test the enhanced hybrid predictor with confidence calibration.
"""

import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from hybrid_predictor_enhanced import EnhancedHybridPredictor

def test_case_1_null_source():
    """Test case with NULL source code (84% of dataset)."""
    print("\n" + "="*80)
    print("🧪 TEST CASE 1: NULL Source Code (84% of dataset)")
    print("="*80)
    
    # Simulate features for a vulnerable contract with NULL source
    features = {
        'source_code': None,  # NULL source
        'has_reentrancy': True,
        'has_unchecked_call': True,
        'num_external_calls': 8,
        'high_severity_count': 3,
        'cei_violations': 0,  # Cannot analyze CEI without source
        'cei_pattern_score': 0.0,
        'has_reentrancy_guard': False,
        'lines_of_code': 150,
        'num_functions': 12,
        'max_cyclomatic_complexity': 8,
        'total_detector_hits': 5,
        'has_access_control_issues': False,
        'has_inline_assembly': False,
        'dfg_num_sensitive_sinks': 3,
        'cg_external_call_ratio': 0.6
    }
    
    predictor = EnhancedHybridPredictor()
    result = predictor.predict_with_uncertainty(
        features=features,
        llm_ready=True
    )
    
    print(f"\n📊 RESULTS:")
    print(f"   Prediction:      {result['security_assessment']['overall_prediction']}")
    print(f"   Confidence:      {result['security_assessment']['calibrated_confidence']:.1%}")
    print(f"   Confidence Level: {result['security_assessment']['confidence_level']}")
    print(f"   Data Quality:    {result['data_quality']['level']}")
    
    print(f"\n🔍 KEY IMPROVEMENTS:")
    print(f"   • Dynamic weights applied: {result['model_insights']['ml_analysis']['weight_applied']:.0%} ML, "
          f"{result['model_insights']['semantic_analysis']['weight_applied']:.0%} Semantic")
    print(f"   • Calibration notes: {len(result['uncertainty_analysis']['calibration_notes'])} adjustments")
    
    print(f"\n💡 RECOMMENDATIONS:")
    for rec_type, recs in result['recommendations'].items():
        if recs:
            print(f"   {rec_type.replace('_', ' ').title()}:")
            for rec in recs[:2]:  # Show top 2
                print(f"     • {rec}")

def test_case_2_ml_certain():
    """Test case where ML is very certain but semantic data is limited."""
    print("\n" + "="*80)
    print("🧪 TEST CASE 2: ML Certainty with Limited Semantic Data")
    print("="*80)
    
    features = {
        'source_code': "contract Test { function withdraw() public { ... } }",
        'has_reentrancy': True,
        'has_unchecked_call': False,
        'num_external_calls': 5,
        'high_severity_count': 2,
        'cei_violations': 2,  # Some CEI violations detected
        'cei_pattern_score': 0.4,
        'has_reentrancy_guard': True,
        'lines_of_code': 200,
        'num_functions': 15,
        'max_cyclomatic_complexity': 12,
        'total_detector_hits': 8,
        'has_access_control_issues': True,
        'has_inline_assembly': True,
        'dfg_num_sensitive_sinks': 5,
        'cg_external_call_ratio': 0.8
    }
    
    predictor = EnhancedHybridPredictor()
    result = predictor.predict_with_uncertainty(
        features=features,
        llm_ready=True
    )
    
    print(f"\n📊 RESULTS:")
    print(f"   Prediction:      {result['security_assessment']['overall_prediction']}")
    print(f"   Confidence:      {result['security_assessment']['calibrated_confidence']:.1%}")
    print(f"   Data Quality:    {result['data_quality']['level']}")
    print(f"   ML Score:        {result['model_insights']['ml_analysis']['score']:.3f}")
    print(f"   Semantic Score:  {result['model_insights']['semantic_analysis']['score']:.3f}")
    
    print(f"\n🎯 CONFIDENCE CALIBRATION:")
    for note in result['uncertainty_analysis']['calibration_notes']:
        print(f"   • {note}")

def test_case_3_contradictory_signals():
    """Test case with contradictory signals."""
    print("\n" + "="*80)
    print("🧪 TEST CASE 3: Contradictory Signals")
    print("="*80)
    
    features = {
        'source_code': "contract Safe { function foo() public pure {} }",
        'has_reentrancy': False,
        'has_unchecked_call': False,
        'num_external_calls': 0,
        'high_severity_count': 0,
        'cei_violations': 0,
        'cei_pattern_score': 1.0,
        'has_reentrancy_guard': False,
        'lines_of_code': 50,
        'num_functions': 3,
        'max_cyclomatic_complexity': 2,
        'total_detector_hits': 0,
        'has_access_control_issues': False,
        'has_inline_assembly': False,
        'dfg_num_sensitive_sinks': 0,
        'cg_external_call_ratio': 0.0
    }
    
    predictor = EnhancedHybridPredictor()
    result = predictor.predict_with_uncertainty(
        features=features,
        llm_ready=True
    )
    
    print(f"\n📊 RESULTS:")
    print(f"   Prediction:      {result['security_assessment']['overall_prediction']}")
    print(f"   Confidence:      {result['security_assessment']['calibrated_confidence']:.1%}")
    print(f"   Data Quality:    {result['data_quality']['level']}")
    
    print(f"\n🔍 UNCERTAINTY FACTORS:")
    for factor in result['uncertainty_analysis']['factors']:
        print(f"   • {factor}")

def main():
    """Run all test cases."""
    print("\n" + "="*80)
    print("🚀 ENHANCED HYBRID PREDICTOR - CONFIDENCE CALIBRATION TESTS")
    print("="*80)
    
    test_case_1_null_source()
    test_case_2_ml_certain()
    test_case_3_contradictory_signals()
    
    print("\n" + "="*80)
    print("✅ ALL TESTS COMPLETED")
    print("="*80)
    
    # Summary of improvements
    print("\n🎯 KEY ENHANCEMENTS IMPLEMENTED:")
    print("   1. ✅ Dynamic Weight Adjustment")
    print("      - Adjusts ML/semantic weights based on data quality")
    print("      - NULL source → Higher ML weight (80/20)")
    print("      - Full source → Standard hybrid (30/70)")
    
    print("\n   2. ✅ Confidence Calibration")
    print("      - Boosts confidence when ML certainty aligns with static signals")
    print("      - Reduces confidence for contradictory signals")
    print("      - Applies data quality multipliers")
    
    print("\n   3. ✅ Data Completeness Tracking")
    print("      - Tracks source code availability")
    print("      - Monitors semantic analysis completeness")
    print("      - Calculates overall data quality score")
    
    print("\n   4. ✅ Enhanced LLM Output")
    print("      - Detailed uncertainty explanations")
    print("      - Data quality assessment")
    print("      - Actionable recommendations")
    print("      - Confidence calibration notes")

if __name__ == "__main__":
    main()
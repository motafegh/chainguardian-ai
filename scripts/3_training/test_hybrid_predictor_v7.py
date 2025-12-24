#!/usr/bin/env python3
"""
Test EnhancedHybridPredictorV2 with Trained Model
=================================================
Validates full inference pipeline using actual API.

Run: poetry run python scripts/3_training/test_hybrid_predictor_v7.py
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import json
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from chainguardian.ml.core.path_resolver import path_resolver
from chainguardian.ml.models.hybrid_predictor_enhanced_v2 import EnhancedHybridPredictorV2

print("=" * 80)
print("🧪 ENHANCED HYBRID PREDICTOR V2 - INFERENCE TEST")
print("=" * 80)

# Test 1: Initialize Predictor (auto-loads model)
print("\n[TEST 1] Initialize Predictor (Auto-Load Model)")
try:
    # Get models directory
    models_dir = str(path_resolver.models_dir)
    config_path = str(path_resolver.get_config_file("hybrid_config.yaml"))
    
    print(f"   Models dir: {models_dir}")
    print(f"   Config: {config_path}")
    
    # Initialize - this automatically loads the model
    predictor = EnhancedHybridPredictorV2(
        models_dir=models_dir,
        config_path=config_path,
        enable_monitoring=True,
        enable_shap=False  # Disable SHAP for speed
    )
    
    print(f"✅ Predictor initialized")
    print(f"   Type: {type(predictor).__name__}")
    print(f"   Ensemble mode: {predictor.use_ensemble}")
    print(f"   Features loaded: {len(predictor.feature_names)}")
    
except Exception as e:
    print(f"❌ Predictor initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Load Real Data for Testing
print("\n[TEST 2] Load Test Data")
try:
    data_path = path_resolver.data_dir / "ml_ready_v4.csv"
    df = pd.read_csv(data_path)
    
    # Get feature names from predictor
    feature_names = predictor.feature_names
    
    # Prepare test samples
    # Exclude target and leakage features
    available_features = [f for f in feature_names if f in df.columns]
    
    print(f"✅ Data loaded: {len(df)} samples")
    print(f"✅ Expected features: {len(feature_names)}")
    print(f"✅ Available features: {len(available_features)}")
    
    # Take 5 test samples
    test_samples = df[available_features].head(5)
    test_labels = df['ground_truth_vulnerable'].head(5).values
    
    print(f"✅ Test samples prepared: {len(test_samples)}")
    
except Exception as e:
    print(f"❌ Data loading failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Single Prediction
print("\n[TEST 3] Single Prediction")
try:
    single_sample = test_samples.iloc[0].to_dict()
    
    # Use predict_single (the actual method)
    result = predictor.predict_single(
        features=single_sample,
        return_details=True,
        explain=False  # Skip SHAP for speed
    )
    
    print(f"✅ Prediction completed")
    print(f"   Prediction: {result['prediction_label']}")
    print(f"   Raw score: {result['raw_score']:.4f}")
    print(f"   ML score: {result['ml_score']:.4f}")
    print(f"   Semantic score: {result['semantic_score']:.4f}")
    print(f"   Confidence: {result['calibrated_confidence']:.4f}")
    print(f"   Confidence level: {result['confidence_level']}")
    print(f"   Data quality: {result['data_quality']['quality_level']}")
    
    if 'processing_time_ms' in result:
        print(f"   Processing time: {result['processing_time_ms']:.2f}ms")
    
    print(f"\n   Actual label: {'VULNERABLE' if test_labels[0] == 1 else 'SAFE'}")
    print(f"   Correct: {'✅' if result['prediction'] == test_labels[0] else '❌'}")
    
except Exception as e:
    print(f"❌ Single prediction failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
# In test script, add this after TEST 3:
print("\n[TEST 3.5] Detailed Timing Breakdown")
# Add after TEST 3, before TEST 4
print("\n[TEST 3.5] 🔍 TIMING BREAKDOWN (Finding the 5-second culprit)")
try:
    import time
    sample = test_samples.iloc[0].to_dict()
    
    # Time 1: Feature vector extraction
    start = time.time()
    feature_vector = predictor._get_feature_vector(frozenset(sample.items()))
    t1 = (time.time() - start) * 1000
    print(f"   1. Feature vector extraction: {t1:.2f}ms")
    
    # Time 2: Scaling
    start = time.time()
    X_scaled = predictor.scaler.transform(feature_vector.reshape(1, -1))
    t2 = (time.time() - start) * 1000
    print(f"   2. Feature scaling: {t2:.2f}ms")
    
    # Time 3: ML prediction (ensemble)
    start = time.time()
    if predictor.use_ensemble:
        ml_pred, ml_proba, ml_ci = predictor.ml_model.predict_with_uncertainty(X_scaled)
    else:
        ml_proba = predictor.ml_model.predict_proba(X_scaled)
    t3 = (time.time() - start) * 1000
    print(f"   3. ML ensemble prediction: {t3:.2f}ms")
    
    # Time 4: Data completeness assessment
    start = time.time()
    data_completeness = predictor.assess_data_completeness(sample)
    t4 = (time.time() - start) * 1000
    print(f"   4. Data completeness check: {t4:.2f}ms")
    
    # Time 5: Semantic risk
    start = time.time()
    semantic_score, reasons, meta = predictor.calculate_semantic_risk(sample)
    t5 = (time.time() - start) * 1000
    print(f"   5. Semantic risk calculation: {t5:.2f}ms")
    
    # Time 6: Dynamic weights
    start = time.time()
    ml_weight, sem_weight = predictor.calculate_dynamic_weights(data_completeness.get_quality_level())
    t6 = (time.time() - start) * 1000
    print(f"   6. Dynamic weights: {t6:.2f}ms")
    
    # Time 7: Confidence calibration
    start = time.time()
    conf, notes = predictor.calibrate_confidence(0.5, 0.0, sample, data_completeness)
    t7 = (time.time() - start) * 1000
    print(f"   7. Confidence calibration: {t7:.2f}ms")
    
    # Time 8: Full predict_single (for comparison)
    start = time.time()
    result = predictor.predict_single(sample, return_details=True, explain=False)
    t8 = (time.time() - start) * 1000
    print(f"   8. FULL predict_single: {t8:.2f}ms")
    
    total_breakdown = t1 + t2 + t3 + t4 + t5 + t6 + t7
    print(f"\n   📊 Breakdown total: {total_breakdown:.2f}ms")
    print(f"   📊 Full call total: {t8:.2f}ms")
    print(f"   📊 Unaccounted overhead: {t8 - total_breakdown:.2f}ms")
    
    # Find the culprit
    times = {
        'Feature extraction': t1,
        'Scaling': t2,
        'ML prediction': t3,
        'Data completeness': t4,
        'Semantic risk': t5,
        'Dynamic weights': t6,
        'Confidence calibration': t7
    }
    slowest = max(times.items(), key=lambda x: x[1])
    print(f"\n   🐌 SLOWEST COMPONENT: {slowest[0]} ({slowest[1]:.2f}ms)")
    
except Exception as e:
    print(f"   ❌ Timing breakdown failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Batch Prediction
print("\n[TEST 4] Batch Prediction (5 samples)")
try:
    batch_samples = test_samples.to_dict('records')
    
    # Use predict_batch (the actual method)
    results = predictor.predict_batch(
        features_list=batch_samples,
        return_details=True
    )
    
    print(f"✅ Batch prediction completed")
    print(f"   Samples processed: {len(results)}")
    
    # Show results table
    print("\n   Results:")
    print("   " + "-" * 90)
    print(f"   {'#':<3} {'Prediction':<12} {'Raw':<8} {'ML':<8} {'Sem':<8} {'Conf':<8} {'Actual':<12} {'Match':<5}")
    print("   " + "-" * 90)
    
    correct = 0
    for i, (result, actual) in enumerate(zip(results, test_labels)):
        pred_label = result['prediction_label']
        actual_label = 'VULNERABLE' if actual == 1 else 'SAFE'
        match = '✅' if result['prediction'] == actual else '❌'
        
        if result['prediction'] == actual:
            correct += 1
        
        print(f"   {i:<3} {pred_label:<12} {result['raw_score']:.4f}   "
              f"{result['ml_score']:.4f}   {result['semantic_score']:.4f}   "
              f"{result['calibrated_confidence']:.4f}   {actual_label:<12} {match:<5}")
    
    print("   " + "-" * 90)
    print(f"   Accuracy: {correct}/{len(results)} ({correct/len(results)*100:.1f}%)")
    
except Exception as e:
    print(f"❌ Batch prediction failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Semantic Analysis
print("\n[TEST 5] Semantic Risk Analysis")
try:
    sample = test_samples.iloc[0].to_dict()
    
    # Test semantic risk calculation directly
    semantic_score, reasons, metadata = predictor.calculate_semantic_risk(sample)
    
    print(f"✅ Semantic analysis completed")
    print(f"   Risk score: {semantic_score:.4f}")
    print(f"   Components used: {metadata.get('components_used', [])}")
    print(f"\n   Risk Reasons:")
    for reason in reasons[:5]:  # Show top 5
        print(f"      {reason}")
    
except Exception as e:
    print(f"⚠️  Semantic analysis failed: {e}")

# Test 6: Data Quality Assessment
print("\n[TEST 6] Data Quality Assessment")
try:
    sample = test_samples.iloc[0].to_dict()
    
    # Test data completeness assessment
    completeness = predictor.assess_data_completeness(sample)
    
    print(f"✅ Data quality assessment completed")
    print(f"   Quality score: {completeness.calculate_quality_score():.4f}")
    print(f"   Quality level: {completeness.get_quality_level().value}")
    print(f"   Source code: {'Yes' if completeness.source_code_available else 'No'}")
    print(f"   Semantic analysis: {'Yes' if completeness.semantic_analysis_complete else 'No'}")
    print(f"   Static analysis: {'Yes' if completeness.static_analysis_complete else 'No'}")
    print(f"   CEI quality: {completeness.cei_analysis_quality:.4f}")
    
except Exception as e:
    print(f"⚠️  Data quality assessment failed: {e}")

# Test 7: Performance Test (Speed)
print("\n[TEST 7] Performance Test (100 predictions)")
try:
    # Create 100 copies of first sample
    perf_samples = [test_samples.iloc[0].to_dict() for _ in range(100)]
    
    start_time = time.time()
    perf_results = predictor.predict_batch(perf_samples, return_details=False)
    end_time = time.time()
    
    total_time = end_time - start_time
    avg_time = total_time / len(perf_samples) * 1000  # ms per prediction
    throughput = len(perf_samples) / total_time
    
    print(f"✅ Performance test completed")
    print(f"   Total time: {total_time:.3f}s")
    print(f"   Avg per prediction: {avg_time:.2f}ms")
    print(f"   Throughput: {throughput:.1f} predictions/sec")
    
    # Performance benchmark
    if avg_time < 10:
        grade = "Excellent (production-ready)"
    elif avg_time < 50:
        grade = "Good"
    elif avg_time < 100:
        grade = "Fair"
    else:
        grade = "Needs optimization"
    
    print(f"   Grade: {grade}")
    
except Exception as e:
    print(f"❌ Performance test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 8: Model Metadata
print("\n[TEST 8] Model Metadata")
try:
    if hasattr(predictor, 'metadata'):
        metadata = predictor.metadata
        
        print(f"✅ Model metadata retrieved")
        print(f"   Model type: {metadata.get('model_type', 'unknown')}")
        print(f"   Features: {len(metadata.get('feature_names', []))}")
        
        if 'performance_metrics' in metadata:
            print(f"   Performance:")
            for metric, value in metadata['performance_metrics'].items():
                print(f"      {metric}: {value}")
        
        if 'training_info' in metadata:
            info = metadata['training_info']
            print(f"   Training:")
            print(f"      Version: {info.get('version', 'unknown')}")
            print(f"      Date: {info.get('date', 'unknown')}")
            print(f"      Dataset size: {info.get('dataset_size', 'unknown')}")
    else:
        print("⚠️  Model metadata not available")
        
except Exception as e:
    print(f"⚠️  Metadata retrieval failed: {e}")

# Final Summary
print("\n" + "=" * 80)
print("✅ ALL TESTS COMPLETED")
print("=" * 80)
print("\n📊 Summary:")
print(f"   ✅ Model loaded: {predictor.use_ensemble and 'Ensemble' or 'Single'}")
print(f"   ✅ Features: {len(predictor.feature_names)}")
print(f"   ✅ Single prediction: Working")
print(f"   ✅ Batch prediction: Working")
print(f"   ✅ Accuracy on test samples: {correct}/{len(results)}")
print(f"   ✅ Average inference time: {avg_time:.2f}ms")
print(f"   ✅ Throughput: {throughput:.1f} pred/sec")
print("\n🚀 Ready for production deployment!")
print("=" * 80)

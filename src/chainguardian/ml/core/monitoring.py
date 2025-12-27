# (Paste the entire monitoring.py content here)
"""
Performance Monitoring and Drift Detection for ChainGuardian AI
================================================================
Tracks model performance, detects data drift, and provides alerts.
"""

import numpy as np
import pandas as pd
from datetime import datetime
from collections import deque
import json
from pathlib import Path
from typing import Dict, Optional, Any, Deque
import logging
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class MLMonitor:
    """
    Comprehensive monitoring system for ML models.
    Tracks predictions, detects drift, and monitors performance.
    """
    
    def __init__(self, config):
        """
        Initialize monitoring system.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.monitoring_config = config.monitoring
        
        # Initialize storage
        self.prediction_history: Deque[Dict] = deque(
            maxlen=self.monitoring_config.get('drift_detection', {}).get('window_size', 1000)
        )
        
        self.performance_metrics: Deque[Dict] = deque(maxlen=1000)
        
        # Drift detection state
        self.reference_distribution = None
        self.last_drift_check = None
        self.drift_detected = False
        
        # Performance baselines
        self.performance_baseline = None
        
        # Setup logging directory
        self.log_dir = Path(self.monitoring_config.get('log_dir', 'logs'))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("ML Monitoring system initialized")
    
    def log_prediction(self, features: Dict, prediction: Dict, 
                      ground_truth: Optional[bool] = None):
        """
        Log a prediction for monitoring.
        
        Args:
            features: Input features
            prediction: Prediction output
            ground_truth: Actual label (if available)
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'features': self._extract_monitoring_features(features),
            'prediction': prediction.get('prediction'),
            'confidence': prediction.get('calibrated_confidence', 0.5),
            'data_quality': prediction.get('data_quality', {}).get('quality_score', 0.0),
            'ground_truth': ground_truth,
            'processing_time_ms': prediction.get('processing_time_ms', 0)
        }
        
        # Store in memory
        self.prediction_history.append(log_entry)
        
        # Save to disk
        self._save_to_log_file(log_entry)
        
        # Check for drift periodically
        self._check_for_drift()
        
        # Update performance metrics if ground truth available
        if ground_truth is not None:
            self._update_performance_metrics(log_entry)
    
    def _extract_monitoring_features(self, features: Dict) -> Dict:
        """
        Extract key features for monitoring and drift detection.
        
        Args:
            features: Full feature dictionary
            
        Returns:
            Subset of features for monitoring
        """
        # Select key features that are important for drift detection
        key_features = [
            'has_reentrancy',
            'has_unchecked_call',
            'num_external_calls',
            'cei_violations',
            'lines_of_code',
            'num_functions',
            'cfg_num_nodes',
            'dfg_num_sensitive_sinks'
        ]
        
        return {k: features.get(k, 0) for k in key_features if k in features}
    
    def _save_to_log_file(self, log_entry: Dict):
        """Save log entry to daily log file."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"predictions_{date_str}.jsonl"
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def _check_for_drift(self):
        """Check for data drift using statistical tests."""
        drift_config = self.monitoring_config.get('drift_detection', {})
        
        if not drift_config.get('enabled', False):
            return
        
        # Check interval
        check_interval = drift_config.get('check_interval', 100)
        if len(self.prediction_history) < check_interval:
            return
        
        if self.last_drift_check is None or \
           len(self.prediction_history) - self.last_drift_check >= check_interval:
            
            self.last_drift_check = len(self.prediction_history)
            
            # Extract recent features
            recent_features = [entry['features'] for entry in self.prediction_history]
            recent_df = pd.DataFrame(recent_features)
            
            if len(recent_df) < 100:  # Need sufficient samples
                return
            
            # Initialize reference distribution if not set
            if self.reference_distribution is None:
                self.reference_distribution = self._calculate_distribution(recent_df)
                logger.info("Reference distribution initialized")
                return
            
            # Calculate current distribution
            current_distribution = self._calculate_distribution(recent_df)
            
            # Compare distributions using Kolmogorov-Smirnov test
            drift_detected, drift_score = self._detect_drift(
                self.reference_distribution, 
                current_distribution,
                drift_config.get('drift_threshold', 0.05)
            )
            
            if drift_detected and not self.drift_detected:
                logger.warning(f"🚨 DATA DRIFT DETECTED! Score: {drift_score:.4f}")
                self.drift_detected = True
                
                # Trigger alert
                self._trigger_alert('data_drift', {
                    'drift_score': drift_score,
                    'samples_analyzed': len(recent_df),
                    'timestamp': datetime.now().isoformat()
                })
            elif not drift_detected and self.drift_detected:
                logger.info("✅ Drift condition cleared")
                self.drift_detected = False
    
    def _calculate_distribution(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate feature distribution statistics.
        
        Args:
            df: DataFrame with features
            
        Returns:
            Distribution statistics
        """
        distribution = {}
        
        for column in df.columns:
            if df[column].dtype in [np.float64, np.int64]:
                distribution[column] = {
                    'mean': float(df[column].mean()),
                    'std': float(df[column].std()),
                    'min': float(df[column].min()),
                    'max': float(df[column].max()),
                    'percentiles': {
                        '25': float(df[column].quantile(0.25)),
                        '50': float(df[column].quantile(0.50)),
                        '75': float(df[column].quantile(0.75))
                    }
                }
            else:
                # For categorical/boolean
                value_counts = df[column].value_counts().to_dict()
                distribution[column] = {
                    'value_counts': value_counts,
                    'unique_values': len(value_counts)
                }
        
        return distribution
    
    def _detect_drift(self, ref_dist: Dict, curr_dist: Dict, threshold: float) -> tuple:
        """
        Detect drift using statistical tests.
        
        Args:
            ref_dist: Reference distribution
            curr_dist: Current distribution
            threshold: Drift detection threshold
            
        Returns:
            (drift_detected, drift_score)
        """
        try:
            from scipy import stats
        except ImportError:
            logger.warning("SciPy not available for statistical tests")
            return False, 0.0
        
        drift_scores = []
        
        for feature in ref_dist.keys():
            if feature not in curr_dist:
                continue
            
            ref_data = ref_dist[feature]
            curr_data = curr_dist[feature]
            
            if 'mean' in ref_data and 'mean' in curr_data:
                # For continuous features, use KS test on simulated data
                # Simulate data from reference distribution
                n_samples = 1000
                ref_samples = np.random.normal(
                    ref_data['mean'], 
                    max(ref_data['std'], 0.01), 
                    n_samples
                )
                
                # Simulate data from current distribution
                curr_samples = np.random.normal(
                    curr_data['mean'], 
                    max(curr_data['std'], 0.01), 
                    n_samples
                )
                
                # Kolmogorov-Smirnov test
                ks_statistic, p_value = stats.ks_2samp(ref_samples, curr_samples)
                drift_scores.append(1 - p_value)  # Convert to drift score
            
            elif 'value_counts' in ref_data and 'value_counts' in curr_data:
                # For categorical features, use chi-square test
                # This is simplified - in production, use proper contingency table
                ref_total = sum(ref_data['value_counts'].values())
                curr_total = sum(curr_data['value_counts'].values())
                
                if ref_total > 0 and curr_total > 0:
                    # Calculate distribution difference
                    common_categories = set(ref_data['value_counts'].keys()) | \
                                      set(curr_data['value_counts'].keys())
                    
                    diff = 0
                    for category in common_categories:
                        ref_prob = ref_data['value_counts'].get(category, 0) / ref_total
                        curr_prob = curr_data['value_counts'].get(category, 0) / curr_total
                        diff += abs(ref_prob - curr_prob)
                    
                    drift_scores.append(diff / len(common_categories))
        
        if not drift_scores:
            return False, 0.0
        
        overall_score = np.mean(drift_scores)
        return overall_score > threshold, overall_score
    
    def _update_performance_metrics(self, log_entry: Dict):
        """
        Update performance metrics based on ground truth.
        
        Args:
            log_entry: Log entry with ground truth
        """
        if log_entry['ground_truth'] is None:
            return
        
        # Calculate performance for this prediction
        correct = log_entry['prediction'] == log_entry['ground_truth']
        confidence = log_entry['confidence']
        
        performance_entry = {
            'timestamp': log_entry['timestamp'],
            'correct': correct,
            'confidence': confidence,
            'data_quality': log_entry['data_quality']
        }
        
        self.performance_metrics.append(performance_entry)
        
        # Update baseline if not set
        if self.performance_baseline is None and len(self.performance_metrics) >= 100:
            self.performance_baseline = self._calculate_performance_baseline()
        
        # Check for performance degradation
        self._check_performance_degradation()
    
    def _calculate_performance_baseline(self) -> Dict:
        """
        Calculate baseline performance metrics.
        
        Returns:
            Baseline performance dictionary
        """
        if len(self.performance_metrics) < 100:
            return {}
        
        recent = list(self.performance_metrics)[-100:]
        
        accuracy = sum(1 for entry in recent if entry['correct']) / len(recent)
        avg_confidence = np.mean([entry['confidence'] for entry in recent])
        calibration_error = abs(accuracy - avg_confidence)
        
        return {
            'accuracy': accuracy,
            'avg_confidence': avg_confidence,
            'calibration_error': calibration_error,
            'sample_size': len(recent),
            'established_at': datetime.now().isoformat()
        }
    
    def _check_performance_degradation(self):
        """Check for performance degradation."""
        if self.performance_baseline is None:
            return
        
        if len(self.performance_metrics) < 50:
            return
        
        # Calculate recent performance
        recent = list(self.performance_metrics)[-50:]
        recent_accuracy = sum(1 for entry in recent if entry['correct']) / len(recent)
        
        baseline_accuracy = self.performance_baseline['accuracy']
        
        # Check for significant degradation
        accuracy_degradation = baseline_accuracy - recent_accuracy
        
        if accuracy_degradation > 0.1:  # More than 10% degradation
            logger.warning("⚠️ PERFORMANCE DEGRADATION DETECTED!")
            logger.warning(f"   Baseline accuracy: {baseline_accuracy:.4f}")
            logger.warning(f"   Recent accuracy: {recent_accuracy:.4f}")
            logger.warning(f"   Degradation: {accuracy_degradation:.4f}")
            
            # Trigger alert
            self._trigger_alert('performance_degradation', {
                'baseline_accuracy': baseline_accuracy,
                'recent_accuracy': recent_accuracy,
                'degradation': accuracy_degradation,
                'samples_analyzed': len(recent)
            })
    
    def _trigger_alert(self, alert_type: str, details: Dict):
        """
        Trigger alert for monitoring events.
        
        Args:
            alert_type: Type of alert
            details: Alert details
        """
        alert = {
            'type': alert_type,
            'timestamp': datetime.now().isoformat(),
            'details': details,
            'severity': 'warning'
        }
        
        # Save alert to file
        alert_file = self.log_dir / f"alerts_{datetime.now().strftime('%Y-%m')}.jsonl"
        with open(alert_file, 'a') as f:
            f.write(json.dumps(alert) + '\n')
        
        # In production, this could trigger:
        # - Email notifications
        # - Slack/Teams messages
        # - PagerDuty alerts
        # - Auto-retraining triggers
        
        logger.warning(f"ALERT: {alert_type} - {details}")
    
    def get_performance_report(self, window_size: int = 100) -> Dict:
        """
        Generate performance report for recent predictions.
        
        Args:
            window_size: Number of recent predictions to include
            
        Returns:
            Performance report dictionary
        """
        if len(self.performance_metrics) < window_size:
            window = list(self.performance_metrics)
        else:
            window = list(self.performance_metrics)[-window_size:]
        
        if not window:
            return {}
        
        # Calculate metrics
        accuracy = sum(1 for entry in window if entry['correct']) / len(window)
        avg_confidence = np.mean([entry['confidence'] for entry in window])
        avg_data_quality = np.mean([entry['data_quality'] for entry in window])
        
        # Calculate calibration metrics
        confidence_bins = np.linspace(0, 1, 11)
        calibration_data = []
        
        for i in range(len(confidence_bins) - 1):
            lower, upper = confidence_bins[i], confidence_bins[i + 1]
            
            bin_entries = [e for e in window if lower <= e['confidence'] < upper]
            
            if bin_entries:
                bin_accuracy = sum(1 for e in bin_entries if e['correct']) / len(bin_entries)
                avg_bin_confidence = np.mean([e['confidence'] for e in bin_entries])
                
                calibration_data.append({
                    'confidence_range': [float(lower), float(upper)],
                    'accuracy': bin_accuracy,
                    'avg_confidence': avg_bin_confidence,
                    'samples': len(bin_entries)
                })
        
        report = {
            'window_size': len(window),
            'time_period': {
                'start': window[0]['timestamp'] if window else None,
                'end': window[-1]['timestamp'] if window else None
            },
            'accuracy': accuracy,
            'average_confidence': avg_confidence,
            'calibration_error': abs(accuracy - avg_confidence),
            'average_data_quality': avg_data_quality,
            'calibration_data': calibration_data,
            'drift_detected': self.drift_detected,
            'performance_baseline': self.performance_baseline
        }
        
        return report
    
    def export_monitoring_data(self, output_path: Optional[str] = None) -> str:
        """
        Export monitoring data for analysis.
        
        Args:
            output_path: Optional output path
            
        Returns:
            Path to exported data
        """
        # ✅ FIX: Use a properly typed local variable
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path: Path = self.log_dir / f"monitoring_export_{timestamp}.json"
        else:
            export_path = Path(output_path)
        
        export_data = {
            'metadata': {
                'exported_at': datetime.now().isoformat(),
                'total_predictions': len(self.prediction_history),
                'total_performance_entries': len(self.performance_metrics)
            },
            'configuration': self.monitoring_config,
            'performance_report': self.get_performance_report(window_size=1000),
            'drift_status': {
                'detected': self.drift_detected,
                'reference_distribution_initialized': self.reference_distribution is not None
            },
            'prediction_sample': list(self.prediction_history)[-100:] if self.prediction_history else [],
            'performance_sample': list(self.performance_metrics)[-100:] if self.performance_metrics else []
        }
        
        # ✅ FIX: Use export_path instead of output_path
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Monitoring data exported to {export_path}")
        return str(export_path)

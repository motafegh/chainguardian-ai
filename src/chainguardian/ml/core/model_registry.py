# (Paste the entire model_registry.py content here)
"""
Model Registry for ChainGuardian AI
====================================
Version control, tracking, and management for ML models.
Provides reproducible model deployment and rollback capabilities.
"""

import json
import joblib
from pathlib import Path
from datetime import datetime
import hashlib
from typing import Dict, List, Optional, Any, cast
import logging
import shutil
from chainguardian.ml.core.path_resolver import path_resolver

logger = logging.getLogger(__name__)

class ModelRegistry:
    """
    Registry for model versioning, tracking, and deployment.
    Implements semantic versioning and comprehensive metadata storage.
    """
    
    def __init__(self, registry_path: Optional[str] = None):
        """
        Initialize model registry with absolute paths.
        
        Args:
            registry_path: Path to registry directory (relative to project root or absolute)
        """
        if registry_path is None:
            # Default: use path_resolver
            self.registry_path = path_resolver.registry_dir
        else:
            # Convert to absolute path
            registry_path_obj = Path(registry_path)
            if not registry_path_obj.is_absolute():
                self.registry_path = path_resolver.project_root / registry_path_obj
            else:
                self.registry_path = registry_path_obj
        
        # Ensure directory exists
        self.registry_path.mkdir(parents=True, exist_ok=True)
        
        # Registry index file
        self.index_file = self.registry_path / "index.json"
        self.registry_index = self._load_index()
        
        logger.info(f"✅ Model registry initialized at: {self.registry_path}")

    
    def _load_index(self) -> Dict[str, Any]:
        """Load or create registry index."""
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                # ✅ FIX: Cast json.load to proper type
                return cast(Dict[str, Any], json.load(f))
        else:
            return {
                'versions': {},
                'latest_version': None,
                'metadata': {
                    'created': datetime.now().isoformat(),
                    'total_models': 0
                }
            }

    
    def _save_index(self):
        """Save registry index to file."""
        with open(self.index_file, 'w') as f:
            json.dump(self.registry_index, f, indent=2)
    
    def _generate_version(self, version_type: str = 'patch') -> str:
        """
        Generate new semantic version.
        
        Args:
            version_type: 'major', 'minor', or 'patch'
            
        Returns:
            Version string (e.g., '1.0.0')
        """
        if not self.registry_index['versions']:
            return '1.0.0'
        
        # Get latest version
        latest = self.registry_index['latest_version']
        if latest is None:
            return '1.0.0'
        
        major, minor, patch = map(int, latest.split('.'))
        
        if version_type == 'major':
            return f"{major + 1}.0.0"
        elif version_type == 'minor':
            return f"{major}.{minor + 1}.0"
        else:  # patch
            return f"{major}.{minor}.{patch + 1}"
    
    def _calculate_model_hash(self, model_info: Dict) -> str:
        """
        Calculate hash for model to detect changes.
        
        Args:
            model_info: Model information dictionary
            
        Returns:
            MD5 hash string
        """
        # Create stable string representation
        model_str = json.dumps(model_info, sort_keys=True, default=str)
        return hashlib.md5(model_str.encode()).hexdigest()
    
    def register_model(self, model_info: Dict, version: Optional[str] = None,
                      description: str = "") -> str:
        """
        Register a new model version.
        
        Args:
            model_info: Dictionary containing:
                - model: Trained model object
                - scaler: Fitted scaler
                - feature_names: List of feature names
                - config: Training configuration
                - performance_metrics: Model performance metrics
                - training_info: Training metadata
            version: Optional specific version string
            description: Human-readable description
            
        Returns:
            Assigned version string
        """
        # Generate version if not provided
        if version is None:
            version = self._generate_version()
        
        # Create version directory
        version_dir = self.registry_path / f"v{version}"
        version_dir.mkdir(exist_ok=True)
        
        # Calculate model hash
        model_hash = self._calculate_model_hash(model_info)
        
        # Prepare version metadata
        version_metadata = {
            'version': version,
            'timestamp': datetime.now().isoformat(),
            'hash': model_hash,
            'description': description,
            'performance_metrics': model_info.get('performance_metrics', {}),
            'training_info': model_info.get('training_info', {}),
            'feature_count': len(model_info.get('feature_names', [])),
            'model_type': type(model_info.get('model')).__name__
        }
        
        # Save model assets
        model_path = version_dir / "model.pkl"
        scaler_path = version_dir / "scaler.pkl"
        metadata_path = version_dir / "metadata.json"
        
        # Save model and scaler
        joblib.dump(model_info['model'], model_path)
        joblib.dump(model_info['scaler'], scaler_path)
        
        # Save comprehensive metadata
        full_metadata = {
            **version_metadata,
            'feature_names': model_info.get('feature_names', []),
            'config': model_info.get('config', {}),
            'hyperparameters': model_info.get('hyperparameters', {})
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(full_metadata, f, indent=2)
        
        # Update registry index
        self.registry_index['versions'][version] = {
            'path': str(version_dir),
            'timestamp': version_metadata['timestamp'],
            'hash': model_hash,
            'description': description,
            'performance': version_metadata['performance_metrics']
        }
        
        self.registry_index['latest_version'] = version
        self.registry_index['metadata']['total_models'] = len(self.registry_index['versions'])
        self.registry_index['metadata']['last_updated'] = datetime.now().isoformat()
        
        self._save_index()
        
        logger.info(f"✅ Model registered as version {version}")
        logger.info(f"   Performance: {version_metadata['performance_metrics']}")
        
        return version
    
    def get_model(self, version: Optional[str] = None) -> Dict:
        """
        Retrieve a model by version (latest if not specified).
        
        Args:
            version: Model version string
            
        Returns:
            Dictionary with model, scaler, and metadata
        """
        if version is None:
            version = self.registry_index['latest_version']
        
        if version not in self.registry_index['versions']:
            raise ValueError(f"Model version {version} not found in registry")
        
        self.registry_index['versions'][version]
        version_dir = self.registry_path / f"v{version}"
        
        # Load model assets
        model_path = version_dir / "model.pkl"
        scaler_path = version_dir / "scaler.pkl"
        metadata_path = version_dir / "metadata.json"
        
        if not all(p.exists() for p in [model_path, scaler_path, metadata_path]):
            raise FileNotFoundError(f"Model files missing for version {version}")
        
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        return {
            'model': model,
            'scaler': scaler,
            'metadata': metadata,
            'version': version,
            'path': str(version_dir)
        }
    
    def list_models(self, detailed: bool = False) -> List[Dict]:
        """
        List all models in registry.
        
        Args:
            detailed: Whether to include full metadata
            
        Returns:
            List of model information dictionaries
        """
        models = []
        
        for version, info in self.registry_index['versions'].items():
            model_info = {
                'version': version,
                'timestamp': info['timestamp'],
                'description': info.get('description', ''),
                'performance': info.get('performance', {})
            }
            
            if detailed:
                try:
                    full_model = self.get_model(version)
                    model_info.update({
                        'feature_count': len(full_model['metadata'].get('feature_names', [])),
                        'model_type': full_model['metadata'].get('model_type', 'unknown'),
                        'training_date': full_model['metadata'].get('training_info', {}).get('date', '')
                    })
                except Exception as e:
                    model_info['error'] = str(e)
            
            models.append(model_info)
        
        # Sort by version (semantic)
        models.sort(key=lambda x: [int(v) for v in x['version'].split('.')], reverse=True)
        
        return models
    
    def compare_models(self, version1: str, version2: str) -> Dict[str, Any]:
        """
        Compare two model versions.
        
        Args:
            version1: First version
            version2: Second version
            
        Returns:
            Comparison results
        """
        model1 = self.get_model(version1)
        model2 = self.get_model(version2)
        
        # ✅ FIX: Explicit type annotation
        comparison: Dict[str, Any] = {
            'versions': [version1, version2],
            'performance_comparison': {},
            'feature_differences': [],
            'training_differences': []
        }
        
        # Compare performance metrics
        metrics1 = model1['metadata'].get('performance_metrics', {})
        metrics2 = model2['metadata'].get('performance_metrics', {})
        
        # ✅ Now this works - mypy knows it's Dict[str, Any]
        for metric in set(list(metrics1.keys()) + list(metrics2.keys())):
            comparison['performance_comparison'][metric] = {
                version1: metrics1.get(metric, 'N/A'),
                version2: metrics2.get(metric, 'N/A'),
                'difference': metrics1.get(metric, 0) - metrics2.get(metric, 0) 
                            if metric in metrics1 and metric in metrics2 else None
            }
        
        # Compare features
        features1 = set(model1['metadata'].get('feature_names', []))
        features2 = set(model2['metadata'].get('feature_names', []))
        
        added = features2 - features1
        removed = features1 - features2
        
        # ✅ Now this works - mypy knows it's List
        if added:
            comparison['feature_differences'].append(f"Added {len(added)} features")
        if removed:
            comparison['feature_differences'].append(f"Removed {len(removed)} features")
        
        # Compare training info
        train1 = model1['metadata'].get('training_info', {})
        train2 = model2['metadata'].get('training_info', {})
        
        for key in set(list(train1.keys()) + list(train2.keys())):
            if train1.get(key) != train2.get(key):
                # ✅ Now this works - mypy knows it's List
                comparison['training_differences'].append(
                    f"{key}: {train1.get(key)} → {train2.get(key)}"
                )
        
        return comparison

    
    def promote_model(self, version: str, environment: str = 'production') -> bool:
        """
        Promote model to specific environment.
        
        Args:
            version: Model version to promote
            environment: Target environment ('staging', 'production')
            
        Returns:
            Success status
        """
        if version not in self.registry_index['versions']:
            logger.error(f"Cannot promote: version {version} not found")
            return False
        
        # Create symlink or copy for environment
        env_dir = self.registry_path / environment
        env_dir.mkdir(exist_ok=True)
        
        version_dir = Path(self.registry_index['versions'][version]['path'])
        
        # Copy model files to environment directory
        for file in ['model.pkl', 'scaler.pkl', 'metadata.json']:
            src = version_dir / file
            dst = env_dir / file
            
            if src.exists():
                shutil.copy2(src, dst)
        
        # Update environment metadata
        env_metadata = {
            'version': version,
            'promoted_at': datetime.now().isoformat(),
            'promoted_by': 'system',  # In production, track user
            'performance': self.registry_index['versions'][version].get('performance', {})
        }
        
        with open(env_dir / "environment.json", 'w') as f:
            json.dump(env_metadata, f, indent=2)
        
        logger.info(f"✅ Model {version} promoted to {environment} environment")
        return True
    
    def rollback_model(self, environment: str = 'production', 
                      target_version: Optional[str] = None) -> bool:
        """
        Rollback environment to previous version.
        
        Args:
            environment: Environment to rollback
            target_version: Specific version to rollback to (defaults to previous)
            
        Returns:
            Success status
        """
        env_dir = self.registry_path / environment
        
        if not env_dir.exists():
            logger.error(f"Environment {environment} not found")
            return False
        
        # Get current version
        env_metadata_path = env_dir / "environment.json"
        if env_metadata_path.exists():
            with open(env_metadata_path, 'r') as f:
                current_env = json.load(f)
            current_version = current_env.get('version')
        else:
            current_version = None
        
        # Determine target version
        if target_version is None:
            # Find previous version
            all_versions = list(self.registry_index['versions'].keys())
            all_versions.sort(key=lambda v: [int(x) for x in v.split('.')])
            
            if current_version in all_versions:
                current_idx = all_versions.index(current_version)
                if current_idx > 0:
                    target_version = all_versions[current_idx - 1]
                else:
                    logger.error(f"No previous version for {current_version}")
                    return False
            else:
                logger.error(f"Current version {current_version} not in registry")
                return False
        
        # Promote target version
        return self.promote_model(target_version, environment)
    
    def cleanup_old_versions(self, keep_last_n: int = 10) -> List[str]:
        """
        Clean up old model versions, keeping only the most recent N.
        
        Args:
            keep_last_n: Number of recent versions to keep
            
        Returns:
            List of removed versions
        """
        all_versions = list(self.registry_index['versions'].keys())
        
        # Sort by version (semantic)
        all_versions.sort(key=lambda v: [int(x) for x in v.split('.')])
        
        if len(all_versions) <= keep_last_n:
            logger.info(f"No cleanup needed. Have {len(all_versions)} versions, keeping {keep_last_n}")
            return []
        
        # Determine which versions to remove
        versions_to_remove = all_versions[:-keep_last_n]
        
        removed = []
        for version in versions_to_remove:
            version_dir = Path(self.registry_index['versions'][version]['path'])
            
            # Remove directory
            if version_dir.exists():
                shutil.rmtree(version_dir)
            
            # Remove from index
            del self.registry_index['versions'][version]
            
            removed.append(version)
            logger.info(f"Removed old version: {version}")
        
        # Update latest version
        if removed and self.registry_index['latest_version'] in removed:
            remaining_versions = list(self.registry_index['versions'].keys())
            if remaining_versions:
                self.registry_index['latest_version'] = remaining_versions[-1]
        
        self.registry_index['metadata']['total_models'] = len(self.registry_index['versions'])
        self._save_index()
        
        logger.info(f"✅ Cleanup completed. Removed {len(removed)} old versions")
        return removed
    
    def get_performance_history(self, metric: str = 'auc') -> Dict[str, Any]:
        """
        Get performance history for a specific metric.
        
        Args:
            metric: Performance metric to track
            
        Returns:
            Performance history dictionary
        """
        # ✅ FIX: Add explicit type annotation
        history: Dict[str, Any] = {
            'metric': metric,
            'timeline': [],
            'best_version': None,
            'best_value': -float('inf')
        }
        
        for version, info in self.registry_index['versions'].items():
            performance = info.get('performance', {})
            metric_value = performance.get(metric)
            
            if metric_value is not None:
                # ✅ Now mypy knows timeline is a List
                history['timeline'].append({
                    'version': version,
                    'timestamp': info['timestamp'],
                    'value': metric_value
                })
                
                # Track best value
                if metric_value > history['best_value']:
                    history['best_value'] = metric_value
                    history['best_version'] = version
        
        # Sort timeline by timestamp
        # ✅ Now mypy knows timeline has .sort()
        history['timeline'].sort(key=lambda x: x['timestamp'])
        
        return history

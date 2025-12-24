# (Paste the entire config_manager.py content here)
"""
Configuration Manager for ChainGuardian AI
==========================================
Responsible for loading, validating, and managing all configuration parameters.
Ensures type safety and provides default values for backward compatibility.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
from typing import Dict, Any, Optional, Union  # Add Union

logger = logging.getLogger(__name__)

class CalibrationMethod(Enum):
    """Supported calibration methods."""
    SIGMOID = "sigmoid"
    ISOTONIC = "isotonic"
    NONE = "none"

class AugmentationStrategy(Enum):
    """Supported data augmentation strategies."""
    MIXUP = "mixup"
    GAUSSIAN = "gaussian"
    SMOTE = "smote"
    NONE = "none"

@dataclass
class HyperparameterConfig:
    """Configuration for hyperparameter tuning."""
    enable_optuna: bool = True
    n_trials: int = 50
    timeout_seconds: int = 3600
    study_name: str = "chainguardian_optimization"
    
    # Search spaces with type hints
    search_spaces: Dict[str, Dict] = field(default_factory=lambda: {
        'xgboost': {
            'n_estimators': [100, 300],
            'max_depth': [3, 8],
            'learning_rate': [0.01, 0.2]
        }
    })
    
    def validate(self):
        """Validate hyperparameter configuration."""
        if self.n_trials < 10:
            logger.warning(f"n_trials={self.n_trials} is low. Consider increasing for better optimization.")
        return True
    
@dataclass
class UncertaintyConfig:
    """Configuration for uncertainty quantification."""
    enable_bootstrap: bool = False
    n_bootstrap_samples: int = 100
    confidence_level: float = 0.95
@dataclass
class EnsembleConfig:
    """Configuration for model ensemble."""
    enabled: bool = True
    voting_method: str = "soft"
    calibration_method: Union[CalibrationMethod, str] = CalibrationMethod.SIGMOID
    initial_weights: Dict[str, float] = field(default_factory=lambda: {
        'xgboost': 0.4,
        'random_forest': 0.3,
        'lightgbm': 0.2,
        'logistic_regression': 0.1
    })
    uncertainty: UncertaintyConfig = field(default_factory=UncertaintyConfig)  # ← ADD THIS
    
    def __post_init__(self):
        """Auto-convert string/dict to CalibrationMethod Enum."""
        # Handle calibration_method conversion
        if isinstance(self.calibration_method, str):
            try:
                self.calibration_method = CalibrationMethod(self.calibration_method.lower())
            except ValueError:
                logger.warning(f"Unknown calibration method '{self.calibration_method}', using SIGMOID")
                self.calibration_method = CalibrationMethod.SIGMOID
        elif isinstance(self.calibration_method, dict):
            value = self.calibration_method.get('value', 'sigmoid')
            try:
                self.calibration_method = CalibrationMethod(value.lower())
            except ValueError:
                logger.warning(f"Unknown calibration method '{value}', using SIGMOID")
                self.calibration_method = CalibrationMethod.SIGMOID
        
        # Handle uncertainty config (if loaded as dict from YAML)
        if isinstance(self.uncertainty, dict):
            self.uncertainty = UncertaintyConfig(**self.uncertainty)
    
    def validate(self) -> bool:
        """Validate ensemble configuration."""
        if sum(self.initial_weights.values()) != 1.0:
            logger.warning("Ensemble weights don't sum to 1.0. Normalizing...")
            total = sum(self.initial_weights.values())
            self.initial_weights = {k: v / total for k, v in self.initial_weights.items()}
        return True


@dataclass
class Config:
    """Main configuration dataclass."""
    hyperparameter_tuning: HyperparameterConfig = field(default_factory=HyperparameterConfig)
    ensemble: EnsembleConfig = field(default_factory=EnsembleConfig)
    weights: Dict = field(default_factory=dict)
    augmentation: Dict = field(default_factory=dict)
    batch_processing: Dict = field(default_factory=dict)
    model_registry: Dict = field(default_factory=dict)
    monitoring: Dict = field(default_factory=dict)
    thresholds: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization validation."""
        self.validate_all()
    
    def validate_all(self):
        """Validate all configuration sections."""
        self.hyperparameter_tuning.validate()
        self.ensemble.validate()
        # Add validation for other sections as needed
        return True
    
    def to_dict(self):
        """Convert configuration to JSON-serializable dictionary."""
        def make_serializable(obj):
            """Recursively convert objects to JSON-serializable format."""
            if isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            elif isinstance(obj, (list, tuple)):
                return [make_serializable(item) for item in obj]
            elif isinstance(obj, dict):
                return {key: make_serializable(value) for key, value in obj.items()}
            elif hasattr(obj, '__dict__'):
                # Handle dataclass or custom objects
                result = {}
                for key, value in obj.__dict__.items():
                    if key.startswith('_'):
                        continue  # Skip private attributes
                    try:
                        result[key] = make_serializable(value)
                    except Exception:
                        result[key] = str(value)  # Fallback to string
                return result
            elif isinstance(obj, Enum):
                return obj.value
            elif hasattr(obj, 'value'):
                # Enum-like objects
                return obj.value
            else:
                # Last resort: convert to string
                return str(obj)
        
        return make_serializable(asdict(self))

    
    def save(self, path: str):
        """Save configuration to YAML file."""
        with open(path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)
        logger.info(f"Configuration saved to {path}")

class ConfigManager:
    """
    Manages loading, validation, and access to configuration.
    Singleton pattern ensures consistent configuration across the system.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize configuration manager."""
        if self._initialized:
            return
        
        # Default configuration paths
        self.default_config_paths = [
            "config/hybrid_config.yaml",
            "../config/hybrid_config.yaml",
            "./hybrid_config.yaml"
        ]
        
        self.config = None
        self._initialized = True
        logger.info("Configuration Manager initialized")
    
    def load_config(self, config_path: Optional[str] = None) -> Config:
        """
        Load configuration from YAML file with fallback logic.
        
        Args:
            config_path: Optional explicit path to config file
            
        Returns:
            Config object
        """
        # Try explicit path first
        if config_path and Path(config_path).exists():
            config_dict = self._load_yaml(config_path)
        else:
            # Try default paths
            config_dict = None
            for path in self.default_config_paths:
                if Path(path).exists():
                    config_dict = self._load_yaml(path)
                    logger.info(f"Loaded configuration from {path}")
                    break
            
            if config_dict is None:
                logger.warning("No configuration file found. Using defaults.")
                config_dict = {}
        
        # Convert nested dictionaries to dataclasses
        self.config = self._dict_to_dataclass(config_dict, Config)
        
        # Set up paths relative to config file location
        if config_path:
            self._setup_paths(config_path)
        
        logger.info("Configuration loaded successfully")
        return self.config
    
    def _load_yaml(self, path: str) -> Dict[str, Any]:
        """Load YAML file with error handling."""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config from {path}: {e}")
            raise
    
    def _dict_to_dataclass(self, data: Dict, dataclass_type) -> Any:
        """Recursively convert dictionary to dataclass."""
        if not isinstance(data, dict):
            return data
        
        # Get field types from dataclass
        field_types = {f.name: f.type for f in dataclass_type.__dataclass_fields__.values()}
        
        # Create kwargs for dataclass
        kwargs = {}
        for field_name, field_type in field_types.items():
            if field_name in data:
                # Handle nested dataclasses
                if hasattr(field_type, '__dataclass_fields__'):
                    kwargs[field_name] = self._dict_to_dataclass(data[field_name], field_type)
                else:
                    kwargs[field_name] = data[field_name]
        
        return dataclass_type(**kwargs)
    
    def _setup_paths(self, config_path: str):
        """Setup relative paths based on config file location."""
        config_dir = Path(config_path).parent
        # os.chdir(config_dir)
        # logger.info(f"Working directory set to: {os.getcwd()}")
    
    def get_config(self) -> Config:
        """Get current configuration."""
        if self.config is None:
            self.load_config()
        return self.config
    
    def update_config(self, updates: Dict[str, Any]):
        """Update configuration dynamically."""
        if self.config is None:
            self.load_config()
        
        # Update configuration (simplified - in production, use deep update)
        for key, value in updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        logger.info("Configuration updated")

# Global configuration access
config_manager = ConfigManager()
def get_config() -> Config:
    """Global accessor for configuration."""
    return config_manager.get_config()
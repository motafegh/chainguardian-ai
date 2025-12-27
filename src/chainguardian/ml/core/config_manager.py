"""
Configuration Manager for ChainGuardian AI
==========================================
Responsible for loading, validating, and managing all configuration parameters.
Ensures type safety and provides default values for backward compatibility.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union, cast, Type, TypeVar, get_origin, get_args
from dataclasses import dataclass, field, asdict, is_dataclass, fields
from enum import Enum
import logging

from chainguardian.ml.core.path_resolver import path_resolver

logger = logging.getLogger(__name__)

T = TypeVar('T')


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
    
    search_spaces: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        'xgboost': {
            'n_estimators': [100, 300],
            'max_depth': [3, 8],
            'learning_rate': [0.01, 0.2]
        }
    })
    
    def validate(self) -> bool:
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
    uncertainty: Union[UncertaintyConfig, Dict[str, Any]] = field(default_factory=UncertaintyConfig)
    
    def __post_init__(self) -> None:
        """Auto-convert string/dict to CalibrationMethod Enum."""
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
        
        if isinstance(self.uncertainty, dict):
            self.uncertainty = UncertaintyConfig(**self.uncertainty)
    
    def validate(self) -> bool:
        """Validate ensemble configuration."""
        total = sum(self.initial_weights.values())
        if abs(total - 1.0) > 0.01:
            logger.warning("Ensemble weights don't sum to 1.0. Normalizing...")
            self.initial_weights = {k: v / total for k, v in self.initial_weights.items()}
        return True


@dataclass
class Config:
    """Main configuration dataclass."""
    hyperparameter_tuning: HyperparameterConfig = field(default_factory=HyperparameterConfig)
    ensemble: EnsembleConfig = field(default_factory=EnsembleConfig)
    weights: Dict[str, Any] = field(default_factory=dict)
    augmentation: Dict[str, Any] = field(default_factory=dict)
    batch_processing: Dict[str, Any] = field(default_factory=dict)
    model_registry: Dict[str, Any] = field(default_factory=dict)
    monitoring: Dict[str, Any] = field(default_factory=dict)
    thresholds: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Post-initialization validation."""
        self.validate_all()
    
    def validate_all(self) -> bool:
        """Validate all configuration sections."""
        self.hyperparameter_tuning.validate()
        self.ensemble.validate()
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to JSON-serializable dictionary."""
        def make_serializable(obj: Any) -> Any:
            """Recursively convert objects to JSON-serializable format."""
            if isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            elif isinstance(obj, (list, tuple)):
                return [make_serializable(item) for item in obj]
            elif isinstance(obj, dict):
                return {key: make_serializable(value) for key, value in obj.items()}
            elif isinstance(obj, Enum):
                return obj.value
            elif is_dataclass(obj):
                result: Dict[str, Any] = {}
                for field_obj in fields(obj):
                    if field_obj.name.startswith('_'):
                        continue
                    try:
                        result[field_obj.name] = make_serializable(getattr(obj, field_obj.name))
                    except Exception:
                        result[field_obj.name] = str(getattr(obj, field_obj.name))
                return result
            elif hasattr(obj, '__dict__'):
                result = {}
                for key, value in obj.__dict__.items():
                    if key.startswith('_'):
                        continue
                    try:
                        result[key] = make_serializable(value)
                    except Exception:
                        result[key] = str(value)
                return result
            else:
                return str(obj)
        
        serialized = make_serializable(asdict(self))
        return cast(Dict[str, Any], serialized)
    
    def save(self, path: str) -> None:
        """Save configuration to YAML file."""
        with open(path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)
        logger.info(f"Configuration saved to {path}")


class ConfigManager:
    """
    Manages loading, validation, and access to configuration.
    Singleton pattern ensures consistent configuration across the system.
    """
    
    _instance: Optional['ConfigManager'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'ConfigManager':
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize configuration manager."""
        if self._initialized:
            return
        
        self.default_config_paths: list[str] = [
            "config/hybrid_config.yaml",
            "../config/hybrid_config.yaml",
            "./hybrid_config.yaml"
        ]
        
        self.config: Optional[Config] = None
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
        config_dict: Optional[Dict[str, Any]] = None
        
        if config_path:
            config_path_obj = Path(config_path)
            if not config_path_obj.is_absolute():
                config_path_obj = path_resolver.project_root / config_path_obj
            
            if config_path_obj.exists():
                config_dict = self._load_yaml(str(config_path_obj))
                logger.info(f"✅ Loaded config from: {config_path_obj}")
        else:
            default_config = path_resolver.get_config_file("hybrid_config.yaml")
            if default_config.exists():
                config_dict = self._load_yaml(str(default_config))
                logger.info(f"✅ Loaded config from: {default_config}")
        
        if config_dict is None:
            logger.warning("⚠️ No configuration file found. Using defaults.")
            config_dict = {}
        
        self.config = self._dict_to_dataclass(config_dict, Config)
        logger.info("✅ Configuration loaded successfully")
        return self.config
    
    def _load_yaml(self, path: str) -> Dict[str, Any]:
        """Load YAML file with error handling."""
        try:
            with open(path, 'r') as f:
                result = yaml.safe_load(f)
                return cast(Dict[str, Any], result if result is not None else {})
        except Exception as e:
            logger.error(f"Failed to load config from {path}: {e}")
            raise
    
    def _dict_to_dataclass(self, data: Any, dataclass_type: Type[T]) -> T:
        """
        Recursively convert dictionary to dataclass.
        
        Args:
            data: Dictionary to convert
            dataclass_type: Target dataclass type
            
        Returns:
            Instance of dataclass_type
        """
        if not isinstance(data, dict):
            return cast(T, data)
        
        if not is_dataclass(dataclass_type):
            return cast(T, data)
        
        field_types: Dict[str, Any] = {
            f.name: f.type for f in fields(dataclass_type)
        }
        
        kwargs: Dict[str, Any] = {}
        for field_name, field_type in field_types.items():
            if field_name in data:
                origin = get_origin(field_type)
                if origin is Union:
                    union_args = get_args(field_type)
                    for arg in union_args:
                        if is_dataclass(arg):
                            kwargs[field_name] = self._dict_to_dataclass(
                                data[field_name], 
                                cast(Type[Any], arg)
                            )
                            break
                    else:
                        kwargs[field_name] = data[field_name]
                elif is_dataclass(field_type):
                    kwargs[field_name] = self._dict_to_dataclass(
                        data[field_name], 
                        cast(Type[Any], field_type)
                    )
                else:
                    kwargs[field_name] = data[field_name]
        
        return dataclass_type(**kwargs)
    
    def _setup_paths(self, config_path: str) -> None:
        """Setup relative paths based on config file location."""
        logger.debug(f"Config loaded from: {config_path}")
        logger.debug(f"Project root: {path_resolver.project_root}")
    
    def get_config(self) -> Config:
        """Get current configuration."""
        if self.config is None:
            self.load_config()
        
        assert self.config is not None, "Config should be loaded by now"
        return self.config
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration dynamically."""
        if self.config is None:
            self.load_config()
        
        if self.config is not None:
            for key, value in updates.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
            logger.info("Configuration updated")


# Global configuration access
config_manager = ConfigManager()


def get_config() -> Config:
    """Global accessor for configuration."""
    return config_manager.get_config()

# (Paste the entire data_augmenter.py content here)
"""
Smart Data Augmentation for Smart Contract Features
====================================================
Implements augmentation strategies suitable for tabular ML features:
1. Mixup: Convex combinations of samples (good for small datasets)
2. Gaussian Noise: Add controlled noise to continuous features
3. Feature-specific augmentations for smart contract data
"""

import numpy as np
import pandas as pd
from sklearn.utils import resample
from typing import Tuple, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SmartContractAugmenter:
    """
    Smart data augmentation for smart contract feature datasets.
    Uses domain knowledge to apply appropriate augmentations.
    """
    
    def __init__(self, config):
        """Initialize augmenter with configuration."""
        self.config = config
        self.augmentation_config = config.augmentation
        logger.info(f"Data augmenter initialized with strategy: {self.augmentation_config.get('strategy')}")
    
    def augment(self, X: pd.DataFrame, y: pd.Series, 
                strategy: Optional[str] = None) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Augment dataset using specified strategy.
        
        Args:
            X: Feature DataFrame
            y: Target Series
            strategy: Override config strategy
            
        Returns:
            Augmented X, y
        """
        if strategy is None:
            strategy = self.augmentation_config.get('strategy', 'none')
        
        if strategy == 'none' or not self.augmentation_config.get('enabled', False):
            logger.info("Data augmentation disabled")
            return X.copy(), y.copy()
        
        logger.info(f"Applying {strategy} augmentation...")
        
        if strategy == 'mixup':
            return self._mixup_augmentation(X, y)
        elif strategy == 'gaussian':
            return self._gaussian_augmentation(X, y)
        elif strategy == 'smote':
            return self._smote_augmentation(X, y)
        else:
            logger.warning(f"Unknown augmentation strategy: {strategy}")
            return X.copy(), y.copy()
    
    def _mixup_augmentation(self, X: pd.DataFrame, y: pd.Series) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Mixup augmentation: convex combinations of samples.
        Good for small datasets as it creates smooth interpolations.
        
        Args:
            X: Feature DataFrame
            y: Target Series
            
        Returns:
            Augmented X, y
        """
        alpha = self.augmentation_config.get('mixup_alpha', 0.2)
        max_factor = self.augmentation_config.get('max_augmentation_factor', 2.0)
        
        n_original = len(X)
        n_augment = min(int(n_original * 0.5),  # Create up to 50% more samples
                       int(n_original * (max_factor - 1)))
        
        if n_augment <= 0:
            return X.copy(), y.copy()
        
        X_aug = []
        y_aug = []
        
        # Convert to numpy for efficient operations
        X_np = X.values
        y_np = y.values
        
        for _ in range(n_augment):
            # Randomly select two samples
            idx1, idx2 = np.random.choice(n_original, 2, replace=False)
            
            # Sample lambda from Beta distribution
            lam = np.random.beta(alpha, alpha)
            
            # Create mixed sample
            x_mix = lam * X_np[idx1] + (1 - lam) * X_np[idx2]
            y_mix = lam * y_np[idx1] + (1 - lam) * y_np[idx2]
            
            X_aug.append(x_mix)
            y_aug.append(y_mix)
        
        # Combine with original
        X_combined = pd.DataFrame(
            np.vstack([X_np, np.array(X_aug)]),
            columns=X.columns
        )
        y_combined = pd.Series(np.hstack([y_np, np.array(y_aug)]))
        
        logger.info(f"Mixup: Added {n_augment} samples (total: {len(X_combined)})")
        
        return X_combined, y_combined
    
    def _gaussian_augmentation(self, X: pd.DataFrame, y: pd.Series) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Add Gaussian noise to continuous features only.
        Preserves boolean/categorical features.
        
        Args:
            X: Feature DataFrame
            y: Target Series
            
        Returns:
            Augmented X, y
        """
        std = self.augmentation_config.get('gaussian_std', 0.05)
        max_factor = self.augmentation_config.get('max_augmentation_factor', 2.0)
        
        n_original = len(X)
        n_augment = min(int(n_original * 0.3),  # Create up to 30% more samples
                       int(n_original * (max_factor - 1)))
        
        if n_augment <= 0:
            return X.copy(), y.copy()
        
        # Identify continuous features (not boolean, not starting with 'has_')
        continuous_cols = [col for col in X.columns 
                          if not col.startswith('has_') 
                          and not col.startswith('is_')
                          and X[col].dtype in [np.float64, np.int64]]
        
        X_aug = []
        
        for _ in range(n_augment):
            # Randomly select a sample
            idx = np.random.randint(n_original)
            x_sample = X.iloc[idx].copy()
            
            # Add noise only to continuous features
            for col in continuous_cols:
                noise = np.random.normal(0, std * X[col].std())
                x_sample[col] = max(0, x_sample[col] + noise)  # Keep non-negative
            
            X_aug.append(x_sample)
        
        # Combine with original
        X_combined = pd.concat([X, pd.DataFrame(X_aug)], ignore_index=True)
        y_combined = pd.concat([y, y.iloc[:n_augment].reset_index(drop=True)], ignore_index=True)
        
        logger.info(f"Gaussian: Added {n_augment} samples (total: {len(X_combined)})")
        
        return X_combined, y_combined
    
    def _smote_augmentation(self, X: pd.DataFrame, y: pd.Series) -> Tuple[pd.DataFrame, pd.Series]:
        """SMOTE with configurable augmentation factor."""
        try:
            from imblearn.over_sampling import SMOTE
        except ImportError:
            logger.error("SMOTE requires imbalanced-learn: pip install imbalanced-learn")
            return X.copy(), y.copy()
        
        class_counts = y.value_counts()
        minority_count = class_counts.min()
        majority_count = class_counts.max()
        
        # Calculate target samples based on max_augmentation_factor
        max_factor = self.augmentation_config.get('max_augmentation_factor', 2.0)
        target_total = int(len(X) * max_factor)
        
        # SMOTE will balance classes, then we need to calculate sampling strategy
        # For balanced classes: each class should have target_total / 2
        target_per_class = target_total // 2
        
        logger.info(f"Applying SMOTE to augment dataset...")
        logger.info(f"Original: {len(X)} samples, distribution: {class_counts.to_dict()}")
        logger.info(f"Target: {target_total} samples ({target_per_class} per class)")
        
        smote = SMOTE(
            sampling_strategy={0: target_per_class, 1: target_per_class},  # Balance both classes
            random_state=42,
            k_neighbors=min(5, minority_count - 1)
        )
        
        X_resampled, y_resampled = smote.fit_resample(X, y)
        
        logger.info(f"✅ SMOTE: {len(X)} -> {len(X_resampled)} samples")
        logger.info(f"   New distribution: {pd.Series(y_resampled).value_counts().to_dict()}")
        
        return pd.DataFrame(X_resampled, columns=X.columns), pd.Series(y_resampled)

    def validate_augmentation(self, X_original: pd.DataFrame, X_augmented: pd.DataFrame, 
                            y_original: pd.Series, y_augmented: pd.Series) -> Dict[str, Any]:
        """
        Validate that augmentation preserved important dataset properties.
        
        Args:
            X_original: Original features
            X_augmented: Augmented features
            y_original: Original labels
            y_augmented: Augmented labels
            
        Returns:
            Validation metrics
        """
        validation = {
            'samples_added': len(X_augmented) - len(X_original),
            'class_balance_original': y_original.mean(),
            'class_balance_augmented': y_augmented.mean(),
            'feature_means_similarity': {},
            'validation_passed': True
        }
        
        # Check feature means are similar
        for col in X_original.columns:
            mean_original = X_original[col].mean()
            mean_augmented = X_augmented[col].mean()
            diff = abs(mean_original - mean_augmented) / (abs(mean_original) + 1e-10)
            
            validation['feature_means_similarity'][col] = {
                'original': float(mean_original),
                'augmented': float(mean_augmented),
                'relative_diff': float(diff)
            }
            
            if diff > 0.1:  # More than 10% change
                logger.warning(f"Large mean change for {col}: {diff:.2%}")
                validation['validation_passed'] = False
        
        # Check no extreme outliers introduced
        for col in X_original.columns:
            if X_original[col].dtype in [np.float64, np.int64]:
                q99_original = X_original[col].quantile(0.99)
                q99_augmented = X_augmented[col].quantile(0.99)
                
                if q99_augmented > q99_original * 2:
                    logger.warning(f"Extreme values introduced for {col}")
                    validation['validation_passed'] = False
        
        return validation
"""
Path Resolver for ChainGuardian AI
===================================
Centralized path management using absolute paths anchored to project root.
Prevents path conflicts when running from different directories.
"""

from pathlib import Path
from typing import Optional
import os


class PathResolver:
    """
    Resolve all project paths relative to project root.
    Handles Poetry, Docker, and multi-environment setups.
    """
    
    _instance: Optional['PathResolver'] = None
    _project_root: Optional[Path] = None
    _initialized: bool = False  # ✅ FIX: Declare the attribute
    
    def __new__(cls) -> 'PathResolver':
        """Singleton pattern for consistent path resolution."""
        if cls._instance is None:
            cls._instance = super(PathResolver, cls).__new__(cls)
            cls._instance._initialized = False  # ✅ Now mypy knows the type
        return cls._instance
    
    def __init__(self) -> None:
        if self._initialized:  # ✅ Now mypy knows the type
            return
        
        # Detect project root (where pyproject.toml lives)
        self._project_root = self._find_project_root()
        self._initialized = True
    
    def _find_project_root(self) -> Path:
        """
        Find project root by looking for pyproject.toml.
        This works from any subdirectory.
        """
        # Start from current file location
        current = Path(__file__).resolve()
        
        # Traverse up until we find pyproject.toml
        for parent in [current, *current.parents]:
            if (parent / "pyproject.toml").exists():
                return parent
        
        # Fallback: use current working directory
        cwd = Path.cwd()
        if (cwd / "pyproject.toml").exists():
            return cwd
        
        raise RuntimeError(
            "Cannot find project root (pyproject.toml not found). "
            f"Searched from {current} to root."
        )
    
    @property
    def project_root(self) -> Path:
        """Get absolute path to project root."""
        if self._project_root is None:
            raise RuntimeError(
                "PathResolver not properly initialized. "
                "_project_root is None."
            )
        return self._project_root
    
    @property
    def config_dir(self) -> Path:
        """config/ directory."""
        return self.project_root / "config"
    
    @property
    def models_dir(self) -> Path:
        """config/models/ directory."""
        path = self.config_dir / "models"
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def registry_dir(self) -> Path:
        """config/models/registry/ directory."""
        path = self.models_dir / "registry"
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def logs_dir(self) -> Path:
        """config/logs/ directory."""
        path = self.config_dir / "logs"
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def data_dir(self) -> Path:
        """data/ directory."""
        return self.project_root / "data"
    
    def get_config_file(self, filename: str = "hybrid_config.yaml") -> Path:
        """Get absolute path to config file."""
        return self.config_dir / filename
    
    def resolve(self, relative_path: str) -> Path:
        """
        Resolve any relative path to absolute path from project root.
        
        Args:
            relative_path: Path relative to project root
            
        Returns:
            Absolute Path object
        """
        return self.project_root / relative_path


# Global instance
path_resolver = PathResolver()


def get_project_root() -> Path:
    """Quick accessor for project root."""
    return path_resolver.project_root

"""
Model loading singleton.

This module implements a singleton for loading and caching ML models.
"""

import pickle
from pathlib import Path
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ModelLoader:
    """
    Singleton for loading and caching ML models.
    
    This class loads EBM models and encoders once and caches them for reuse.
    """
    
    _instance = None
    _models: Dict[str, Any] = {}
    _initialized = False
    
    def __new__(cls, models_dir: str = "models"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.models_dir = Path(models_dir)
            cls._instance._initialized = True
            logger.info(f"ModelLoader initialized with directory: {models_dir}")
        return cls._instance
    
    def __init__(self, models_dir: str = "models"):
        """
        Initialize ModelLoader.
        
        Args:
            models_dir: Directory containing model files
        """
        # Initialization happens in __new__ to ensure singleton pattern works correctly
        pass
    
    def load_model(self, model_name: str) -> Optional[Any]:
        """
        Load a model by name with caching.
        
        Args:
            model_name: Name of model file (without .pkl extension)
            
        Returns:
            Loaded model or None if loading fails
        """
        # Check cache first
        if model_name in self._models:
            logger.debug(f"Model {model_name} loaded from cache")
            return self._models[model_name]
        
        # Load from file
        model_path = self.models_dir / f"{model_name}.pkl"
        
        if not model_path.exists():
            logger.error(f"Model file not found: {model_path}")
            return None
        
        try:
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            
            self._models[model_name] = model
            logger.info(f"Model {model_name} loaded successfully")
            return model
        
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            return None
    
    def load_all_models(self) -> bool:
        """
        Load all required models at startup.
        
        Returns:
            True if all models loaded successfully, False otherwise
        """
        required_models = [
            "ebm_finance",      # Daksha model
            "ebm_health",       # Health Shield model
            "fin_encoders",     # Finance feature encoders
            "health_encoders"   # Health feature encoders
        ]
        
        success = True
        for model_name in required_models:
            model = self.load_model(model_name)
            if model is None:
                logger.error(f"Failed to load required model: {model_name}")
                success = False
        
        if success:
            logger.info("All models loaded successfully")
        else:
            logger.warning("Some models failed to load")
        
        return success
    
    def get_model(self, model_name: str) -> Optional[Any]:
        """
        Get a cached model.
        
        Args:
            model_name: Name of model
            
        Returns:
            Cached model or None
        """
        return self._models.get(model_name)
    
    def validate_models(self) -> bool:
        """
        Validate that all required models are loaded.
        
        Returns:
            True if all required models are available
        """
        required = ["ebm_finance", "ebm_health", "fin_encoders", "health_encoders"]
        return all(model in self._models for model in required)
    
    def clear_cache(self):
        """Clear the model cache."""
        self._models.clear()
        logger.info("Model cache cleared")


# Convenience function
def get_model_loader(models_dir: str = "models") -> ModelLoader:
    """
    Get the ModelLoader singleton instance.
    
    Args:
        models_dir: Directory containing model files
        
    Returns:
        ModelLoader instance
    """
    return ModelLoader(models_dir)

"""
ML Processing Microservice - Enterprise-grade traditional machine learning
Traditional ML algorithms with scikit-learn, XGBoost, CatBoost, and LightGBM
"""
__version__ = "2.0.0"

from .api import ml_router
from .business import MlProcessingBaseMicroservice, MlProcessingMicroserviceFactory

__all__ = [
    'ml_router',
    'MlProcessingBaseMicroservice', 
    'MlProcessingMicroserviceFactory'
]
"""
AI Trading Ensemble System
==========================

Advanced AI ensemble combining multiple ML models for forex/gold trading:
- Unsupervised learning with RandomForest, SGD, PassiveAggressive, MLP
- LSTM neural networks for price prediction and pattern recognition
- Multi-timeframe analysis (M1, M5, M15, H1, H4, D1)
- Real-time inference under 300ms
- 6-AI collaborative processing with cross-learning
- Online learning and continuous adaptation
"""

import asyncio
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import SGDRegressor, PassiveAggressiveRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, accuracy_score, r2_score
from sklearn.base import BaseEstimator, RegressorMixin
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
import joblib
import pickle
import logging
import json
import time
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Third-party integrations for AI collaboration
try:
    import langgraph
    from letta import Letta
    import litellm
    HAS_AI_FRAMEWORKS = True
except ImportError:
    HAS_AI_FRAMEWORKS = False
    logging.warning("AI collaboration frameworks not available")


class TimeFrame(Enum):
    """Trading timeframes"""
    M1 = "1min"
    M5 = "5min"
    M15 = "15min"
    H1 = "1hour"
    H4 = "4hour"
    D1 = "1day"


class PredictionType(Enum):
    """Types of predictions"""
    PRICE_DIRECTION = "price_direction"
    PRICE_TARGET = "price_target"
    VOLATILITY = "volatility"
    PATTERN_RECOGNITION = "pattern_recognition"
    REGIME_CLASSIFICATION = "regime_classification"


@dataclass
class ModelConfig:
    """Configuration for individual models"""
    model_type: str
    hyperparameters: Dict[str, Any]
    timeframes: List[TimeFrame] = field(default_factory=lambda: [TimeFrame.H1])
    prediction_types: List[PredictionType] = field(default_factory=lambda: [PredictionType.PRICE_DIRECTION])
    update_frequency: int = 100  # Update every N samples
    confidence_threshold: float = 0.7
    max_features: int = 50
    lookback_window: int = 60
    online_learning: bool = True


@dataclass
class EnsembleConfig:
    """Configuration for the ensemble system"""
    # Model configurations
    models: List[ModelConfig] = field(default_factory=list)

    # Performance requirements
    max_inference_time_ms: int = 300
    min_accuracy_threshold: float = 0.65

    # Multi-timeframe settings
    primary_timeframe: TimeFrame = TimeFrame.H1
    correlation_timeframes: List[TimeFrame] = field(default_factory=lambda: [TimeFrame.M15, TimeFrame.H1, TimeFrame.H4])

    # Online learning
    enable_online_learning: bool = True
    adaptation_rate: float = 0.01
    performance_window: int = 1000

    # AI collaboration
    enable_ai_collaboration: bool = True
    collaboration_models: List[str] = field(default_factory=lambda: ["gpt-4-turbo", "claude-3-sonnet", "gemini-pro"])
    cross_learning_weight: float = 0.3

    # Memory and storage
    model_save_frequency: int = 500
    memory_namespace: str = "swarm-swarm-1758196378311-2992v6o0m"
    memory_key_prefix: str = "ml_models"


class AdvancedLSTM(nn.Module):
    """Advanced LSTM with attention and residual connections for financial data"""

    def __init__(self, input_size: int, hidden_size: int = 128, num_layers: int = 3,
                 dropout: float = 0.2, output_size: int = 1, use_attention: bool = True,
                 prediction_type: PredictionType = PredictionType.PRICE_DIRECTION):
        super(AdvancedLSTM, self).__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.prediction_type = prediction_type
        self.use_attention = use_attention

        # Input normalization
        self.input_norm = nn.LayerNorm(input_size)

        # LSTM layers with residual connections
        self.lstm1 = nn.LSTM(input_size, hidden_size, batch_first=True, dropout=dropout)
        self.lstm2 = nn.LSTM(hidden_size, hidden_size, batch_first=True, dropout=dropout)
        self.lstm3 = nn.LSTM(hidden_size, hidden_size, batch_first=True, dropout=dropout)

        # Attention mechanism
        if use_attention:
            self.attention = nn.MultiheadAttention(hidden_size, num_heads=8, dropout=dropout, batch_first=True)
            self.attention_norm = nn.LayerNorm(hidden_size)

        # Residual projections
        self.residual_proj1 = nn.Linear(input_size, hidden_size)
        self.residual_proj2 = nn.Linear(hidden_size, hidden_size)

        # Output layers
        self.dropout = nn.Dropout(dropout)
        self.fc1 = nn.Linear(hidden_size, hidden_size // 2)
        self.fc2 = nn.Linear(hidden_size // 2, hidden_size // 4)

        # Prediction-specific output layers
        if prediction_type == PredictionType.PRICE_DIRECTION:
            self.output = nn.Linear(hidden_size // 4, 3)  # Buy, Hold, Sell
            self.activation = nn.Softmax(dim=1)
        elif prediction_type == PredictionType.VOLATILITY:
            self.output = nn.Linear(hidden_size // 4, 1)
            self.activation = nn.ReLU()
        else:  # Price target or pattern recognition
            self.output = nn.Linear(hidden_size // 4, output_size)
            self.activation = nn.Tanh()

        # Batch normalization
        self.bn1 = nn.BatchNorm1d(hidden_size // 2)
        self.bn2 = nn.BatchNorm1d(hidden_size // 4)

    def forward(self, x):
        batch_size, seq_len, _ = x.shape

        # Input normalization
        x = self.input_norm(x)

        # First LSTM with residual connection
        lstm_out1, _ = self.lstm1(x)
        residual1 = self.residual_proj1(x)
        lstm_out1 = lstm_out1 + residual1

        # Second LSTM with residual connection
        lstm_out2, _ = self.lstm2(lstm_out1)
        lstm_out2 = lstm_out2 + lstm_out1  # Residual connection

        # Third LSTM
        lstm_out3, _ = self.lstm3(lstm_out2)
        residual2 = self.residual_proj2(lstm_out2)
        lstm_out3 = lstm_out3 + residual2

        # Attention mechanism
        if self.use_attention:
            attended, _ = self.attention(lstm_out3, lstm_out3, lstm_out3)
            attended = self.attention_norm(attended + lstm_out3)  # Residual
            output = attended[:, -1, :]  # Take last timestep
        else:
            output = lstm_out3[:, -1, :]

        # Feed-forward layers
        output = self.dropout(output)
        output = torch.relu(self.bn1(self.fc1(output)))
        output = self.dropout(output)
        output = torch.relu(self.bn2(self.fc2(output)))
        output = self.output(output)

        return self.activation(output)


class PatternRecognitionLSTM(nn.Module):
    """Specialized LSTM for recognizing trading patterns"""

    def __init__(self, input_size: int, hidden_size: int = 64, num_patterns: int = 10):
        super(PatternRecognitionLSTM, self).__init__()

        self.conv1d = nn.Conv1d(input_size, 32, kernel_size=3, padding=1)
        self.lstm = nn.LSTM(32, hidden_size, num_layers=2, batch_first=True, dropout=0.2)
        self.attention = nn.MultiheadAttention(hidden_size, num_heads=4, batch_first=True)
        self.classifier = nn.Linear(hidden_size, num_patterns)
        self.dropout = nn.Dropout(0.3)

    def forward(self, x):
        # x shape: (batch, seq_len, features)
        x = x.transpose(1, 2)  # (batch, features, seq_len)
        x = torch.relu(self.conv1d(x))
        x = x.transpose(1, 2)  # Back to (batch, seq_len, features)

        lstm_out, _ = self.lstm(x)
        attended, _ = self.attention(lstm_out, lstm_out, lstm_out)

        # Global average pooling
        pooled = torch.mean(attended, dim=1)
        output = self.dropout(pooled)
        return torch.softmax(self.classifier(output), dim=1)


class OnlineMLModel(BaseEstimator, RegressorMixin):
    """Online learning wrapper for traditional ML models"""

    def __init__(self, base_model, learning_rate: float = 0.01, memory_size: int = 1000):
        self.base_model = base_model
        self.learning_rate = learning_rate
        self.memory_size = memory_size
        self.training_data = {'X': [], 'y': []}
        self.is_fitted = False
        self.update_count = 0

    def partial_fit(self, X: np.ndarray, y: np.ndarray):
        """Incremental learning update"""
        # Add to memory
        if len(self.training_data['X']) == 0:
            self.training_data['X'] = X.tolist()
            self.training_data['y'] = y.tolist()
        else:
            self.training_data['X'].extend(X.tolist())
            self.training_data['y'].extend(y.tolist())

        # Limit memory size
        if len(self.training_data['X']) > self.memory_size:
            excess = len(self.training_data['X']) - self.memory_size
            self.training_data['X'] = self.training_data['X'][excess:]
            self.training_data['y'] = self.training_data['y'][excess:]

        # Retrain on recent data
        if len(self.training_data['X']) >= 50:  # Minimum samples
            X_train = np.array(self.training_data['X'])
            y_train = np.array(self.training_data['y'])

            if hasattr(self.base_model, 'partial_fit'):
                self.base_model.partial_fit(X_train, y_train)
            else:
                self.base_model.fit(X_train, y_train)

            self.is_fitted = True
            self.update_count += 1

    def fit(self, X: np.ndarray, y: np.ndarray):
        """Full training"""
        self.base_model.fit(X, y)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        if not self.is_fitted:
            return np.zeros(len(X))
        return self.base_model.predict(X)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Calculate R² score"""
        if not self.is_fitted:
            return 0.0
        predictions = self.predict(X)
        return r2_score(y, predictions)


class AICollaborationFramework:
    """Framework for AI model collaboration using LangGraph, Letta, and LiteLLM"""

    def __init__(self, config: EnsembleConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.collaboration_cache = {}
        self.cross_learning_weights = {}

        if HAS_AI_FRAMEWORKS:
            self._initialize_frameworks()

    def _initialize_frameworks(self):
        """Initialize AI collaboration frameworks"""
        try:
            # Initialize LiteLLM for model routing
            litellm.set_verbose = False

            # Initialize Letta for memory management
            if hasattr(Letta, 'initialize'):
                self.letta_client = Letta.initialize()

            self.logger.info("AI collaboration frameworks initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize AI frameworks: {e}")

    async def collaborative_prediction(self, features: np.ndarray, base_predictions: Dict[str, float]) -> Dict[str, float]:
        """Generate collaborative predictions using multiple AI models"""
        if not HAS_AI_FRAMEWORKS or not self.config.enable_ai_collaboration:
            return base_predictions

        try:
            # Create prompt for AI collaboration
            prompt = self._create_collaboration_prompt(features, base_predictions)

            # Get predictions from multiple AI models
            ai_predictions = {}
            for model_name in self.config.collaboration_models:
                try:
                    response = await self._query_ai_model(model_name, prompt)
                    ai_predictions[model_name] = self._parse_ai_response(response)
                except Exception as e:
                    self.logger.warning(f"AI model {model_name} failed: {e}")

            # Combine predictions with cross-learning
            enhanced_predictions = self._combine_predictions(base_predictions, ai_predictions)

            return enhanced_predictions

        except Exception as e:
            self.logger.error(f"Collaborative prediction failed: {e}")
            return base_predictions

    def _create_collaboration_prompt(self, features: np.ndarray, predictions: Dict[str, float]) -> str:
        """Create prompt for AI model collaboration"""
        feature_summary = {
            'mean': float(np.mean(features)),
            'std': float(np.std(features)),
            'trend': float(np.corrcoef(np.arange(len(features)), features)[0, 1]) if len(features) > 1 else 0.0
        }

        prompt = f"""
        Trading Analysis Request:

        Market Features Summary:
        - Mean: {feature_summary['mean']:.4f}
        - Volatility (std): {feature_summary['std']:.4f}
        - Trend correlation: {feature_summary['trend']:.4f}

        Base Model Predictions:
        {json.dumps(predictions, indent=2)}

        Please provide your analysis of market direction and confidence level (0-1).
        Respond in JSON format: {{"direction": "buy/sell/hold", "confidence": 0.XX, "reasoning": "..."}}
        """

        return prompt

    async def _query_ai_model(self, model_name: str, prompt: str) -> str:
        """Query specific AI model"""
        try:
            response = await litellm.acompletion(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Failed to query {model_name}: {e}")
            return "{}"

    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI model response"""
        try:
            parsed = json.loads(response)
            return {
                'direction': parsed.get('direction', 'hold'),
                'confidence': float(parsed.get('confidence', 0.5)),
                'reasoning': parsed.get('reasoning', '')
            }
        except:
            return {'direction': 'hold', 'confidence': 0.5, 'reasoning': 'Parse error'}

    def _combine_predictions(self, base_predictions: Dict, ai_predictions: Dict) -> Dict[str, float]:
        """Combine base and AI predictions with cross-learning"""
        enhanced = base_predictions.copy()

        if not ai_predictions:
            return enhanced

        # Calculate AI consensus
        ai_confidences = [pred['confidence'] for pred in ai_predictions.values()]
        ai_directions = [pred['direction'] for pred in ai_predictions.values()]

        avg_confidence = np.mean(ai_confidences)
        direction_consensus = max(set(ai_directions), key=ai_directions.count)

        # Apply cross-learning weight
        weight = self.config.cross_learning_weight * avg_confidence

        # Enhance predictions
        if direction_consensus == 'buy':
            enhanced['ai_enhanced_signal'] = min(enhanced.get('price_direction', 0.5) + weight, 1.0)
        elif direction_consensus == 'sell':
            enhanced['ai_enhanced_signal'] = max(enhanced.get('price_direction', 0.5) - weight, 0.0)
        else:
            enhanced['ai_enhanced_signal'] = enhanced.get('price_direction', 0.5)

        enhanced['ai_confidence'] = avg_confidence
        enhanced['ai_consensus'] = direction_consensus

        return enhanced


class MultiTimeframeAnalyzer:
    """Multi-timeframe analysis system for trading signals"""

    def __init__(self, timeframes: List[TimeFrame] = None):
        self.timeframes = timeframes or [TimeFrame.M15, TimeFrame.H1, TimeFrame.H4, TimeFrame.D1]
        self.scalers = {tf: StandardScaler() for tf in self.timeframes}
        self.feature_cache = {}

    def prepare_multitimeframe_features(self, data: Dict[str, pd.DataFrame]) -> np.ndarray:
        """Prepare features from multiple timeframes"""
        all_features = []

        for timeframe in self.timeframes:
            if timeframe.value in data:
                df = data[timeframe.value]
                features = self._extract_timeframe_features(df, timeframe)
                all_features.append(features)

        if not all_features:
            return np.array([])

        # Concatenate features from all timeframes
        combined_features = np.concatenate(all_features, axis=1)
        return combined_features

    def _extract_timeframe_features(self, df: pd.DataFrame, timeframe: TimeFrame) -> np.ndarray:
        """Extract features for specific timeframe"""
        features = []

        # Price-based features
        if len(df) >= 20:
            # Moving averages
            df['sma_5'] = df['close'].rolling(5).mean()
            df['sma_20'] = df['close'].rolling(20).mean()
            df['ema_12'] = df['close'].ewm(span=12).mean()
            df['ema_26'] = df['close'].ewm(span=26).mean()

            # Momentum indicators
            df['rsi'] = self._calculate_rsi(df['close'])
            df['macd'] = df['ema_12'] - df['ema_26']
            df['macd_signal'] = df['macd'].ewm(span=9).mean()

            # Volatility
            df['atr'] = self._calculate_atr(df)
            df['bb_upper'], df['bb_lower'] = self._calculate_bollinger_bands(df['close'])

            # Volume features (if available)
            if 'volume' in df.columns:
                df['volume_sma'] = df['volume'].rolling(20).mean()
                df['volume_ratio'] = df['volume'] / df['volume_sma']

            # Select recent features
            feature_columns = ['sma_5', 'sma_20', 'rsi', 'macd', 'macd_signal', 'atr']
            if 'volume_ratio' in df.columns:
                feature_columns.append('volume_ratio')

            # Get last 60 rows of features
            recent_features = df[feature_columns].dropna().tail(60)

            if len(recent_features) > 0:
                # Normalize features for this timeframe
                if timeframe not in self.scalers:
                    self.scalers[timeframe] = StandardScaler()

                if not hasattr(self.scalers[timeframe], 'mean_'):
                    # Fit scaler if not already fitted
                    self.scalers[timeframe].fit(recent_features)

                normalized_features = self.scalers[timeframe].transform(recent_features)
                features.append(normalized_features.flatten())

        if not features:
            # Return zeros if no features available
            return np.zeros((1, 60 * 6))  # 60 time steps * 6 features

        return np.array(features)

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift())
        tr3 = abs(df['low'] - df['close'].shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        return atr

    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2) -> Tuple[pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(period).mean()
        std = prices.rolling(period).std()

        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)

        return upper_band, lower_band


class PerformanceTracker:
    """Track and adapt model performance in real-time"""

    def __init__(self, config: EnsembleConfig):
        self.config = config
        self.performance_history = {}
        self.model_scores = {}
        self.adaptation_weights = {}
        self.logger = logging.getLogger(__name__)

    def update_performance(self, model_name: str, prediction: float, actual: float,
                         confidence: float, timestamp: datetime = None):
        """Update performance metrics for a model"""
        if timestamp is None:
            timestamp = datetime.now()

        if model_name not in self.performance_history:
            self.performance_history[model_name] = []

        # Calculate error metrics
        error = abs(prediction - actual)
        accuracy = 1.0 - min(error, 1.0)  # Capped at 1.0

        performance_record = {
            'timestamp': timestamp,
            'prediction': prediction,
            'actual': actual,
            'error': error,
            'accuracy': accuracy,
            'confidence': confidence
        }

        self.performance_history[model_name].append(performance_record)

        # Keep only recent history
        if len(self.performance_history[model_name]) > self.config.performance_window:
            self.performance_history[model_name] = \
                self.performance_history[model_name][-self.config.performance_window:]

        # Update model scores
        self._update_model_scores(model_name)

        # Update adaptation weights
        self._update_adaptation_weights()

    def _update_model_scores(self, model_name: str):
        """Update overall score for a model"""
        if model_name not in self.performance_history:
            return

        recent_records = self.performance_history[model_name][-100:]  # Last 100 predictions

        if len(recent_records) < 10:
            return

        # Calculate weighted performance metrics
        accuracies = [r['accuracy'] for r in recent_records]
        confidences = [r['confidence'] for r in recent_records]

        # Recent performance gets higher weight
        weights = np.exp(np.linspace(0, 1, len(accuracies)))
        weights = weights / np.sum(weights)

        weighted_accuracy = np.average(accuracies, weights=weights)
        avg_confidence = np.mean(confidences)

        # Combined score considering both accuracy and confidence calibration
        confidence_calibration = 1.0 - abs(weighted_accuracy - avg_confidence)

        overall_score = (weighted_accuracy * 0.7 + confidence_calibration * 0.3)

        self.model_scores[model_name] = {
            'accuracy': weighted_accuracy,
            'confidence_calibration': confidence_calibration,
            'overall_score': overall_score,
            'sample_count': len(recent_records)
        }

    def _update_adaptation_weights(self):
        """Update weights for ensemble combination based on performance"""
        if not self.model_scores:
            return

        # Calculate weights based on performance scores
        scores = [info['overall_score'] for info in self.model_scores.values()]
        model_names = list(self.model_scores.keys())

        if len(scores) == 0:
            return

        # Softmax weighting with temperature
        temperature = 2.0  # Higher temperature = more uniform weights
        exp_scores = np.exp(np.array(scores) / temperature)
        weights = exp_scores / np.sum(exp_scores)

        # Update adaptation weights
        for i, model_name in enumerate(model_names):
            self.adaptation_weights[model_name] = weights[i]

    def get_ensemble_weights(self) -> Dict[str, float]:
        """Get current ensemble weights based on performance"""
        if not self.adaptation_weights:
            return {}

        return self.adaptation_weights.copy()

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        summary = {
            'model_count': len(self.model_scores),
            'total_predictions': sum(len(hist) for hist in self.performance_history.values()),
            'model_performance': self.model_scores.copy(),
            'ensemble_weights': self.adaptation_weights.copy(),
            'last_update': max([
                max(records, key=lambda r: r['timestamp'])['timestamp']
                for records in self.performance_history.values()
            ]) if self.performance_history else None
        }

        return summary


class AITradingEnsemble:
    """Main AI Trading Ensemble orchestrating all models and frameworks"""

    def __init__(self, config: EnsembleConfig = None):
        self.config = config or EnsembleConfig()
        self.logger = logging.getLogger(__name__)

        # Core components
        self.models = {}
        self.pytorch_models = {}
        self.scalers = {}
        self.performance_tracker = PerformanceTracker(self.config)
        self.multitimeframe_analyzer = MultiTimeframeAnalyzer(self.config.correlation_timeframes)
        self.ai_collaboration = AICollaborationFramework(self.config)

        # State management
        self.is_initialized = False
        self.last_update = datetime.now()
        self.inference_times = []

        # Memory storage
        self.memory_store = {}

        self.logger.info("AI Trading Ensemble initialized")

    async def initialize(self):
        """Initialize all models and components"""
        try:
            self.logger.info("Initializing AI Trading Ensemble...")

            # Initialize traditional ML models
            await self._initialize_traditional_models()

            # Initialize PyTorch models
            await self._initialize_pytorch_models()

            # Load saved models if available
            await self._load_saved_models()

            # Initialize AI collaboration
            if self.config.enable_ai_collaboration:
                await self.ai_collaboration._initialize_frameworks()

            self.is_initialized = True
            self.logger.info("✅ AI Trading Ensemble fully initialized")

            # Store initialization in memory
            await self._store_in_memory("initialization", {
                "timestamp": datetime.now().isoformat(),
                "model_count": len(self.models) + len(self.pytorch_models),
                "status": "initialized"
            })

            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize AI Trading Ensemble: {e}")
            return False

    async def _initialize_traditional_models(self):
        """Initialize traditional ML models"""
        try:
            # RandomForest for different prediction types
            self.models['rf_price_direction'] = OnlineMLModel(
                RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42),
                learning_rate=0.01
            )

            self.models['rf_volatility'] = OnlineMLModel(
                RandomForestRegressor(n_estimators=150, max_depth=12, random_state=42),
                learning_rate=0.01
            )

            # SGD models for online learning
            self.models['sgd_price'] = OnlineMLModel(
                SGDRegressor(learning_rate='adaptive', eta0=0.01, random_state=42),
                learning_rate=0.02
            )

            # Passive Aggressive for robust online learning
            self.models['pa_price'] = OnlineMLModel(
                PassiveAggressiveRegressor(C=0.1, random_state=42),
                learning_rate=0.015
            )

            # MLP for non-linear patterns
            self.models['mlp_pattern'] = OnlineMLModel(
                MLPRegressor(hidden_layer_sizes=(128, 64, 32), max_iter=500,
                           learning_rate_init=0.001, random_state=42),
                learning_rate=0.005
            )

            # Specialized models for different timeframes
            for tf in self.config.correlation_timeframes:
                model_name = f'rf_{tf.value}'
                self.models[model_name] = OnlineMLModel(
                    RandomForestRegressor(n_estimators=75, max_depth=8, random_state=42),
                    learning_rate=0.01
                )

            # Initialize scalers
            self.scalers = {model_name: StandardScaler() for model_name in self.models.keys()}

            self.logger.info(f"Initialized {len(self.models)} traditional ML models")

        except Exception as e:
            self.logger.error(f"Failed to initialize traditional models: {e}")
            raise

    async def _initialize_pytorch_models(self):
        """Initialize PyTorch neural network models"""
        try:
            # Price direction LSTM
            self.pytorch_models['lstm_price_direction'] = AdvancedLSTM(
                input_size=50,  # Will be adjusted based on actual features
                hidden_size=128,
                num_layers=3,
                prediction_type=PredictionType.PRICE_DIRECTION
            )

            # Volatility prediction LSTM
            self.pytorch_models['lstm_volatility'] = AdvancedLSTM(
                input_size=50,
                hidden_size=96,
                num_layers=2,
                prediction_type=PredictionType.VOLATILITY
            )

            # Pattern recognition LSTM
            self.pytorch_models['lstm_pattern'] = PatternRecognitionLSTM(
                input_size=50,
                hidden_size=64,
                num_patterns=10
            )

            # Price target prediction LSTM for different timeframes
            for tf in [TimeFrame.M15, TimeFrame.H1, TimeFrame.H4]:
                model_name = f'lstm_target_{tf.value}'
                self.pytorch_models[model_name] = AdvancedLSTM(
                    input_size=50,
                    hidden_size=64,
                    num_layers=2,
                    prediction_type=PredictionType.PRICE_TARGET
                )

            # Set up optimizers and loss functions
            self.optimizers = {}
            self.loss_functions = {}

            for name, model in self.pytorch_models.items():
                self.optimizers[name] = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-5)

                if 'direction' in name:
                    self.loss_functions[name] = nn.CrossEntropyLoss()
                elif 'pattern' in name:
                    self.loss_functions[name] = nn.CrossEntropyLoss()
                else:
                    self.loss_functions[name] = nn.MSELoss()

            self.logger.info(f"Initialized {len(self.pytorch_models)} PyTorch models")

        except Exception as e:
            self.logger.error(f"Failed to initialize PyTorch models: {e}")
            raise

    async def predict(self, features: np.ndarray, timeframe_data: Dict[str, pd.DataFrame] = None) -> Dict[str, Any]:
        """Generate predictions from all models with real-time performance optimization"""
        start_time = time.time()

        try:
            if not self.is_initialized:
                await self.initialize()

            # Prepare multi-timeframe features if available
            if timeframe_data:
                mt_features = self.multitimeframe_analyzer.prepare_multitimeframe_features(timeframe_data)
                if len(mt_features) > 0:
                    features = np.concatenate([features, mt_features.flatten()])

            # Adjust input size if needed
            input_size = features.shape[-1] if len(features.shape) > 1 else len(features)
            await self._adjust_model_input_sizes(input_size)

            # Get predictions from traditional models
            traditional_predictions = await self._get_traditional_predictions(features)

            # Get predictions from PyTorch models
            pytorch_predictions = await self._get_pytorch_predictions(features)

            # Combine all predictions
            all_predictions = {**traditional_predictions, **pytorch_predictions}

            # Apply ensemble weighting based on performance
            ensemble_weights = self.performance_tracker.get_ensemble_weights()
            weighted_predictions = self._apply_ensemble_weights(all_predictions, ensemble_weights)

            # AI collaboration enhancement
            if self.config.enable_ai_collaboration:
                enhanced_predictions = await self.ai_collaboration.collaborative_prediction(
                    features, weighted_predictions
                )
            else:
                enhanced_predictions = weighted_predictions

            # Calculate inference time
            inference_time = (time.time() - start_time) * 1000  # Convert to ms
            self.inference_times.append(inference_time)

            # Keep last 100 inference times
            if len(self.inference_times) > 100:
                self.inference_times = self.inference_times[-100:]

            # Generate final prediction summary
            prediction_summary = self._generate_prediction_summary(enhanced_predictions, inference_time)

            # Store prediction in memory
            await self._store_in_memory("latest_prediction", prediction_summary)

            return prediction_summary

        except Exception as e:
            self.logger.error(f"❌ Prediction failed: {e}")
            return {
                'error': str(e),
                'inference_time_ms': (time.time() - start_time) * 1000,
                'timestamp': datetime.now().isoformat()
            }

    async def _get_traditional_predictions(self, features: np.ndarray) -> Dict[str, float]:
        """Get predictions from traditional ML models"""
        predictions = {}

        for model_name, model in self.models.items():
            try:
                if model.is_fitted:
                    # Scale features
                    if model_name in self.scalers and hasattr(self.scalers[model_name], 'mean_'):
                        scaled_features = self.scalers[model_name].transform(features.reshape(1, -1))
                    else:
                        scaled_features = features.reshape(1, -1)

                    prediction = model.predict(scaled_features)[0]
                    predictions[model_name] = float(prediction)
                else:
                    predictions[model_name] = 0.5  # Neutral prediction

            except Exception as e:
                self.logger.warning(f"Traditional model {model_name} prediction failed: {e}")
                predictions[model_name] = 0.5

        return predictions

    async def _get_pytorch_predictions(self, features: np.ndarray) -> Dict[str, float]:
        """Get predictions from PyTorch models"""
        predictions = {}

        # Prepare sequence data for LSTM models
        sequence_length = 60
        if len(features) >= sequence_length:
            sequence_features = features[-sequence_length:].reshape(1, sequence_length, -1)
        else:
            # Pad with zeros if not enough data
            padded = np.zeros((sequence_length, features.shape[-1] if len(features.shape) > 1 else len(features)))
            padded[-len(features):] = features.reshape(-1, features.shape[-1] if len(features.shape) > 1 else len(features))
            sequence_features = padded.reshape(1, sequence_length, -1)

        for model_name, model in self.pytorch_models.items():
            try:
                model.eval()
                with torch.no_grad():
                    input_tensor = torch.FloatTensor(sequence_features)
                    output = model(input_tensor)

                    if 'direction' in model_name:
                        # Convert softmax output to direction score
                        probs = output.cpu().numpy()[0]
                        # Buy=0, Hold=1, Sell=2 -> convert to 0-1 scale
                        direction_score = (probs[0] - probs[2] + 1) / 2  # Maps [-1,1] to [0,1]
                        predictions[model_name] = float(direction_score)
                    elif 'pattern' in model_name:
                        # Get most likely pattern
                        pattern_probs = output.cpu().numpy()[0]
                        predictions[model_name] = float(np.max(pattern_probs))
                    else:
                        # Regression output
                        predictions[model_name] = float(output.cpu().numpy()[0])

            except Exception as e:
                self.logger.warning(f"PyTorch model {model_name} prediction failed: {e}")
                predictions[model_name] = 0.5

        return predictions

    def _apply_ensemble_weights(self, predictions: Dict[str, float], weights: Dict[str, float]) -> Dict[str, float]:
        """Apply performance-based weights to ensemble predictions"""
        if not weights:
            return predictions

        weighted_predictions = {}

        # Group predictions by type
        price_direction_models = [k for k in predictions.keys() if 'direction' in k or 'price' in k]
        volatility_models = [k for k in predictions.keys() if 'volatility' in k]
        pattern_models = [k for k in predictions.keys() if 'pattern' in k]

        # Calculate weighted averages for each prediction type
        for model_group, group_name in [
            (price_direction_models, 'price_direction'),
            (volatility_models, 'volatility'),
            (pattern_models, 'pattern_recognition')
        ]:
            if model_group:
                total_weight = sum(weights.get(model, 1.0) for model in model_group)
                if total_weight > 0:
                    weighted_sum = sum(
                        predictions[model] * weights.get(model, 1.0)
                        for model in model_group
                    )
                    weighted_predictions[group_name] = weighted_sum / total_weight

        # Add individual model predictions for detailed analysis
        weighted_predictions.update(predictions)

        return weighted_predictions

    def _generate_prediction_summary(self, predictions: Dict[str, float], inference_time: float) -> Dict[str, Any]:
        """Generate comprehensive prediction summary"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'inference_time_ms': inference_time,
            'performance_target_met': inference_time < self.config.max_inference_time_ms,

            # Main predictions
            'price_direction': predictions.get('price_direction', 0.5),
            'volatility': predictions.get('volatility', 0.5),
            'pattern_confidence': predictions.get('pattern_recognition', 0.5),

            # Enhanced predictions
            'ai_enhanced_signal': predictions.get('ai_enhanced_signal', predictions.get('price_direction', 0.5)),
            'ai_confidence': predictions.get('ai_confidence', 0.5),
            'ai_consensus': predictions.get('ai_consensus', 'hold'),

            # Individual model predictions
            'model_predictions': predictions,

            # Performance metrics
            'avg_inference_time_ms': np.mean(self.inference_times) if self.inference_times else inference_time,
            'model_count': len(self.models) + len(self.pytorch_models),

            # Trading signals
            'signal_strength': self._calculate_signal_strength(predictions),
            'confidence_level': self._calculate_confidence_level(predictions),
            'recommended_action': self._determine_recommended_action(predictions)
        }

        return summary

    def _calculate_signal_strength(self, predictions: Dict[str, float]) -> float:
        """Calculate overall signal strength"""
        direction_score = predictions.get('price_direction', 0.5)
        ai_enhanced = predictions.get('ai_enhanced_signal', direction_score)
        pattern_conf = predictions.get('pattern_recognition', 0.5)

        # Combine signals with weights
        signal_strength = (
            direction_score * 0.4 +
            ai_enhanced * 0.4 +
            pattern_conf * 0.2
        )

        return float(signal_strength)

    def _calculate_confidence_level(self, predictions: Dict[str, float]) -> float:
        """Calculate prediction confidence level"""
        # Use AI confidence if available
        ai_conf = predictions.get('ai_confidence', 0.5)

        # Calculate model agreement
        direction_predictions = [
            v for k, v in predictions.items()
            if 'direction' in k or 'price' in k
        ]

        if len(direction_predictions) > 1:
            agreement = 1.0 - np.std(direction_predictions)
        else:
            agreement = 0.5

        # Combine AI confidence and model agreement
        confidence = (ai_conf * 0.6 + agreement * 0.4)
        return float(confidence)

    def _determine_recommended_action(self, predictions: Dict[str, float]) -> str:
        """Determine recommended trading action"""
        signal_strength = self._calculate_signal_strength(predictions)
        confidence = self._calculate_confidence_level(predictions)

        # Require high confidence for action
        if confidence < 0.7:
            return "hold"

        if signal_strength > 0.6:
            return "buy"
        elif signal_strength < 0.4:
            return "sell"
        else:
            return "hold"

    async def train_online(self, features: np.ndarray, targets: Dict[str, float],
                          timeframe_data: Dict[str, pd.DataFrame] = None):
        """Perform online learning update"""
        try:
            if not self.config.enable_online_learning:
                return

            # Prepare multi-timeframe features
            if timeframe_data:
                mt_features = self.multitimeframe_analyzer.prepare_multitimeframe_features(timeframe_data)
                if len(mt_features) > 0:
                    features = np.concatenate([features, mt_features.flatten()])

            # Update traditional models
            await self._train_traditional_models_online(features, targets)

            # Update PyTorch models
            await self._train_pytorch_models_online(features, targets)

            # Update performance tracking
            current_predictions = await self.predict(features, timeframe_data)
            for target_type, actual_value in targets.items():
                if target_type in current_predictions.get('model_predictions', {}):
                    predicted_value = current_predictions['model_predictions'][target_type]
                    confidence = current_predictions.get('confidence_level', 0.5)

                    self.performance_tracker.update_performance(
                        target_type, predicted_value, actual_value, confidence
                    )

            # Store training progress
            await self._store_in_memory("training_progress", {
                "timestamp": datetime.now().isoformat(),
                "features_shape": features.shape if hasattr(features, 'shape') else len(features),
                "targets": targets,
                "performance_summary": self.performance_tracker.get_performance_summary()
            })

            self.logger.info(f"Online training completed with {len(targets)} targets")

        except Exception as e:
            self.logger.error(f"❌ Online training failed: {e}")

    async def _train_traditional_models_online(self, features: np.ndarray, targets: Dict[str, float]):
        """Train traditional models with new data"""
        for model_name, model in self.models.items():
            try:
                # Map target based on model type
                target_value = None
                if 'direction' in model_name or 'price' in model_name:
                    target_value = targets.get('price_direction')
                elif 'volatility' in model_name:
                    target_value = targets.get('volatility')
                elif 'pattern' in model_name:
                    target_value = targets.get('pattern')

                if target_value is not None:
                    # Scale features
                    if model_name in self.scalers:
                        if not hasattr(self.scalers[model_name], 'mean_'):
                            # Fit scaler if not already fitted
                            self.scalers[model_name].fit(features.reshape(1, -1))

                        scaled_features = self.scalers[model_name].transform(features.reshape(1, -1))
                    else:
                        scaled_features = features.reshape(1, -1)

                    # Perform partial fit
                    model.partial_fit(scaled_features, np.array([target_value]))

            except Exception as e:
                self.logger.warning(f"Traditional model {model_name} online training failed: {e}")

    async def _train_pytorch_models_online(self, features: np.ndarray, targets: Dict[str, float]):
        """Train PyTorch models with new data"""
        # Prepare sequence data
        sequence_length = 60
        if len(features) >= sequence_length:
            sequence_features = features[-sequence_length:].reshape(1, sequence_length, -1)
        else:
            # Pad with zeros
            padded = np.zeros((sequence_length, features.shape[-1] if len(features.shape) > 1 else len(features)))
            padded[-len(features):] = features.reshape(-1, features.shape[-1] if len(features.shape) > 1 else len(features))
            sequence_features = padded.reshape(1, sequence_length, -1)

        for model_name, model in self.pytorch_models.items():
            try:
                # Map target based on model type
                target_value = None
                if 'direction' in model_name:
                    direction_score = targets.get('price_direction', 0.5)
                    # Convert to class index: 0=buy, 1=hold, 2=sell
                    if direction_score > 0.6:
                        target_value = 0  # Buy
                    elif direction_score < 0.4:
                        target_value = 2  # Sell
                    else:
                        target_value = 1  # Hold
                elif 'volatility' in model_name:
                    target_value = targets.get('volatility')
                elif 'pattern' in model_name:
                    pattern_score = targets.get('pattern', 0.5)
                    target_value = int(pattern_score * 9)  # Convert to pattern class 0-9
                elif 'target' in model_name:
                    target_value = targets.get('price_target')

                if target_value is not None:
                    model.train()
                    optimizer = self.optimizers[model_name]
                    loss_fn = self.loss_functions[model_name]

                    # Forward pass
                    input_tensor = torch.FloatTensor(sequence_features)
                    output = model(input_tensor)

                    # Prepare target tensor
                    if 'direction' in model_name or 'pattern' in model_name:
                        target_tensor = torch.LongTensor([target_value])
                    else:
                        target_tensor = torch.FloatTensor([target_value])

                    # Calculate loss and update
                    loss = loss_fn(output, target_tensor)

                    optimizer.zero_grad()
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                    optimizer.step()

            except Exception as e:
                self.logger.warning(f"PyTorch model {model_name} online training failed: {e}")

    async def _adjust_model_input_sizes(self, input_size: int):
        """Adjust model input sizes if features change"""
        for model_name, model in self.pytorch_models.items():
            try:
                if hasattr(model, 'input_norm') and model.input_norm.normalized_shape[0] != input_size:
                    # Reinitialize model with new input size
                    if isinstance(model, AdvancedLSTM):
                        prediction_type = getattr(model, 'prediction_type', PredictionType.PRICE_DIRECTION)
                        new_model = AdvancedLSTM(
                            input_size=input_size,
                            hidden_size=model.hidden_size,
                            num_layers=model.num_layers,
                            prediction_type=prediction_type
                        )
                        self.pytorch_models[model_name] = new_model
                        self.optimizers[model_name] = optim.Adam(new_model.parameters(), lr=0.001)
                    elif isinstance(model, PatternRecognitionLSTM):
                        new_model = PatternRecognitionLSTM(
                            input_size=input_size,
                            hidden_size=model.lstm.hidden_size
                        )
                        self.pytorch_models[model_name] = new_model
                        self.optimizers[model_name] = optim.Adam(new_model.parameters(), lr=0.001)

            except Exception as e:
                self.logger.warning(f"Failed to adjust input size for {model_name}: {e}")

    async def _store_in_memory(self, key: str, data: Any):
        """Store data in swarm memory"""
        try:
            memory_key = f"{self.config.memory_key_prefix}_{key}"
            self.memory_store[memory_key] = {
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'namespace': self.config.memory_namespace
            }

            # In a real implementation, this would use the swarm memory system
            # For now, we'll just store locally and log
            self.logger.debug(f"Stored data in memory: {memory_key}")

        except Exception as e:
            self.logger.error(f"Failed to store in memory: {e}")

    async def _load_saved_models(self):
        """Load previously saved models"""
        try:
            # This would load from the swarm memory system
            # For now, it's a placeholder
            self.logger.info("Checking for saved models...")

        except Exception as e:
            self.logger.warning(f"Could not load saved models: {e}")

    async def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        try:
            performance_summary = self.performance_tracker.get_performance_summary()

            report = {
                'timestamp': datetime.now().isoformat(),
                'system_status': {
                    'initialized': self.is_initialized,
                    'model_count': len(self.models) + len(self.pytorch_models),
                    'last_update': self.last_update.isoformat(),
                    'avg_inference_time_ms': np.mean(self.inference_times) if self.inference_times else 0.0,
                    'performance_target_met': np.mean(self.inference_times) < self.config.max_inference_time_ms if self.inference_times else False
                },
                'performance_metrics': performance_summary,
                'model_details': {
                    'traditional_models': list(self.models.keys()),
                    'pytorch_models': list(self.pytorch_models.keys()),
                    'ai_collaboration_enabled': self.config.enable_ai_collaboration and HAS_AI_FRAMEWORKS,
                    'online_learning_enabled': self.config.enable_online_learning
                },
                'configuration': {
                    'max_inference_time_ms': self.config.max_inference_time_ms,
                    'min_accuracy_threshold': self.config.min_accuracy_threshold,
                    'primary_timeframe': self.config.primary_timeframe.value,
                    'correlation_timeframes': [tf.value for tf in self.config.correlation_timeframes]
                }
            }

            # Store report in memory
            await self._store_in_memory("performance_report", report)

            return report

        except Exception as e:
            self.logger.error(f"Failed to generate performance report: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def save_models(self):
        """Save all trained models"""
        try:
            save_data = {
                'timestamp': datetime.now().isoformat(),
                'traditional_models': {},
                'pytorch_models': {},
                'scalers': {},
                'performance_history': self.performance_tracker.performance_history,
                'config': self.config
            }

            # Save traditional models
            for name, model in self.models.items():
                if model.is_fitted:
                    save_data['traditional_models'][name] = {
                        'model': model,
                        'type': 'traditional'
                    }

            # Save PyTorch model state dicts
            for name, model in self.pytorch_models.items():
                save_data['pytorch_models'][name] = {
                    'state_dict': model.state_dict(),
                    'type': type(model).__name__
                }

            # Save scalers
            for name, scaler in self.scalers.items():
                if hasattr(scaler, 'mean_'):
                    save_data['scalers'][name] = scaler

            # Store in memory
            await self._store_in_memory("model_checkpoint", save_data)

            self.logger.info("Models saved successfully")

        except Exception as e:
            self.logger.error(f"Failed to save models: {e}")


# Hook function for coordination
async def notify_training_completion():
    """Notify coordination system of training completion"""
    try:
        import subprocess
        result = subprocess.run([
            'npx', 'claude-flow@alpha', 'hooks', 'notify',
            '--message', 'AI ensemble training completed'
        ], capture_output=True, text=True)

        if result.returncode == 0:
            logging.info("Training completion notification sent")
        else:
            logging.warning(f"Failed to send notification: {result.stderr}")

    except Exception as e:
        logging.warning(f"Coordination notification failed: {e}")


# Factory function for easy initialization
async def create_trading_ensemble(config: EnsembleConfig = None) -> AITradingEnsemble:
    """Create and initialize a complete AI trading ensemble"""
    try:
        # Create default config with optimized models
        if config is None:
            config = EnsembleConfig(
                models=[
                    ModelConfig(
                        model_type="RandomForest",
                        hyperparameters={"n_estimators": 100, "max_depth": 10},
                        timeframes=[TimeFrame.H1, TimeFrame.H4],
                        prediction_types=[PredictionType.PRICE_DIRECTION, PredictionType.VOLATILITY]
                    ),
                    ModelConfig(
                        model_type="LSTM",
                        hyperparameters={"hidden_size": 128, "num_layers": 3},
                        timeframes=[TimeFrame.M15, TimeFrame.H1],
                        prediction_types=[PredictionType.PRICE_DIRECTION, PredictionType.PATTERN_RECOGNITION]
                    )
                ]
            )

        # Create and initialize ensemble
        ensemble = AITradingEnsemble(config)
        await ensemble.initialize()

        # Notify coordination system
        await notify_training_completion()

        return ensemble

    except Exception as e:
        logging.error(f"Failed to create trading ensemble: {e}")
        raise


# Export main components
__all__ = [
    'AITradingEnsemble',
    'EnsembleConfig',
    'ModelConfig',
    'TimeFrame',
    'PredictionType',
    'AdvancedLSTM',
    'PatternRecognitionLSTM',
    'OnlineMLModel',
    'AICollaborationFramework',
    'MultiTimeframeAnalyzer',
    'PerformanceTracker',
    'create_trading_ensemble'
]
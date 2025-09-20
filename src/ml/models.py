"""
AI Trading System - Model Implementations
=========================================

This module contains implementations of all machine learning models used
in the trading pipeline, including traditional ML models, deep learning
architectures, and ensemble methods.
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import xgboost as xgb
import lightgbm as lgb
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge, Lasso
from sklearn.base import BaseEstimator, RegressorMixin
from typing import Dict, List, Optional, Tuple, Any, Union
import joblib
import warnings
warnings.filterwarnings('ignore')

class TradingDataset(Dataset):
    """PyTorch Dataset for trading data"""

    def __init__(self, features: np.ndarray, targets: np.ndarray, sequence_length: int = 20):
        self.features = torch.FloatTensor(features)
        self.targets = torch.FloatTensor(targets)
        self.sequence_length = sequence_length

    def __len__(self):
        return len(self.features) - self.sequence_length

    def __getitem__(self, idx):
        return (
            self.features[idx:idx + self.sequence_length],
            self.targets[idx + self.sequence_length]
        )

class PositionalEncoding(nn.Module):
    """Positional encoding for Transformer models"""

    def __init__(self, d_model: int, max_len: int = 5000):
        super(PositionalEncoding, self).__init__()

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-np.log(10000.0) / d_model))

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)

        self.register_buffer('pe', pe)

    def forward(self, x):
        return x + self.pe[:x.size(0), :]

class TradingLSTM(nn.Module):
    """LSTM model with attention mechanism for trading prediction"""

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.2,
        output_size: int = 1,
        use_attention: bool = True
    ):
        super(TradingLSTM, self).__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.use_attention = use_attention

        # LSTM layers
        self.lstm = nn.LSTM(
            input_size, hidden_size, num_layers,
            batch_first=True, dropout=dropout, bidirectional=False
        )

        # Attention mechanism
        if use_attention:
            self.attention = nn.MultiheadAttention(hidden_size, num_heads=8, dropout=dropout)

        # Output layers
        self.dropout = nn.Dropout(dropout)
        self.fc1 = nn.Linear(hidden_size, hidden_size // 2)
        self.fc2 = nn.Linear(hidden_size // 2, output_size)
        self.batch_norm = nn.BatchNorm1d(hidden_size // 2)

    def forward(self, x):
        # LSTM forward pass
        lstm_out, (hidden, cell) = self.lstm(x)

        if self.use_attention:
            # Apply attention
            lstm_out = lstm_out.transpose(0, 1)  # (seq_len, batch, hidden_size)
            attended, _ = self.attention(lstm_out, lstm_out, lstm_out)
            attended = attended.transpose(0, 1)  # (batch, seq_len, hidden_size)
            output = attended[:, -1, :]  # Take last time step
        else:
            output = lstm_out[:, -1, :]  # Take last time step

        # Final layers
        output = self.dropout(output)
        output = F.relu(self.batch_norm(self.fc1(output)))
        output = self.fc2(output)

        return output

class TradingTransformer(nn.Module):
    """Transformer model for trading prediction"""

    def __init__(
        self,
        input_size: int,
        d_model: int = 256,
        nhead: int = 8,
        num_layers: int = 6,
        dim_feedforward: int = 1024,
        dropout: float = 0.1,
        output_size: int = 1
    ):
        super(TradingTransformer, self).__init__()

        self.d_model = d_model
        self.input_projection = nn.Linear(input_size, d_model)
        self.positional_encoding = PositionalEncoding(d_model)

        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model, nhead, dim_feedforward, dropout, activation='gelu'
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers)

        # Output layers
        self.layer_norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, output_size)
        )

    def forward(self, x):
        # Input projection
        x = self.input_projection(x) * np.sqrt(self.d_model)
        x = self.positional_encoding(x)

        # Transformer encoding
        x = x.transpose(0, 1)  # (seq_len, batch, d_model)
        encoded = self.transformer_encoder(x)
        encoded = encoded.transpose(0, 1)  # (batch, seq_len, d_model)

        # Global average pooling or take last token
        output = self.layer_norm(encoded[:, -1, :])  # Take last time step
        output = self.dropout(output)
        output = self.classifier(output)

        return output

class TradingCNN(nn.Module):
    """CNN model for pattern recognition in trading data"""

    def __init__(
        self,
        input_channels: int,
        sequence_length: int,
        num_filters: List[int] = [64, 128, 256],
        kernel_sizes: List[int] = [3, 5, 7],
        dropout: float = 0.2,
        output_size: int = 1
    ):
        super(TradingCNN, self).__init__()

        self.conv_layers = nn.ModuleList()
        self.pool_layers = nn.ModuleList()

        # Convolutional layers
        in_channels = input_channels
        for i, (num_filters_i, kernel_size) in enumerate(zip(num_filters, kernel_sizes)):
            self.conv_layers.append(
                nn.Conv1d(in_channels, num_filters_i, kernel_size, padding=kernel_size//2)
            )
            self.pool_layers.append(nn.MaxPool1d(2))
            in_channels = num_filters_i

        # Calculate output size after convolutions
        self.adaptive_pool = nn.AdaptiveAvgPool1d(1)

        # Fully connected layers
        self.dropout = nn.Dropout(dropout)
        self.fc1 = nn.Linear(num_filters[-1], num_filters[-1] // 2)
        self.fc2 = nn.Linear(num_filters[-1] // 2, output_size)
        self.batch_norm = nn.BatchNorm1d(num_filters[-1] // 2)

    def forward(self, x):
        # Transpose for Conv1d: (batch, sequence, features) -> (batch, features, sequence)
        x = x.transpose(1, 2)

        # Convolutional layers
        for conv, pool in zip(self.conv_layers, self.pool_layers):
            x = F.relu(conv(x))
            x = pool(x)

        # Global average pooling
        x = self.adaptive_pool(x)
        x = x.view(x.size(0), -1)

        # Fully connected layers
        x = self.dropout(x)
        x = F.relu(self.batch_norm(self.fc1(x)))
        x = self.fc2(x)

        return x

class TradingGAN(nn.Module):
    """Generative Adversarial Network for data augmentation"""

    def __init__(self, input_size: int, hidden_size: int = 128, noise_dim: int = 100):
        super(TradingGAN, self).__init__()

        # Generator
        self.generator = nn.Sequential(
            nn.Linear(noise_dim, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size * 2),
            nn.ReLU(),
            nn.Linear(hidden_size * 2, input_size),
            nn.Tanh()
        )

        # Discriminator
        self.discriminator = nn.Sequential(
            nn.Linear(input_size, hidden_size * 2),
            nn.LeakyReLU(0.2),
            nn.Dropout(0.3),
            nn.Linear(hidden_size * 2, hidden_size),
            nn.LeakyReLU(0.2),
            nn.Dropout(0.3),
            nn.Linear(hidden_size, 1),
            nn.Sigmoid()
        )

        self.noise_dim = noise_dim

    def generate(self, batch_size: int):
        noise = torch.randn(batch_size, self.noise_dim)
        return self.generator(noise)

    def discriminate(self, x):
        return self.discriminator(x)

class MetaLearner(nn.Module):
    """Meta-learning model to combine predictions from multiple base models"""

    def __init__(
        self,
        num_base_models: int,
        meta_features_size: int = 0,
        hidden_size: int = 64,
        dropout: float = 0.2
    ):
        super(MetaLearner, self).__init__()

        input_size = num_base_models + meta_features_size

        self.meta_network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, 1)
        )

        # Attention weights for base models
        self.attention = nn.Linear(num_base_models, num_base_models)

    def forward(self, base_predictions: torch.Tensor, meta_features: torch.Tensor = None):
        # Apply attention to base predictions
        attention_weights = F.softmax(self.attention(base_predictions), dim=1)
        weighted_predictions = base_predictions * attention_weights

        # Combine with meta features if available
        if meta_features is not None:
            combined = torch.cat([weighted_predictions, meta_features], dim=1)
        else:
            combined = weighted_predictions

        return self.meta_network(combined)

class TradingModelWrapper:
    """Base wrapper class for all trading models"""

    def __init__(self, model_type: str, config: Dict[str, Any]):
        self.model_type = model_type
        self.config = config
        self.model = None
        self.is_trained = False
        self.feature_names = None

    def fit(self, X: np.ndarray, y: np.ndarray, X_val: np.ndarray = None, y_val: np.ndarray = None):
        """Fit the model to training data"""
        raise NotImplementedError

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        raise NotImplementedError

    def save(self, filepath: str):
        """Save the trained model"""
        raise NotImplementedError

    def load(self, filepath: str):
        """Load a trained model"""
        raise NotImplementedError

class XGBoostWrapper(TradingModelWrapper):
    """XGBoost model wrapper"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("xgboost", config)

    def fit(self, X: np.ndarray, y: np.ndarray, X_val: np.ndarray = None, y_val: np.ndarray = None):
        eval_set = [(X_val, y_val)] if X_val is not None and y_val is not None else None

        self.model = xgb.XGBRegressor(**self.config)
        self.model.fit(
            X, y,
            eval_set=eval_set,
            verbose=False
        )
        self.is_trained = True

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        return self.model.predict(X)

    def get_feature_importance(self) -> Dict[str, float]:
        if self.model and self.feature_names:
            importance = self.model.feature_importances_
            return dict(zip(self.feature_names, importance))
        return {}

    def save(self, filepath: str):
        if self.model:
            self.model.save_model(filepath)

    def load(self, filepath: str):
        self.model = xgb.XGBRegressor()
        self.model.load_model(filepath)
        self.is_trained = True

class LightGBMWrapper(TradingModelWrapper):
    """LightGBM model wrapper"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("lightgbm", config)

    def fit(self, X: np.ndarray, y: np.ndarray, X_val: np.ndarray = None, y_val: np.ndarray = None):
        eval_set = [(X_val, y_val)] if X_val is not None and y_val is not None else None

        self.model = lgb.LGBMRegressor(**self.config)
        self.model.fit(
            X, y,
            eval_set=eval_set,
            verbose=False
        )
        self.is_trained = True

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        return self.model.predict(X)

    def save(self, filepath: str):
        if self.model:
            joblib.dump(self.model, filepath)

    def load(self, filepath: str):
        self.model = joblib.load(filepath)
        self.is_trained = True

class RandomForestWrapper(TradingModelWrapper):
    """Random Forest model wrapper"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("random_forest", config)

    def fit(self, X: np.ndarray, y: np.ndarray, X_val: np.ndarray = None, y_val: np.ndarray = None):
        self.model = RandomForestRegressor(**self.config)
        self.model.fit(X, y)
        self.is_trained = True

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        return self.model.predict(X)

    def save(self, filepath: str):
        if self.model:
            joblib.dump(self.model, filepath)

    def load(self, filepath: str):
        self.model = joblib.load(filepath)
        self.is_trained = True

class PyTorchModelWrapper(TradingModelWrapper):
    """Base wrapper for PyTorch models"""

    def __init__(self, model_type: str, config: Dict[str, Any]):
        super().__init__(model_type, config)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.optimizer = None
        self.scheduler = None

    def _create_model(self, input_size: int):
        """Create the PyTorch model - to be implemented by subclasses"""
        raise NotImplementedError

    def fit(self, X: np.ndarray, y: np.ndarray, X_val: np.ndarray = None, y_val: np.ndarray = None):
        input_size = X.shape[-1]
        sequence_length = self.config.get('sequence_length', 20)

        # Create model
        self.model = self._create_model(input_size)
        self.model.to(self.device)

        # Create datasets
        train_dataset = TradingDataset(X, y, sequence_length)
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.get('batch_size', 32),
            shuffle=True
        )

        val_loader = None
        if X_val is not None and y_val is not None:
            val_dataset = TradingDataset(X_val, y_val, sequence_length)
            val_loader = DataLoader(val_dataset, batch_size=self.config.get('batch_size', 32))

        # Setup optimizer and scheduler
        self.optimizer = torch.optim.Adam(
            self.model.parameters(),
            lr=self.config.get('learning_rate', 0.001),
            weight_decay=self.config.get('weight_decay', 1e-5)
        )
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='min', patience=10, factor=0.5
        )

        # Training loop
        self._train_loop(train_loader, val_loader)
        self.is_trained = True

    def _train_loop(self, train_loader: DataLoader, val_loader: DataLoader = None):
        """Training loop for PyTorch models"""
        epochs = self.config.get('epochs', 100)
        criterion = nn.MSELoss()
        best_val_loss = float('inf')
        patience = self.config.get('early_stopping_patience', 20)
        patience_counter = 0

        for epoch in range(epochs):
            # Training
            self.model.train()
            train_loss = 0.0
            for batch_X, batch_y in train_loader:
                batch_X, batch_y = batch_X.to(self.device), batch_y.to(self.device)

                self.optimizer.zero_grad()
                outputs = self.model(batch_X).squeeze()
                loss = criterion(outputs, batch_y)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                self.optimizer.step()

                train_loss += loss.item()

            # Validation
            if val_loader:
                self.model.eval()
                val_loss = 0.0
                with torch.no_grad():
                    for batch_X, batch_y in val_loader:
                        batch_X, batch_y = batch_X.to(self.device), batch_y.to(self.device)
                        outputs = self.model(batch_X).squeeze()
                        loss = criterion(outputs, batch_y)
                        val_loss += loss.item()

                val_loss /= len(val_loader)
                self.scheduler.step(val_loss)

                # Early stopping
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                else:
                    patience_counter += 1
                    if patience_counter >= patience:
                        print(f"Early stopping at epoch {epoch}")
                        break

            if epoch % 10 == 0:
                print(f"Epoch {epoch}, Train Loss: {train_loss/len(train_loader):.6f}")
                if val_loader:
                    print(f"Val Loss: {val_loss:.6f}")

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")

        sequence_length = self.config.get('sequence_length', 20)
        dataset = TradingDataset(X, np.zeros(len(X)), sequence_length)
        dataloader = DataLoader(dataset, batch_size=self.config.get('batch_size', 32))

        self.model.eval()
        predictions = []

        with torch.no_grad():
            for batch_X, _ in dataloader:
                batch_X = batch_X.to(self.device)
                outputs = self.model(batch_X)
                predictions.extend(outputs.cpu().numpy())

        return np.array(predictions)

    def save(self, filepath: str):
        if self.model:
            torch.save({
                'model_state_dict': self.model.state_dict(),
                'config': self.config
            }, filepath)

    def load(self, filepath: str):
        checkpoint = torch.load(filepath, map_location=self.device)
        self.config = checkpoint['config']
        input_size = self.config.get('input_size')
        self.model = self._create_model(input_size)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.to(self.device)
        self.is_trained = True

class LSTMWrapper(PyTorchModelWrapper):
    """LSTM model wrapper"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("lstm", config)

    def _create_model(self, input_size: int):
        return TradingLSTM(
            input_size=input_size,
            hidden_size=self.config.get('hidden_size', 128),
            num_layers=self.config.get('num_layers', 2),
            dropout=self.config.get('dropout', 0.2),
            use_attention=self.config.get('use_attention', True)
        )

class TransformerWrapper(PyTorchModelWrapper):
    """Transformer model wrapper"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("transformer", config)

    def _create_model(self, input_size: int):
        return TradingTransformer(
            input_size=input_size,
            d_model=self.config.get('d_model', 256),
            nhead=self.config.get('nhead', 8),
            num_layers=self.config.get('num_layers', 6),
            dim_feedforward=self.config.get('dim_feedforward', 1024),
            dropout=self.config.get('dropout', 0.1)
        )

class CNNWrapper(PyTorchModelWrapper):
    """CNN model wrapper"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("cnn", config)

    def _create_model(self, input_size: int):
        return TradingCNN(
            input_channels=input_size,
            sequence_length=self.config.get('sequence_length', 60),
            num_filters=self.config.get('num_filters', [64, 128, 256]),
            kernel_sizes=self.config.get('kernel_sizes', [3, 5, 7]),
            dropout=self.config.get('dropout', 0.2)
        )

class EnsembleModel:
    """Ensemble model that combines multiple base models"""

    def __init__(self, base_models: List[TradingModelWrapper], meta_learner: MetaLearner = None):
        self.base_models = base_models
        self.meta_learner = meta_learner
        self.weights = None
        self.is_trained = False

    def fit(self, X: np.ndarray, y: np.ndarray, X_val: np.ndarray = None, y_val: np.ndarray = None):
        """Train all base models and optionally the meta-learner"""

        # Train base models
        for model in self.base_models:
            print(f"Training {model.model_type}...")
            model.fit(X, y, X_val, y_val)

        # Train meta-learner if provided
        if self.meta_learner is not None:
            # Get base model predictions for meta-learning
            base_predictions = []
            for model in self.base_models:
                pred = model.predict(X_val if X_val is not None else X)
                base_predictions.append(pred)

            base_predictions = np.column_stack(base_predictions)
            base_predictions_tensor = torch.FloatTensor(base_predictions)
            targets_tensor = torch.FloatTensor(y_val if y_val is not None else y)

            # Train meta-learner
            optimizer = torch.optim.Adam(self.meta_learner.parameters(), lr=0.001)
            criterion = nn.MSELoss()

            for epoch in range(100):
                optimizer.zero_grad()
                meta_pred = self.meta_learner(base_predictions_tensor)
                loss = criterion(meta_pred.squeeze(), targets_tensor)
                loss.backward()
                optimizer.step()

        else:
            # Simple averaging or learned weights
            if X_val is not None and y_val is not None:
                self._learn_ensemble_weights(X_val, y_val)
            else:
                # Equal weights
                self.weights = np.ones(len(self.base_models)) / len(self.base_models)

        self.is_trained = True

    def _learn_ensemble_weights(self, X_val: np.ndarray, y_val: np.ndarray):
        """Learn optimal ensemble weights using validation data"""
        from scipy.optimize import minimize

        # Get base model predictions
        base_predictions = []
        for model in self.base_models:
            pred = model.predict(X_val)
            base_predictions.append(pred)

        base_predictions = np.column_stack(base_predictions)

        def objective(weights):
            weights = weights / np.sum(weights)  # Normalize
            ensemble_pred = np.dot(base_predictions, weights)
            return np.mean((ensemble_pred - y_val) ** 2)

        # Optimize weights
        initial_weights = np.ones(len(self.base_models)) / len(self.base_models)
        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
        bounds = [(0, 1) for _ in range(len(self.base_models))]

        result = minimize(objective, initial_weights, constraints=constraints, bounds=bounds)
        self.weights = result.x

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make ensemble predictions"""
        if not self.is_trained:
            raise ValueError("Ensemble must be trained before prediction")

        if self.meta_learner is not None:
            # Use meta-learner
            base_predictions = []
            for model in self.base_models:
                pred = model.predict(X)
                base_predictions.append(pred)

            base_predictions = np.column_stack(base_predictions)
            base_predictions_tensor = torch.FloatTensor(base_predictions)

            with torch.no_grad():
                ensemble_pred = self.meta_learner(base_predictions_tensor)

            return ensemble_pred.numpy().squeeze()

        else:
            # Weighted average
            predictions = []
            for model in self.base_models:
                pred = model.predict(X)
                predictions.append(pred)

            predictions = np.column_stack(predictions)
            return np.dot(predictions, self.weights)

    def save(self, directory: str):
        """Save all models in the ensemble"""
        import os
        os.makedirs(directory, exist_ok=True)

        # Save base models
        for i, model in enumerate(self.base_models):
            model.save(os.path.join(directory, f"base_model_{i}_{model.model_type}"))

        # Save meta-learner
        if self.meta_learner is not None:
            torch.save(self.meta_learner.state_dict(), os.path.join(directory, "meta_learner.pth"))

        # Save weights
        if self.weights is not None:
            np.save(os.path.join(directory, "ensemble_weights.npy"), self.weights)

def create_model(model_type: str, config: Dict[str, Any]) -> TradingModelWrapper:
    """Factory function to create models"""

    if model_type == "xgboost":
        return XGBoostWrapper(config)
    elif model_type == "lightgbm":
        return LightGBMWrapper(config)
    elif model_type == "random_forest":
        return RandomForestWrapper(config)
    elif model_type == "lstm":
        return LSTMWrapper(config)
    elif model_type == "transformer":
        return TransformerWrapper(config)
    elif model_type == "cnn":
        return CNNWrapper(config)
    else:
        raise ValueError(f"Unknown model type: {model_type}")

def create_ensemble_from_config(model_configs: List[Dict[str, Any]], use_meta_learner: bool = True) -> EnsembleModel:
    """Create ensemble model from configuration"""

    base_models = []
    for config in model_configs:
        if config.get('enabled', True):
            model = create_model(config['model_type'], config['parameters'])
            base_models.append(model)

    meta_learner = None
    if use_meta_learner and len(base_models) > 1:
        meta_learner = MetaLearner(num_base_models=len(base_models))

    return EnsembleModel(base_models, meta_learner)
# Deep Learning Microservice

Enterprise-grade deep learning microservice for advanced trading analytics with PyTorch, TensorFlow, and Transformers integration.

## Features

### Neural Network Architectures
- **CNN**: Convolutional Neural Networks for pattern recognition
- **RNN/LSTM/GRU**: Sequential models for time series forecasting
- **Transformers**: Attention-based models for complex patterns
- **Autoencoders**: Dimensionality reduction and anomaly detection
- **GANs**: Generative models for data synthesis

### Core Capabilities
- **Model Training**: Distributed training with GPU acceleration
- **Fine-tuning**: Pre-trained model adaptation with LoRA and full fine-tuning
- **Inference Engine**: Real-time and batch inference with optimization
- **Model Optimization**: Quantization, pruning, and knowledge distillation
- **Multi-modal**: Support for text, image, and time series data

### Enterprise Infrastructure
- **GPU Management**: CUDA optimization and memory management
- **Centralized Logging**: Structured logging with DL-specific context
- **Performance Tracking**: Comprehensive metrics and GPU monitoring
- **Error Handling**: DL-specific error classification and recovery
- **Event Publishing**: DL lifecycle event notifications
- **Health Monitoring**: Model, GPU, and system health checks

## Quick Start

### Docker Deployment
```bash
# Build and run the deep learning service
docker build -t neliti-deep-learning .
docker run --gpus all -p 8005:8005 neliti-deep-learning
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python main.py
```

## API Endpoints

### Model Training
- `POST /api/v1/deep-learning/train` - Train a new neural network
- `GET /api/v1/deep-learning/models` - List trained models
- `GET /api/v1/deep-learning/models/{model_id}` - Get model details

### Fine-tuning
- `POST /api/v1/deep-learning/fine-tune` - Fine-tune pre-trained models
- `GET /api/v1/deep-learning/fine-tuning-jobs` - List fine-tuning jobs

### Inference
- `POST /api/v1/deep-learning/inference` - Real-time inference
- `POST /api/v1/deep-learning/batch-inference` - Batch inference

### Monitoring
- `GET /api/v1/deep-learning/health` - Service health check
- `GET /api/v1/deep-learning/metrics` - Performance and GPU metrics
- `GET /api/v1/deep-learning/frameworks` - Available frameworks

## Configuration

### Environment Variables
```bash
DEEP_LEARNING_PORT=8005
DEEP_LEARNING_DEBUG=false
MICROSERVICE_ENVIRONMENT=production
MAX_CONCURRENT_TRAININGS=2
GPU_MEMORY_FRACTION=0.8
MIXED_PRECISION=true
HEALTH_CHECK_INTERVAL=30
```

### Storage Paths
- Models: `/app/models/`
- Checkpoints: `/app/checkpoints/`
- TensorBoard Logs: `/app/tensorboard/`
- Data Cache: `/app/data/`

## Supported Frameworks

### Deep Learning Frameworks
- **PyTorch**: Primary framework for neural network development
- **TensorFlow**: Alternative framework with Keras integration
- **Lightning**: High-level PyTorch wrapper for scalable training
- **Transformers**: Hugging Face library for NLP models

### Model Types
- **Computer Vision**: ResNet, EfficientNet, Vision Transformers
- **NLP**: BERT, GPT, T5, RoBERTa
- **Time Series**: LSTM, GRU, Temporal Convolutional Networks
- **Generative**: VAE, GAN, Diffusion Models

## GPU Support

### CUDA Optimization
- **Memory Management**: Automatic GPU memory optimization
- **Mixed Precision**: FP16 training for faster convergence
- **Distributed Training**: Multi-GPU and multi-node support
- **Dynamic Batching**: Adaptive batch sizing based on GPU memory

### GPU Monitoring
- **Utilization**: Real-time GPU usage tracking
- **Memory**: GPU memory allocation and peak usage
- **Temperature**: GPU thermal monitoring
- **Performance**: Training throughput and efficiency metrics

## Architecture

The Deep Learning microservice follows the BASE + CORE infrastructure pattern:

- **BASE**: Foundational infrastructure (logging, config, performance)
- **CORE**: DL-specific components (neural networks, GPU management)
- **API**: RESTful endpoints for DL operations
- **Business Logic**: Neural network architectures and training pipelines

## Performance

### Training Performance
- **GPU Acceleration**: 10-100x speedup over CPU training
- **Mixed Precision**: 1.5-2x training speed improvement
- **Distributed Training**: Linear scaling across multiple GPUs
- **Checkpointing**: Automatic model checkpointing and resumption

### Inference Performance
- **Real-time**: Sub-100ms inference for most models
- **Batch Processing**: High-throughput batch inference
- **Model Optimization**: ONNX conversion and TensorRT optimization
- **Caching**: Intelligent model and result caching

## Integration

This microservice integrates with:
- **Database Service**: Model metadata and training data
- **API Gateway**: Centralized routing and authentication
- **Trading Engine**: Advanced pattern recognition and forecasting
- **ML Processing Service**: Hybrid ML/DL ensemble models

## Advanced Features

### Model Optimization
- **Quantization**: INT8 and FP16 model compression
- **Pruning**: Structured and unstructured model pruning
- **Knowledge Distillation**: Teacher-student model compression
- **ONNX Export**: Cross-framework model deployment

### Fine-tuning Techniques
- **LoRA**: Low-Rank Adaptation for efficient fine-tuning
- **QLoRA**: Quantized LoRA for memory-efficient training
- **Full Fine-tuning**: Complete model parameter updates
- **Adapter Layers**: Modular fine-tuning approaches

## Monitoring

- **Health Checks**: Comprehensive system, GPU, and model health
- **Metrics**: Training loss, validation metrics, GPU utilization
- **Logging**: Structured logs with DL operation context
- **Events**: DL lifecycle events for monitoring and alerting
- **TensorBoard**: Visual training progress and model analysis

## Version

**Version**: 2.0.0  
**Framework**: Enterprise Microservice Architecture  
**Infrastructure**: Centralized BASE + CORE Pattern with GPU Support
# 🚀 MT5 Trading Client - Clean Architecture

Enterprise-grade MT5 trading client dengan clean architecture implementation.

## 📋 Quick Start

### 🎯 Cara Menjalankan Aplikasi

#### Option 1: Quick Run (Recommended)
```bash
# Langsung jalankan Hybrid Bridge (paling umum digunakan)
python run.py
```

#### Option 2: Main Menu
```bash
# Menu lengkap dengan berbagai pilihan
python main.py
```

### 🎮 Available Applications

1. **Hybrid Bridge** - WebSocket + Redpanda integration (Recommended)
2. **Simple Bridge** - Basic MT5 bridge
3. **Windows Bridge** - Windows-optimized bridge
4. **Bridge App** - Alternative bridge implementation
5. **Service Manager** - Background service management
6. **Check MT5 Market** - Market connectivity testing
7. **Test Configuration** - Configuration validation

## 🏗️ Architecture

### 📁 Folder Structure (Practical Clean Architecture)
```
client_side/
├── main.py                    # 🎯 Main entry point dengan menu lengkap
├── run.py                     # ⚡ Quick run untuk Hybrid Bridge
├── src/                       # 📦 Source code (only what's actually used)
│   ├── infrastructure/        # 🔌 External integrations
│   │   ├── mt5/              # MT5 platform integration
│   │   ├── websocket/        # WebSocket communication  
│   │   └── streaming/        # Redpanda/Kafka streaming
│   ├── presentation/         # 🖥️ User interfaces
│   │   └── cli/              # Command line applications (6 apps)
│   └── shared/               # 🔧 Cross-cutting concerns
│       ├── config/           # Configuration management
│       ├── security/         # Authentication & credentials
│       └── utils/            # Common utilities
├── tests/integration/        # 🧪 Integration tests (12 test files)
├── scripts/                  # 📜 Utility scripts (batch files, etc)
├── config/                   # ⚙️ Requirements & configurations
├── docs/                     # 📚 Documentation
└── logs/                     # 📝 Application logs
```

### 🎯 Core Applications

#### 1. Hybrid Bridge (`src/presentation/cli/hybrid_bridge.py`)
- **Fungsi**: Dual communication (WebSocket + Redpanda)
- **Use case**: Production trading dengan high-frequency data
- **Features**: Real-time tick streaming, command execution

#### 2. MT5 Handler (`src/infrastructure/mt5/mt5_handler.py`)
- **Fungsi**: Core MT5 integration
- **Use case**: Direct MT5 operations
- **Features**: Trading, data retrieval, account management

#### 3. WebSocket Client (`src/infrastructure/websocket/websocket_client.py`)
- **Fungsi**: Communication dengan server-side
- **Use case**: Real-time commands & control
- **Features**: Async communication, message handling

## ⚙️ Configuration

### Client Settings
Edit `src/shared/config/client_settings.py` untuk:
- MT5 connection parameters
- WebSocket server URL
- Redpanda/Kafka configuration
- Logging settings

### Security
Manage credentials dengan `src/shared/security/credentials.py`

## 🧪 Testing

```bash
# Run integration tests
cd tests/integration
python test_client_settings.py
python test_hybrid_bridge_config.py
```

## 📝 Logs

Aplikasi akan generate logs di folder `logs/`:
- `mt5_bridge.log` - Main application logs
- Error logs dan debug information

## 🔧 Development

### Adding New Features
1. **Infrastructure Components** → `src/infrastructure/`
2. **CLI Applications** → `src/presentation/cli/`
3. **Configuration** → `src/shared/config/`
4. **Utilities** → `src/shared/utils/`
5. **Security** → `src/shared/security/`

### Architecture Principles
- **Clean Architecture** dengan dependency inversion
- **SOLID principles** implementation
- **Separation of concerns** antara layers
- **Enterprise patterns** untuk scalability

## 🚨 Troubleshooting

### Common Issues

1. **Import Error**
   ```bash
   # Pastikan running dari root directory client_side/
   cd /path/to/client_side
   python main.py
   ```

2. **MT5 Connection Issues**
   ```bash
   # Test MT5 connection
   python scripts/check_mt5_market.py
   ```

3. **Configuration Problems**
   ```bash
   # Validate configuration
   python tests/integration/test_client_settings.py
   ```

## 📞 Support

- Check documentation di `docs/`
- Review logs di `logs/`
- Run configuration tests di `tests/integration/`

---

**Status**: Production-ready clean architecture ✅  
**Last Updated**: 2025-07-18
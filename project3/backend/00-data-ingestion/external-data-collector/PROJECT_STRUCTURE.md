# Project Structure - MQL5 Historical Scraper

## 📁 Clean Production Structure

```
external-data-collector/
├── 📄 README.md                          # Main documentation
├── 📄 DEPLOYMENT.md                      # Deployment guide
├── 🐳 Dockerfile.historical              # Production Docker image
├── 🐳 docker-compose.historical.yml      # Docker Compose config
├── 📄 requirements.txt                   # Python dependencies
├── 📄 .gitignore                         # Git ignore rules
│
├── 📂 src/                               # Production source code
│   ├── scrapers/
│   │   └── mql5_historical_scraper.py   # Main scraper class
│   └── utils/
│       └── date_tracker.py              # Date tracking utility
│
├── 📂 tests/                             # Production tests
│   └── test_mql5_historical.py          # Comprehensive test suite
│
├── 📂 scripts/                           # CLI tools
│   └── run_backfill.py                  # Backfill/update/report CLI
│
├── 📂 docs/                              # Documentation
│   └── HISTORICAL_SCRAPING_STRATEGY.md  # Complete strategy doc
│
├── 📂 data/                              # Runtime data (gitignored)
│   └── date_tracking.json               # Progress tracking
│
├── 📂 logs/                              # Runtime logs (gitignored)
│   └── mql5_simple.html                 # Sample HTML for debugging
│
├── 📂 _archived/                         # Old files (gitignored)
│   ├── README.md                        # Archive documentation
│   ├── failed-experiments/              # Failed attempts
│   │   ├── economic_calendar_ai.py     # ForexFactory (geo-blocked)
│   │   ├── economic_calendar_mql5.py   # MQL5 Playwright (detected)
│   │   ├── test_playwright_stealth.py  # Stealth tests (failed)
│   │   ├── test_calendar_simple.py     # Old tests
│   │   └── ...                         # Other old test scripts
│   ├── old-dockerfiles/                 # Old Docker configs
│   │   ├── Dockerfile                  # Original
│   │   ├── Dockerfile.simple           # Playwright version
│   │   ├── Dockerfile.warp*            # WARP attempts
│   │   ├── warp-cli (79MB)             # WARP binaries
│   │   ├── warp-svc (33MB)             # WARP binaries
│   │   └── setup_warp*.sh              # WARP scripts
│   ├── old-docs/                        # Obsolete documentation
│   │   ├── DOCKER_DEPLOY.md            # Old deploy guide
│   │   ├── VPS_DEPLOYMENT_GUIDE.md     # VPS guide (not used)
│   │   ├── WARP_SETUP_GUIDE.md         # WARP guide (failed)
│   │   └── SMART_SCRAPING_STRATEGY.md  # Old strategy
│   ├── config/                          # Old configs
│   └── deploy/                          # Old deployment files
│
└── 🛠️ Utility Scripts (kept for debugging)
    ├── test_mql5_simple.py              # Test aiohttp access
    └── analyze_mql5_data.py             # Analyze scraped data
```

## 📊 File Summary

### Production Files (14 files)

**Core Application (4 files)**
- `src/scrapers/mql5_historical_scraper.py` - Main scraper
- `src/utils/date_tracker.py` - Progress tracking
- `tests/test_mql5_historical.py` - Test suite
- `scripts/run_backfill.py` - CLI tool

**Configuration & Deployment (4 files)**
- `Dockerfile.historical` - Docker image
- `docker-compose.historical.yml` - Docker Compose
- `requirements.txt` - Dependencies
- `.gitignore` - Git rules

**Documentation (4 files)**
- `README.md` - Main docs
- `DEPLOYMENT.md` - Deployment guide
- `docs/HISTORICAL_SCRAPING_STRATEGY.md` - Strategy
- `PROJECT_STRUCTURE.md` - This file

**Utilities (2 files)**
- `test_mql5_simple.py` - Quick test tool
- `analyze_mql5_data.py` - Data analysis tool

### Archived Files (138MB)

- **Failed Experiments**: 20+ test scripts
- **Old Dockerfiles**: 8 Docker configs
- **WARP Binaries**: 112MB (warp-cli + warp-svc)
- **Old Documentation**: 4 obsolete docs
- **Old Configs**: deploy/ and config/ folders

## 🎯 Key Directories

### `/src` - Production Code

Clean, production-ready Python code:
- `scrapers/` - Data collection logic
- `utils/` - Shared utilities

### `/tests` - Test Suite

Comprehensive tests covering:
- Single date scraping
- Date range scraping
- Date tracker integration
- Z.ai parser

### `/scripts` - CLI Tools

Command-line interface for:
- Historical backfill (`backfill`)
- Daily updates (`update`)
- Coverage reports (`report`)

### `/docs` - Documentation

In-depth documentation:
- Database schema design
- Scraping strategies (3 types)
- Implementation plan
- Quality checks

### `/data` - Runtime Data

Generated at runtime:
- `date_tracking.json` - Tracks scraped dates
- Created automatically if not exists

### `/logs` - Runtime Logs

Debugging data:
- HTML samples
- Scraping logs
- Error traces

### `/_archived` - Historical Reference

**DO NOT USE for production!**

Contains:
- Failed experiments (learning reference)
- Old Dockerfiles (version history)
- Obsolete docs (historical context)
- Large WARP binaries (112MB)

## 📐 Size Breakdown

```
Total Project:     ~140MB
├── Production:    ~2MB
│   ├── Source:    ~50KB
│   ├── Tests:     ~20KB
│   └── Docs:      ~30KB
└── Archived:      ~138MB
    ├── Binaries:  112MB (WARP)
    ├── Scripts:   ~20MB
    └── Docs:      ~6MB
```

## 🚀 Development Workflow

### 1. Production Work
Work only in:
- `src/`
- `tests/`
- `scripts/`
- `docs/`

### 2. Testing
```bash
# Quick test
python3 test_mql5_simple.py

# Full test suite
docker run --rm mql5-historical-test

# Data analysis
python3 analyze_mql5_data.py
```

### 3. Deployment
```bash
# Build
docker build -f Dockerfile.historical -t mql5-scraper .

# Deploy
docker-compose -f docker-compose.historical.yml up -d

# Run
docker exec -it mql5-historical-scraper \
  python3 scripts/run_backfill.py backfill --months 12
```

## 📝 File Naming Convention

- **Production**: Descriptive names (e.g., `mql5_historical_scraper.py`)
- **Tests**: `test_*.py` prefix
- **Docs**: UPPERCASE.md (e.g., `README.md`)
- **Docker**: `Dockerfile.*` suffix with purpose
- **Archived**: Moved to `_archived/` with categorization

## 🔄 Archive Policy

### When to Archive:
- ❌ Failed experiments
- ❌ Obsolete approaches
- ❌ Replaced implementations
- ❌ Old documentation

### What to Keep:
- ✅ Production code
- ✅ Working tests
- ✅ Current docs
- ✅ Useful utilities

## 🎯 Clean Code Principles

1. **Single Responsibility**: Each file has one clear purpose
2. **DRY**: No duplicate code (utilities in `src/utils/`)
3. **Testable**: All core logic has tests
4. **Documented**: Clear README and inline docs
5. **Minimal**: Only essential files in root

## 📚 Related Documentation

- See `README.md` for quick start
- See `DEPLOYMENT.md` for deployment details
- See `docs/HISTORICAL_SCRAPING_STRATEGY.md` for technical details
- See `_archived/README.md` for historical context

---

**Last Updated**: 2025-10-05
**Status**: ✅ Production Ready

---
name: skill-creator
description: Helper skill for creating new skills following Anthropic's official format with YAML frontmatter, folder structure, and best practices. Use this to avoid repeated browsing of GitHub documentation.
license: MIT
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
metadata:
  type: Development Tool
  purpose: Skill Creation Assistant
  version: 1.0.0
---

# Skill Creator - Anthropic Standard Format

This skill helps you create new skills following Anthropic's official format without needing to browse GitHub documentation repeatedly.

## When to Use This Skill

Use this skill when:
- Creating a new service skill for the AI Trading Platform
- Migrating existing plain .md skills to Anthropic format
- Updating skill structure to match official standards
- Need quick reference for YAML frontmatter fields
- Validating skill format compliance

## Anthropic Skills Format - Quick Reference

### Required Structure

**Minimal Skill:**
```
skill-name/
└── SKILL.md          # Required: YAML frontmatter + markdown content
```

**Complete Skill:**
```
skill-name/
├── SKILL.md          # Required: Instructions with YAML frontmatter
├── scripts/          # Optional: Python/JS helper scripts
│   └── processor.py
└── resources/        # Optional: Templates, configs, data files
    └── template.json
```

### Naming Convention

**CRITICAL**: Use **hyphen-case** (NOT underscore_case)

✅ **CORRECT:**
- `central-hub`
- `polygon-historical-downloader`
- `tick-aggregator`
- `feature-engineering`

❌ **WRONG:**
- `service_central_hub`
- `polygon_historical_downloader`
- `tick_aggregator`
- `feature_engineering`

## SKILL.md Format

### Required YAML Frontmatter

**Minimal Required Fields:**
```yaml
---
name: skill-name              # Must match folder name (hyphen-case)
description: Clear description of what this skill does and when to use it
---
```

**Complete Example with Optional Fields:**
```yaml
---
name: central-hub
description: Manages service discovery, health monitoring, and centralized configuration for all 18 microservices in the Suho Trading Platform
license: MIT
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
metadata:
  type: Core Infrastructure
  port: 7000
  dependencies:
    - postgresql
    - dragonflydb
    - nats
    - kafka
  version: 3.0.0
---
```

### Content Structure

After YAML frontmatter, structure your content with these sections:

```markdown
# Skill Title

Brief introduction paragraph explaining the skill's purpose.

## When to Use This Skill

Use this skill when:
- Situation 1
- Situation 2
- Situation 3

## Service Overview (for service skills)

**Type:** {Data Ingestion|Data Processing|ML|Trading|Supporting}
**Port:** {port-number}
**Dependencies:** {list of dependencies}

## Key Capabilities

- Capability 1
- Capability 2
- Capability 3

## Architecture / How It Works

Detailed explanation of the service architecture, data flow, or process.

### Data Flow (for data pipeline services)

Input → Processing → Output

## Examples

### Example 1: Basic Usage
```python
# Code example showing basic usage
```

### Example 2: Advanced Usage
```python
# Code example showing advanced usage
```

## Guidelines

- **Guideline 1**: Explanation
- **Guideline 2**: Explanation
- **NEVER**: Common mistakes to avoid

## Critical Rules

1. **Rule 1**: Explanation
2. **Rule 2**: Explanation
3. **Rule 3**: Explanation

## Troubleshooting

### Issue 1: Problem Description
**Solution**: How to fix

### Issue 2: Problem Description
**Solution**: How to fix

## Related Skills

- `other-skill-name` - Brief description of relationship
- `another-skill` - Brief description of relationship

## Validation Checklist

After making changes:
- [ ] Validation item 1
- [ ] Validation item 2
- [ ] Validation item 3

## References

- Link to detailed documentation
- Link to API reference
- Link to code files
```

## Step-by-Step Skill Creation Process

### Step 1: Create Folder Structure

```bash
# Navigate to skills directory
cd .claude/skills

# Create skill folder (use hyphen-case!)
mkdir {service-name}

# Create SKILL.md file
touch {service-name}/SKILL.md
```

### Step 2: Add YAML Frontmatter

**Template:**
```yaml
---
name: {service-name}
description: {One-line description of what this service does}
license: MIT
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
metadata:
  type: {Data Ingestion|Data Processing|ML|Trading|Supporting}
  port: {port-number}
  dependencies:
    - central-hub
    - {dependency-1}
    - {dependency-2}
  version: {version}
---
```

### Step 3: Write Content

Follow the content structure outlined above. Make sure to include:

1. **Clear introduction**: What does this skill help with?
2. **When to Use**: Specific situations where this skill applies
3. **Service Overview**: Technical details (type, port, dependencies)
4. **Examples**: Real code examples showing usage
5. **Guidelines**: Best practices and rules
6. **Critical Rules**: Must-follow rules to prevent errors
7. **Related Skills**: Cross-references to other skills
8. **Validation Checklist**: How to verify changes work

### Step 4: Validate Format

Use this checklist:

- [ ] Folder name is hyphen-case (not underscore_case)
- [ ] SKILL.md file exists in folder
- [ ] YAML frontmatter starts and ends with `---`
- [ ] `name` field matches folder name exactly
- [ ] `description` field is clear and complete
- [ ] Content follows markdown best practices
- [ ] Examples section included
- [ ] Guidelines section included
- [ ] Related skills section included
- [ ] No hardcoded secrets in examples

## Complete Example - Data Ingestion Service

**File:** `.claude/skills/polygon-historical-downloader/SKILL.md`

```markdown
---
name: polygon-historical-downloader
description: Downloads historical tick data from Polygon.io with intelligent gap detection and filling, stores in TimescaleDB for OHLCV aggregation
license: MIT
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
metadata:
  type: Data Ingestion
  port: 8001
  dependencies:
    - central-hub
    - timescaledb
    - nats
  version: 2.0.0
---

# Polygon Historical Downloader Service

Downloads historical tick data from Polygon.io with intelligent gap detection, automatic gap filling, and stores tick data in TimescaleDB for downstream OHLCV aggregation.

## When to Use This Skill

Use this skill when:
- Working on Polygon.io historical data downloader
- Implementing gap detection and filling logic
- Debugging tick data ingestion issues
- Configuring symbols or date ranges
- Optimizing batch download performance

## Service Overview

**Type:** Data Ingestion (Historical)
**Port:** 8001
**Data Source:** Polygon.io REST API (trades endpoint)
**Storage:** TimescaleDB (`market_ticks` table)
**Messaging:** NATS (progress updates)

**Dependencies:**
- Central Hub (operational config, service discovery)
- TimescaleDB (tick storage)
- NATS (status broadcasting)

## Key Capabilities

- Historical tick data download from Polygon.io
- Intelligent gap detection across date ranges
- Automatic gap filling
- Configurable batch size and date ranges
- Progress tracking via NATS
- Database deduplication (upsert on conflict)

## Architecture

### Data Flow

```
Polygon.io REST API → Gap Detector → Batch Downloader → TimescaleDB
                                    ↓
                              NATS (progress updates)
```

### Gap Detection Logic

1. Query TimescaleDB for existing data ranges per symbol
2. Compare with target date range
3. Identify missing date chunks (gaps)
4. Download only gaps (skip existing data)

### Configuration

**Operational Config (Central Hub):**
```json
{
  "operational": {
    "batch_size": 150,
    "gap_check_interval_hours": 1,
    "symbols": ["EURUSD", "XAUUSD"],
    "date_range": {
      "start": "2020-01-01",
      "end": "2025-01-01"
    }
  }
}
```

## Examples

### Example 1: Fetch Config from Central Hub

```python
from shared.components.config import ConfigClient

# Initialize client
client = ConfigClient(
    service_name="polygon-historical-downloader",
    safe_defaults={
        "operational": {
            "batch_size": 100,
            "gap_check_interval_hours": 6
        }
    }
)
await client.init_async()

# Get config
config = await client.get_config()
batch_size = config['operational']['batch_size']
symbols = config['operational']['symbols']
```

### Example 2: Download Ticks for Date Range

```python
from polygon_downloader import PolygonHistoricalDownloader

downloader = PolygonHistoricalDownloader()
await downloader.download_ticks(
    symbol="EURUSD",
    start_date="2024-01-01",
    end_date="2024-01-31",
    batch_size=150
)
```

### Example 3: Update Config via Central Hub API

```bash
curl -X POST http://suho-central-hub:7000/api/v1/config/polygon-historical-downloader \
  -H "Content-Type: application/json" \
  -d '{
    "operational": {
      "batch_size": 200,
      "gap_check_interval_hours": 2
    }
  }'
```

## Guidelines

- **ALWAYS** use ConfigClient for operational settings (batch_size, intervals)
- **NEVER** hardcode API keys (use ENV vars: `POLYGON_API_KEY`)
- **USE** safe defaults in ConfigClient (fallback when Hub unavailable)
- **ENABLE** hot-reload for zero-downtime config updates
- **CHECK** gaps before downloading (avoid duplicate API calls)

## Critical Rules

1. **Config Hierarchy:**
   - API keys → ENV variables (`POLYGON_API_KEY`)
   - Operational settings → Central Hub (batch_size, intervals)
   - Safe defaults → ConfigClient fallback

2. **Gap Detection:**
   - ALWAYS check TimescaleDB for existing data first
   - ONLY download missing date ranges
   - Verify gap detection logic checks entire date range, not just between existing data

3. **Data Integrity:**
   - Use `ON CONFLICT (symbol, timestamp_ms) DO NOTHING` for deduplication
   - Validate tick data schema before insertion
   - Handle API rate limits gracefully

## Troubleshooting

### Issue 1: Config Not Found (404)
**Solution:** Add config via Central Hub API or database insert

### Issue 2: Hot-Reload Not Working
**Solution:** Check NATS connection and `enable_nats_updates=True` in ConfigClient

### Issue 3: Gap Detection Missing Gaps
**Solution:** Verify date range logic checks entire range, not just between existing data points

## Related Skills

- `central-hub` - Provides operational config and service discovery
- `tick-aggregator` - Consumes tick data from TimescaleDB
- `data-bridge` - Moves aggregated data to ClickHouse

## Validation Checklist

After making changes:
- [ ] Ticks inserted into TimescaleDB (`market_ticks` table)
- [ ] Gap detection working correctly
- [ ] NATS progress updates broadcasting
- [ ] ConfigClient fetching from Central Hub
- [ ] Hot-reload responding to config updates
- [ ] No API key hardcoding
- [ ] Safe defaults present in ConfigClient

## References

- Full Documentation: `docs/CONFIG_ARCHITECTURE.md`
- Skill Template: `.claude/skills/skill-creator/SKILL.md`
- Central Hub Skill: `.claude/skills/central-hub/SKILL.md`
- Code: `00-data-ingestion/polygon-historical-downloader/`
```

## Common Mistakes to Avoid

### ❌ Mistake 1: Using Underscores in Folder Names

**WRONG:**
```
.claude/skills/service_central_hub/SKILL.md
```

**CORRECT:**
```
.claude/skills/central-hub/SKILL.md
```

---

### ❌ Mistake 2: Missing YAML Frontmatter

**WRONG:**
```markdown
# Central Hub Service

This skill helps...
```

**CORRECT:**
```markdown
---
name: central-hub
description: Service discovery and config management
---

# Central Hub Service

This skill helps...
```

---

### ❌ Mistake 3: Name Mismatch

**WRONG:**
```yaml
# Folder: polygon-historical-downloader/
---
name: polygon-downloader  # ❌ Doesn't match folder!
---
```

**CORRECT:**
```yaml
# Folder: polygon-historical-downloader/
---
name: polygon-historical-downloader  # ✅ Matches folder!
---
```

---

### ❌ Mistake 4: Hardcoded Secrets in Examples

**WRONG:**
```python
POLYGON_API_KEY = "abc123xyz456"  # ❌ NEVER!
```

**CORRECT:**
```python
import os
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")  # ✅ Always ENV vars!
```

---

### ❌ Mistake 5: No Related Skills Section

**WRONG:**
```markdown
# Skill ends here
```

**CORRECT:**
```markdown
## Related Skills

- `central-hub` - Provides config and service discovery
- `tick-aggregator` - Consumes tick data
```

## Templates by Service Type

### Template 1: Data Ingestion Service

```yaml
---
name: {service-name}
description: {Data source} to {storage} with {key features}
license: MIT
allowed-tools:
  - Read
  - Write
  - Bash
metadata:
  type: Data Ingestion
  port: {port}
  dependencies:
    - central-hub
    - timescaledb
    - nats
---

# {Service Name}

{Brief description}

## When to Use This Skill

- Working on {service} data ingestion
- Debugging data collection issues
- Configuring data sources

## Service Overview

**Type:** Data Ingestion
**Port:** {port}
**Data Source:** {API/WebSocket}
**Storage:** {TimescaleDB table}

## Data Flow

{Source} → {Processing} → {Storage} → NATS

## Examples

### Example 1: Fetch Config
{ConfigClient example}

### Example 2: Collect Data
{Data collection example}

## Related Skills

- `central-hub` - Config and service discovery
- `{downstream-service}` - Consumes this data
```

### Template 2: Data Processing Service

```yaml
---
name: {service-name}
description: {Input data} to {output data} with {processing logic}
license: MIT
allowed-tools:
  - Read
  - Write
  - Bash
metadata:
  type: Data Processing
  port: {port}
  dependencies:
    - central-hub
    - timescaledb
    - clickhouse
    - nats
    - kafka
---

# {Service Name}

{Brief description}

## When to Use This Skill

- Working on {processing logic}
- Optimizing {performance aspect}
- Debugging {specific issue}

## Service Overview

**Type:** Data Processing
**Port:** {port}
**Input:** {source and format}
**Output:** {destination and format}

## Processing Logic

{Detailed explanation}

## Examples

### Example 1: Process Data
{Processing example}

## Related Skills

- `{upstream-service}` - Provides input data
- `{downstream-service}` - Consumes output
```

### Template 3: ML Service

```yaml
---
name: {service-name}
description: {ML task} using {algorithm/framework} for {purpose}
license: MIT
allowed-tools:
  - Read
  - Write
  - Bash
metadata:
  type: Machine Learning
  port: {port}
  dependencies:
    - central-hub
    - clickhouse
    - nats
---

# {Service Name}

{Brief description}

## When to Use This Skill

- Training {model type}
- Tuning {hyperparameters}
- Evaluating {metrics}

## Service Overview

**Type:** ML
**Port:** {port}
**Framework:** {TensorFlow/PyTorch/FinRL}
**Model:** {model architecture}

## Training Pipeline

{Steps}

## Examples

### Example 1: Train Model
{Training example}

## Related Skills

- `feature-engineering` - Provides features
- `inference` - Uses trained models
```

## AI Trading Platform Service Categories

When creating skills for the AI Trading Platform, use these categories:

1. **Data Ingestion** (5 services)
   - polygon-live-collector
   - polygon-historical-downloader
   - dukascopy-historical-downloader
   - external-data-collector
   - mt5-connector

2. **Data Processing** (3 services)
   - tick-aggregator
   - data-bridge
   - feature-engineering

3. **Machine Learning** (3 services)
   - supervised-training
   - finrl-training
   - inference

4. **Trading Execution** (3 services)
   - risk-management
   - execution
   - performance-monitoring

5. **Supporting Services** (4 services)
   - central-hub (Core Infrastructure)
   - backtesting
   - dashboard
   - notification-hub

## Validation Script

Use this bash script to validate skill format:

```bash
#!/bin/bash
# validate_skills.sh

SKILLS_DIR=".claude/skills"

echo "🔍 Validating Skills Format..."

# Check all skills have SKILL.md
skill_count=$(find "$SKILLS_DIR" -maxdepth 2 -name "SKILL.md" | wc -l)
echo "Found $skill_count skills with SKILL.md"

# Check YAML frontmatter
for skill in "$SKILLS_DIR"/*/SKILL.md; do
  skill_name=$(dirname "$skill" | xargs basename)

  # Check frontmatter exists
  if ! head -1 "$skill" | grep -q "^---$"; then
    echo "❌ Missing YAML frontmatter: $skill_name"
  else
    echo "✅ YAML frontmatter found: $skill_name"
  fi

  # Check name matches folder
  yaml_name=$(grep "^name:" "$skill" | awk '{print $2}')
  if [ "$yaml_name" != "$skill_name" ]; then
    echo "❌ Name mismatch in $skill_name: folder=$skill_name, yaml=$yaml_name"
  fi
done

# Check for underscore folders (should be hyphens)
if find "$SKILLS_DIR" -maxdepth 1 -type d -name "*_*" | grep -q .; then
  echo "❌ ERROR: Found folders with underscores (should use hyphens):"
  find "$SKILLS_DIR" -maxdepth 1 -type d -name "*_*"
fi

echo "✅ Validation complete!"
```

## Quick Reference Card

**Folder Structure:**
```
.claude/skills/{skill-name}/SKILL.md
```

**Naming:** hyphen-case (NOT underscore_case)

**YAML Required:**
```yaml
---
name: skill-name
description: What it does
---
```

**Content Sections:**
1. Title + Introduction
2. When to Use
3. Service Overview
4. Examples
5. Guidelines
6. Critical Rules
7. Related Skills
8. Validation Checklist

**Common Dependencies:**
- central-hub (almost all services)
- timescaledb (data ingestion)
- clickhouse (data processing/ML)
- nats (messaging)
- kafka (archival)

## Related Skills

- `central-hub` - All service skills should reference Central Hub for config
- `systematic-debugging` - Use when debugging skill implementation

## References

- Anthropic Official Skills: https://github.com/anthropics/skills
- AI Trading Platform Architecture: `docs/CONFIG_ARCHITECTURE.md`
- Service Template: `.claude/skills/_SERVICE_SKILL_TEMPLATE.md`
- Migration Plan: `docs/ANTHROPIC_SKILLS_FORMAT_ANALYSIS.md`

---

**Created:** 2025-10-19
**Version:** 1.0.0
**Purpose:** Enable rapid skill creation following Anthropic standards without repeated browsing

# Anthropic Skills Format - Analysis & Migration Plan

**Date:** 2025-10-19
**Status:** 🔴 CRITICAL - Our skills don't follow Anthropic standard!
**Action Required:** Restructure all skills to match official format

---

## 🚨 CRITICAL FINDING

**Our current skills DO NOT follow Anthropic's official format!**

### **What We Have (WRONG):**
```
.claude/skills/
├── service_central_hub.md          ❌ Plain markdown
├── service_polygon_historical_downloader.md  ❌ Plain markdown
├── service_tick_aggregator.md      ❌ Plain markdown
└── ... (16 more .md files)          ❌ All wrong format
```

### **What Anthropic Requires (CORRECT):**
```
.claude/skills/
├── central-hub/                     ✅ Folder per skill
│   ├── SKILL.md                    ✅ YAML frontmatter + markdown
│   ├── scripts/                    ✅ Optional: Python/JS helpers
│   └── resources/                  ✅ Optional: Templates, configs
├── polygon-historical-downloader/   ✅ Folder per skill
│   └── SKILL.md                    ✅ YAML frontmatter + markdown
└── ... (16 more folders)           ✅ Each with SKILL.md
```

---

## 📖 ANTHROPIC OFFICIAL FORMAT

### **Required Structure**

**Minimal Skill:**
```
skill-name/
└── SKILL.md
```

**Complete Skill:**
```
skill-name/
├── SKILL.md          # Required: Instructions with YAML frontmatter
├── scripts/          # Optional: Python/JS code
│   └── processor.py
└── resources/        # Optional: Templates, data
    └── template.json
```

---

### **SKILL.md Format (MANDATORY)**

```markdown
---
name: skill-name
description: Clear description of what this skill does and when to use it
---

# Skill Title

Main instructions that Claude will follow when this skill is active.

## When to Use This Skill

- Situation 1
- Situation 2

## How It Works

Detailed explanation of the skill's behavior.

## Examples

### Example 1: Basic Usage
```
Example code or demonstration
```

### Example 2: Advanced Usage
```
More complex example
```

## Guidelines

- Guideline 1
- Guideline 2
- Best practices

## Related Skills

- other-skill-name - Brief description
```

---

### **YAML Frontmatter Fields**

**Required:**
- `name` - Must match directory name in hyphen-case (e.g., `central-hub`)
- `description` - Complete description of purpose and usage

**Optional:**
- `license` - License information
- `allowed-tools` - List of tools this skill can use
- `metadata` - Additional metadata

**Example:**
```yaml
---
name: central-hub
description: Manages service discovery, health monitoring, and centralized configuration for all 18 microservices in the Suho Trading Platform
license: MIT
allowed-tools:
  - Read
  - Write
  - Bash
  - Grep
---
```

---

## 🔍 COMPARISON: Our Format vs Anthropic Format

### **Current Format (WRONG)**

**File:** `service_central_hub.md`
```markdown
# Central Hub Service Skill

**Service Name:** central-hub
**Type:** Core Infrastructure
**Port:** 7000
**Purpose:** Centralized coordination...

---

## 📋 QUICK REFERENCE

**When to use this skill:**
- Working on Central Hub service
...
```

**Issues:**
- ❌ No YAML frontmatter
- ❌ Not in a folder structure
- ❌ Filename doesn't follow convention
- ❌ Structure doesn't match Anthropic standard

---

### **Anthropic Format (CORRECT)**

**Folder:** `central-hub/`
**File:** `central-hub/SKILL.md`
```markdown
---
name: central-hub
description: Manages service discovery, health monitoring, and centralized configuration for all 18 microservices in the Suho Trading Platform
---

# Central Hub Service

This skill helps you work with the Central Hub service, which provides centralized coordination, service discovery, health monitoring, and operational configuration management.

## When to Use This Skill

- Working on Central Hub service
- Adding new API endpoints
- Managing service configurations
- Debugging service discovery
- Monitoring infrastructure health

## Service Overview

**Type:** Core Infrastructure
**Port:** 7000
**Dependencies:** PostgreSQL, DragonflyDB, NATS, Kafka

## Key Capabilities

- Centralized configuration management (PostgreSQL storage)
- Service discovery and registry
- Health monitoring and aggregation
- Workflow orchestration
- Infrastructure monitoring (databases, messaging)
- NATS/Kafka message broadcasting

## Configuration Management

### Architecture

Central Hub manages TWO configuration systems:
...

## Examples

### Example 1: Fetching Service Config
```python
# Use ConfigClient to fetch operational config
from shared.components.config import ConfigClient

client = ConfigClient("polygon-historical-downloader")
await client.init_async()
config = await client.get_config()
```

### Example 2: Updating Config via API
```bash
curl -X POST http://suho-central-hub:7000/api/v1/config/polygon-historical-downloader \
  -H "Content-Type: application/json" \
  -d '{"operational": {"batch_size": 150}}'
```

## Guidelines

- NEVER put secrets in Central Hub (use ENV vars)
- ALWAYS provide safe defaults in ConfigClient
- Use InfrastructureConfigManager ONLY in Central Hub
- Services should use ConfigClient for operational configs

## Related Skills

- `polygon-historical-downloader` - Uses Central Hub for config
- `tick-aggregator` - Depends on Central Hub for discovery
- `data-bridge` - Consumes Central Hub health metrics
```

---

## 📊 MIGRATION REQUIREMENTS

### **All 18 Skills Need Migration**

| Current | Required | Action |
|---------|----------|--------|
| `service_central_hub.md` | `central-hub/SKILL.md` | Restructure + Add YAML |
| `service_polygon_historical_downloader.md` | `polygon-historical-downloader/SKILL.md` | Restructure + Add YAML |
| `service_polygon_live_collector.md` | `polygon-live-collector/SKILL.md` | Restructure + Add YAML |
| `service_tick_aggregator.md` | `tick-aggregator/SKILL.md` | Restructure + Add YAML |
| ... | ... | ... |
| (All 18 services) | (All 18 folders) | Full migration |

---

## 🔄 MIGRATION PLAN

### **Phase 1: Restructure Directory**

**Before:**
```
.claude/skills/
├── service_central_hub.md
├── service_polygon_historical_downloader.md
└── ... (16 more .md files)
```

**After:**
```
.claude/skills/
├── central-hub/
│   └── SKILL.md
├── polygon-historical-downloader/
│   └── SKILL.md
├── polygon-live-collector/
│   └── SKILL.md
└── ... (16 more folders)
```

---

### **Phase 2: Convert Content**

**For Each Skill:**

1. **Create folder** with hyphen-case name
   ```bash
   mkdir .claude/skills/central-hub
   ```

2. **Create SKILL.md** with YAML frontmatter
   ```yaml
   ---
   name: central-hub
   description: Service description
   ---
   ```

3. **Convert content:**
   - Remove `# Service Name Skill` header
   - Remove metadata table (`**Service Name:**`, `**Type:**`, etc.)
   - Restructure to Anthropic format
   - Add proper sections (When to Use, Examples, Guidelines)

4. **Validate:**
   - YAML frontmatter correct
   - Name matches folder
   - Content follows markdown best practices

---

### **Phase 3: Add YAML Frontmatter**

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
    - postgresql
    - nats
---
```

---

## 📝 CONVERSION EXAMPLE

### **Before (Current Format)**

**File:** `service_central_hub.md`
```markdown
# Central Hub Service Skill

**Service Name:** central-hub
**Type:** Core Infrastructure
**Port:** 7000
**Purpose:** Centralized coordination, service discovery...

---

## 📋 QUICK REFERENCE

**When to use this skill:**
- Working on Central Hub service
- Adding new API endpoints
...
```

---

### **After (Anthropic Format)**

**File:** `central-hub/SKILL.md`
```markdown
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
metadata:
  type: Core Infrastructure
  port: 7000
  dependencies:
    - postgresql
    - dragonflydb
    - nats
    - kafka
---

# Central Hub Service

Centralized coordination, service discovery, health monitoring, and operational configuration management.

## When to Use This Skill

Use this skill when:
- Working on Central Hub service
- Adding new API endpoints
- Managing service configurations
- Debugging service discovery
- Monitoring infrastructure health

## Service Overview

The Central Hub is the core infrastructure service that coordinates all 18 microservices in the Suho Trading Platform.

**Key Responsibilities:**
- Service discovery and registry
- Centralized configuration management
- Health monitoring and aggregation
- Workflow orchestration
- Infrastructure monitoring

## Configuration Management

Central Hub provides two configuration systems:

### System 1: Infrastructure Config (Internal)
Uses `InfrastructureConfigManager` for Central Hub's own infrastructure settings.

### System 2: Operational Config (Services)
Provides `ConfigClient` API for all services to fetch operational configurations.

## Examples

### Example 1: Fetch Service Config
```python
from shared.components.config import ConfigClient

client = ConfigClient("polygon-historical-downloader")
await client.init_async()
config = await client.get_config()
batch_size = config['operational']['batch_size']
```

### Example 2: Update Config via API
```bash
curl -X POST http://suho-central-hub:7000/api/v1/config/polygon-historical-downloader \
  -H "Content-Type: application/json" \
  -d '{"operational": {"batch_size": 150}}'
```

## Guidelines

- **NEVER** put secrets in Central Hub (use ENV vars)
- **ALWAYS** provide safe defaults in ConfigClient
- **Use** InfrastructureConfigManager ONLY within Central Hub
- **Services** should use ConfigClient for operational configs

## Critical Rules

1. **Config Hierarchy:**
   - ENV vars → Critical (secrets, credentials)
   - Central Hub → Operational (batch_size, intervals)
   - Safe defaults → Fallback (when Hub unavailable)

2. **NATS Broadcasting:**
   - Config updates broadcast to `config.update.{service_name}`
   - Services auto-reload via hot-reload subscription

## Related Skills

- `polygon-historical-downloader` - Uses Central Hub for config
- `tick-aggregator` - Depends on Central Hub for coordination
- `data-bridge` - Consumes Central Hub health metrics
- `feature-engineering` - Uses Central Hub service discovery

## Troubleshooting

### Config Not Found (404)
Add config via API or database insert.

### Hot-Reload Not Working
Check NATS connection and `enable_nats_updates=True`.

## References

- Full Documentation: `docs/CONFIG_ARCHITECTURE.md`
- API Reference: Central Hub skill file
- Template: `_SERVICE_SKILL_TEMPLATE.md`
```

---

## ✅ VALIDATION CHECKLIST

**After Migration:**

### **Structure**
- [ ] Each skill in its own folder
- [ ] Folder name is hyphen-case
- [ ] SKILL.md file exists in each folder
- [ ] No more plain .md files in skills root

### **Content**
- [ ] YAML frontmatter present
- [ ] `name` field matches folder name
- [ ] `description` field is clear and complete
- [ ] Content follows Anthropic format
- [ ] Examples section included
- [ ] Guidelines section included

### **Quality**
- [ ] No hardcoded secrets in examples
- [ ] Cross-references to other skills
- [ ] Related skills listed
- [ ] Troubleshooting section helpful

---

## 🚀 EXECUTION PLAN

### **Step 1: Create Migration Script**

```bash
#!/bin/bash
# migrate_skills_to_anthropic_format.sh

SKILLS_DIR=".claude/skills"

# List of services
SERVICES=(
  "central-hub"
  "polygon-historical-downloader"
  "polygon-live-collector"
  "dukascopy-historical-downloader"
  "external-data-collector"
  "tick-aggregator"
  "data-bridge"
  "feature-engineering"
  "supervised-training"
  "finrl-training"
  "inference"
  "risk-management"
  "execution"
  "performance-monitoring"
  "mt5-connector"
  "backtesting"
  "dashboard"
  "notification-hub"
)

for service in "${SERVICES[@]}"; do
  # Convert underscores to hyphens
  service_dir=$(echo "$service" | tr '_' '-')

  # Create folder
  mkdir -p "$SKILLS_DIR/$service_dir"

  # Move and rename file (if old format exists)
  old_file="$SKILLS_DIR/service_${service}.md"
  new_file="$SKILLS_DIR/$service_dir/SKILL.md"

  if [ -f "$old_file" ]; then
    # Add YAML frontmatter and move
    echo "Migrating $service..."
    # (Content conversion would go here)
  fi
done

echo "Migration complete!"
```

---

### **Step 2: Manual Conversion**

For each skill:

1. Create folder: `mkdir .claude/skills/{service-name}`
2. Create `SKILL.md` with YAML frontmatter
3. Convert content to Anthropic format
4. Add examples and guidelines
5. Validate against checklist

---

### **Step 3: Validation**

```bash
# Check all skills have SKILL.md
find .claude/skills -name "SKILL.md" | wc -l
# Expected: 18

# Check YAML frontmatter
for skill in .claude/skills/*/SKILL.md; do
  head -1 "$skill" | grep -q "^---$" || echo "Missing YAML: $skill"
done

# Check folder names (should be hyphen-case)
find .claude/skills -maxdepth 1 -type d | grep "_" && echo "ERROR: Underscores found!"
```

---

## 📅 TIMELINE

**Total Estimated Time:** 12-15 hours

### **Phase 1: Setup** (1 hour)
- Create migration script
- Prepare YAML templates
- Test with 1 service

### **Phase 2: Data Pipeline** (4 hours)
- Migrate 5 core services
- Validate structure

### **Phase 3: ML Pipeline** (3 hours)
- Migrate 4 ML services
- Add cross-references

### **Phase 4: Trading & Supporting** (4 hours)
- Migrate remaining 9 services
- Final validation

### **Phase 5: Cleanup** (1 hour)
- Remove old .md files
- Update CLAUDE.md
- Update README.md

---

## 🎯 SUCCESS CRITERIA

- [x] All 18 skills in folder structure
- [x] Each has SKILL.md with YAML frontmatter
- [x] All names are hyphen-case
- [x] Content follows Anthropic format
- [x] No old .md files remain
- [x] Cross-references updated
- [x] CLAUDE.md references correct paths

---

## 📖 REFERENCES

**Official Anthropic Documentation:**
- https://github.com/anthropics/skills
- https://github.com/anthropics/claude-cookbooks/tree/main/skills

**Example Skills:**
- https://github.com/anthropics/skills/tree/main/document-skills/pdf
- https://github.com/anthropics/skills/tree/main/document-skills/xlsx

**Community Resources:**
- https://simonwillison.net/2025/Oct/16/claude-skills/
- https://github.com/travisvn/awesome-claude-skills

---

## 🚨 CRITICAL NEXT STEPS

**BEFORE continuing with centralized config updates:**

1. ✅ **STOP** adding content to current .md files
2. ✅ **MIGRATE** to Anthropic format first
3. ✅ **THEN** add centralized config sections

**Reason:** Don't waste time updating skills in wrong format!

---

**Status:** 🔴 URGENT - Migration required before continuing
**Priority:** P0 - Blocks all other skill updates
**Owner:** Immediate action required
**Timeline:** Start today, complete within 2 days

---

**Created:** 2025-10-19
**Last Updated:** 2025-10-19
**Version:** 1.0.0

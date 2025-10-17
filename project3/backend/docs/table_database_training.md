# 🎓 Database Training Tables - ML/FinRL Training Infrastructure

> **Version**: 1.0.0 (Draft - Placeholder)
> **Last Updated**: 2025-10-17
> **Status**: Not Yet Discussed - Waiting for Process Discussion

---

## 📋 Overview

**Purpose**: Dokumentasi untuk tabel-tabel yang digunakan dalam **ML/FinRL Training Process**

**Input**: `ml_features` table (dari table_database_process.md)
**Output**: Trained models, checkpoints, metrics

**Status**: ⚠️ **FILE PLACEHOLDER** - Will be designed after completing `table_database_process.md` discussion

---

## 🎯 Training Pipeline (To Be Designed)

```
ml_features (72 features)
    ↓
Training Service (ML/FinRL)
    ↓
Training Tables (This document)
```

---

## 📊 Planned Tables (To Be Discussed)

### **1. training_runs**
Track setiap training experiment

### **2. model_checkpoints**
Store model weights & artifacts

### **3. agent_versions**
Version control untuk trained agents

### **4. hyperparameters_log**
Log hyperparameters untuk setiap run

### **5. training_metrics**
Performance metrics selama training

### **6. reward_history** (FinRL specific)
Reward evolution per episode

---

## 📝 Discussion Topics

1. **ML Framework Choice**
   - Supervised ML (sklearn, XGBoost, LightGBM)?
   - Deep Learning (TensorFlow, PyTorch)?
   - Reinforcement Learning (FinRL)?
   - Hybrid approach?

2. **Model Storage Strategy**
   - ClickHouse (binary storage)
   - S3/MinIO (object storage)
   - File system + metadata in ClickHouse

3. **Experiment Tracking**
   - MLflow integration?
   - Custom tracking system?
   - TensorBoard for DL?

4. **Training Strategy**
   - Batch training (periodic retrain)
   - Online learning (continuous update)
   - Transfer learning

---

## 🚧 Status

**Next Steps**:
1. ✅ Complete `table_database_process.md` discussion
2. ⚠️ Design training infrastructure tables (this file)
3. ⚠️ Design trading/deployment tables

---

**This document will be updated after completing the feature engineering discussion.**

**Version History**:
- v1.0.0 (2025-10-17): Initial placeholder - awaiting process discussion completion

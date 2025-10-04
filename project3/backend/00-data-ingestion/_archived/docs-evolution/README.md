# Archived Documentation - Evolution History

## 📚 Documentation Evolution

This folder contains **previous versions** of documentation as the strategy evolved based on user decisions.

---

## 📖 Evolution Timeline

### **Phase 1: Initial Free Tier Strategy**

**Files:**
- `TWELVE_DATA_STRATEGY.md` (25KB)
- `SYMBOL_SELECTION_ANALYSIS.md` (14KB)

**Context:**
- Designed for FREE tier limitations
- 8 WebSocket + 15 REST = 23 pairs total
- Focus on FREE ETF proxies (UUP, SPY)
- No macro instruments (not available on free)

**User Feedback:** "Saya rencana pakai yang berbayar 29 dolar nanti"

---

### **Phase 2: Macro Instruments Research**

**Files:**
- `MACRO_INSTRUMENTS_ANALYSIS.md` (20KB)
- `MACRO_SUMMARY.md` (6KB)
- `test_macro_*.py` (Testing scripts)

**Context:**
- Research into commodities, indices for forex analysis
- Discovered US10Y, DXY, SPX critical for forex
- Found most macro symbols require PAID plan
- Tested availability (UUP, SPY available on free)

**User Decision:** Will use Pro plan ($29/month)

---

### **Phase 3: Pro Plan Initial Allocation**

**Files:**
- `OPTIMAL_ALLOCATION_PRO_PLAN.md` (15KB)
- `FINAL_SYMBOL_ALLOCATION.md` (12KB)

**Context:**
- Designed for Pro plan ($29/month)
- 78 symbols total (8 WS + 70 REST)
- Comprehensive coverage with ALL available symbols
- Included yields, indices, commodities, crypto, regional indices

**User Feedback:** "Jangan memasukkan pair yang kurang berguna"

---

### **Phase 4: Refined Allocation (CURRENT)**

**Files:** (In main docs folder)
- `REFINED_ALLOCATION_PRO.md`
- `PRO_PLAN_SUMMARY.md`

**Context:**
- Eliminated 38 low-value symbols
- 40 symbols total (8 WS + 32 REST)
- Focus on quality over quantity
- Every symbol justified (>0.60 forex correlation)
- No redundancy, high liquidity only

**Status:** ✅ Current production strategy

---

## 🎯 Key Learnings

### **Eliminated Symbols & Why:**

1. **Redundant Correlations (>0.85):**
   - US02Y, US30Y → Use US10Y only
   - NDX, DJI → Use SPX only
   - BRENT → Use WTI only
   - EUR/NZD, GBP/NZD → Covered by EUR/AUD, GBP/AUD

2. **Low Liquidity:**
   - EUR/SEK, USD/SEK, GBP/SEK
   - EUR/CHF, GBP/CHF (lower priority crosses)
   - EUR/PLN, EUR/TRY (emerging markets)

3. **Low Forex Correlation (<0.40):**
   - WHEAT, CORN (agricultural)
   - PLATINUM, PALLADIUM, ALUMINUM
   - BNB, XRP, ADA (only BTC/ETH matter)

4. **Redundant Regional Indices:**
   - FTSE, CAC, HSI, ASX, TSX
   - SPX sufficient, use currency pairs directly

### **Final Principle:**

> **"Every symbol must earn its place with either:**
> **- High forex correlation (>0.60), OR**
> **- Unique critical information (US10Y, DXY, VIX)"**

---

## 📊 Evolution Summary

| Phase | Symbols | Focus | Issue |
|-------|---------|-------|-------|
| **Phase 1** | 23 | Free tier | Limited macro access |
| **Phase 2** | Research | Macro instruments | Testing availability |
| **Phase 3** | 78 | Pro plan comprehensive | Too many redundant |
| **Phase 4** | 40 | Pro plan refined | ✅ Optimal |

---

## 🎓 Lessons Learned

1. **More symbols ≠ Better analysis**
   - 78 symbols had massive redundancy
   - 40 symbols provides same coverage

2. **Correlation analysis critical**
   - Eliminate pairs with >0.85 correlation
   - Focus on complementary (<0.60 corr)

3. **Liquidity matters**
   - Low liquidity = wide spreads
   - Stick to major pairs only

4. **Forex correlation threshold**
   - Need >0.60 correlation to be useful
   - Agricultural, some metals don't qualify

5. **Quality over quantity**
   - Every symbol should have clear purpose
   - If can't justify it, eliminate it

---

## 📝 Test Scripts History

**Testing Evolution:**

1. `test_twelve_data.py` - Verified API limits (8 req/min, 800/day)
2. `test_twelve_data_ws.py` - Tested WebSocket symbol limits (8 max)
3. `test_macro_symbols.py` - Comprehensive macro symbol testing
4. `test_macro_quick.py` - Quick critical symbols test
5. `test_macro_alternatives.py` - ETF alternatives discovery

**Key Discovery:** Most macro symbols require Grow plan ($79), not Pro ($29)

---

## 🔗 References

**Current Production Docs:**
- `/REFINED_ALLOCATION_PRO.md` - Optimal 40 symbol strategy
- `/PRO_PLAN_SUMMARY.md` - Quick reference
- `/QUICK_REFERENCE.md` - Trading vs analysis pairs
- `/PAIR_CLASSIFICATION.md` - Detailed pair breakdown

**Configuration:**
- `/config/config-pro-plan.yaml` - Original 78 symbols (archived)
- `/config/config-pro-plan-refined.yaml` - Current 40 symbols (to be created)

---

## ⚠️ Note

These archived documents are **historical reference only**.

**DO NOT use for production!**

Use current documentation in main folder.

---

**Last Updated:** 2025-10-02
**Archive Reason:** Evolution to refined Pro plan strategy
**Maintained By:** Development team

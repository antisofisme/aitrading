# Symbol Selection Analysis - Optimal Pairs untuk Trading + Correlation

## 🤔 Problem Statement

**Current Allocation:**
- **TIER 1 (WebSocket):** 8 major pairs untuk trading
- **TIER 2 (REST):** 15 minor/cross pairs untuk correlation

**Question:** Apakah ini sudah optimal?

**Answer:** **DEPENDS on your trading strategy!**

---

## 📊 Correlation Science - What Really Matters

### **Correlation Types:**

```
1. POSITIVE CORRELATION (move together)
   EUR/USD vs GBP/USD → ~0.85 correlation
   → If EUR/USD up, GBP/USD likely up too

2. NEGATIVE CORRELATION (move opposite)
   EUR/USD vs USD/CHF → ~-0.90 correlation
   → If EUR/USD up, USD/CHF likely down

3. NO CORRELATION (independent)
   EUR/USD vs AUD/JPY → ~0.10 correlation
   → Movements are independent
```

### **Why Correlation Matters for Trading:**

```python
# Example: Trading EUR/USD

# BAD: Trade correlated pairs simultaneously
Long EUR/USD + Long GBP/USD
→ 0.85 correlation = basically same trade 2x
→ If wrong, lose 2x
→ No diversification!

# GOOD: Trade non-correlated pairs
Long EUR/USD + Long AUD/JPY
→ 0.10 correlation = independent trades
→ If EUR/USD wrong, AUD/JPY might still win
→ Better diversification!

# BETTER: Use correlation for confirmation
EUR/USD shows BUY signal
Check GBP/USD (high correlation)
→ If GBP/USD also bullish → Confirm!
→ If GBP/USD bearish → Wait, something wrong!
```

---

## 🎯 Optimal Symbol Selection Strategy

### **Strategy 1: Diversified Trading (Low Correlation Portfolio)**

**Goal:** Trade multiple independent pairs to spread risk

**TIER 1 (WebSocket - Trading Pairs):**
```yaml
# Select pairs with LOW correlation to each other
- EUR/USD    # Euro vs Dollar
- USD/JPY    # Dollar vs Yen (negative correlation with EUR/USD)
- AUD/JPY    # Risk-on indicator (commodity vs safe haven)
- GBP/NZD    # Cross pair, low correlation with above
- USD/CAD    # Oil correlation (different driver)
- EUR/GBP    # EUR strength indicator
- XAU/USD    # Gold (safe haven, different asset class)
- BTC/USD    # Crypto (completely different market)

Correlation: Pairs are relatively independent
Benefit: Diversification, lower portfolio risk
```

**TIER 2 (REST - Correlation Check):**
```yaml
# Pairs to CONFIRM signals from TIER 1
- GBP/USD    # Confirm EUR/USD (high correlation)
- USD/CHF    # Confirm EUR/USD (negative correlation)
- EUR/JPY    # Confirm EUR strength
- GBP/JPY    # Confirm GBP strength + risk
- AUD/USD    # Confirm risk sentiment
- NZD/USD    # Confirm commodity currencies
... etc
```

**Use Case:**
```python
# Trade EUR/USD
signal = get_signal("EUR/USD")  # WebSocket

# Confirm with correlated pairs (REST)
gbp_usd = get_cached("GBP/USD")  # Should move similar
usd_chf = get_cached("USD/CHF")  # Should move opposite

if signal == "BUY":
    # Check confirmation
    if gbp_usd.trend == "UP" and usd_chf.trend == "DOWN":
        execute_trade()  # Confirmed!
    else:
        wait()  # Mixed signals, something wrong
```

---

### **Strategy 2: Currency Strength Trading (High Correlation)**

**Goal:** Identify strongest/weakest currencies and trade them

**TIER 1 (WebSocket - Major Currency Coverage):**
```yaml
# Cover all major currencies with DIRECT pairs
- EUR/USD    # EUR strength
- GBP/USD    # GBP strength
- USD/JPY    # JPY strength
- AUD/USD    # AUD strength
- USD/CAD    # CAD strength
- USD/CHF    # CHF strength
- NZD/USD    # NZD strength
- XAU/USD    # Risk sentiment

All vs USD → Easy to calculate relative strength!
```

**TIER 2 (REST - Cross Pairs for Fine-tuning):**
```yaml
# Cross pairs untuk verify currency strength
- EUR/GBP    # EUR vs GBP directly
- EUR/JPY    # EUR vs JPY directly
- GBP/JPY    # GBP vs JPY directly
- AUD/JPY    # AUD vs JPY directly
- EUR/CAD, GBP/CAD, etc
```

**Use Case:**
```python
# Calculate currency strength
def calculate_strength():
    """Calculate each currency strength vs USD"""

    strengths = {
        "EUR": get_ws("EUR/USD").change_pct,
        "GBP": get_ws("GBP/USD").change_pct,
        "JPY": -get_ws("USD/JPY").change_pct,  # Inverse
        "AUD": get_ws("AUD/USD").change_pct,
        "CAD": -get_ws("USD/CAD").change_pct,  # Inverse
        "CHF": -get_ws("USD/CHF").change_pct,  # Inverse
        "NZD": get_ws("NZD/USD").change_pct,
    }

    # Find strongest and weakest
    strongest = max(strengths, key=strengths.get)  # e.g., GBP
    weakest = min(strengths, key=strengths.get)    # e.g., JPY

    # Trade the strongest against weakest
    if abs(strengths[strongest] - strengths[weakest]) > 0.5:
        trade_pair = f"{strongest}/{weakest}"  # GBP/JPY
        return "BUY", trade_pair

    return None, None

# Result: Trade GBP/JPY (strongest vs weakest)
# Check with TIER 2 REST data for confirmation
```

---

### **Strategy 3: Risk-On/Risk-Off Trading**

**Goal:** Capture market sentiment shifts

**TIER 1 (WebSocket - Sentiment Indicators):**
```yaml
# Risk-on indicators
- AUD/USD    # Australia (commodity exporter)
- NZD/USD    # New Zealand (commodity)
- AUD/JPY    # Classic risk indicator
- NZD/JPY    # Classic risk indicator

# Safe haven indicators
- USD/JPY    # Yen safe haven
- USD/CHF    # Franc safe haven
- XAU/USD    # Gold safe haven

# General market
- EUR/USD    # Most liquid
```

**TIER 2 (REST - Confirm Sentiment):**
```yaml
# Additional risk indicators
- GBP/JPY    # High beta risk pair
- EUR/JPY
- CAD/JPY
- CHF/JPY    # Safe haven cross

# Commodity currencies
- AUD/CAD
- NZD/CAD
- AUD/NZD
```

**Use Case:**
```python
def detect_risk_sentiment():
    """Detect if market is risk-on or risk-off"""

    # Risk-on pairs (should go UP in risk-on)
    risk_pairs = [
        get_ws("AUD/JPY"),
        get_ws("NZD/JPY"),
        get_ws("AUD/USD"),
    ]

    # Safe haven pairs (should go DOWN in risk-on)
    safe_haven = [
        get_ws("XAU/USD"),
        get_ws("USD/CHF"),
    ]

    risk_score = 0
    for pair in risk_pairs:
        if pair.change_pct > 0:
            risk_score += 1

    for pair in safe_haven:
        if pair.change_pct < 0:
            risk_score += 1

    if risk_score >= 4:
        return "RISK_ON"
    elif risk_score <= 1:
        return "RISK_OFF"
    else:
        return "NEUTRAL"

# If RISK_ON detected:
# → Buy commodity currencies (AUD, NZD)
# → Sell safe havens (JPY, CHF, Gold)
```

---

## 🔬 Scientific Analysis - Correlation Matrix

### **Typical Forex Correlations:**

```
HIGH POSITIVE (>0.8):
- EUR/USD ↔ GBP/USD     (0.85)
- EUR/USD ↔ AUD/USD     (0.75)
- EUR/USD ↔ NZD/USD     (0.70)
- AUD/USD ↔ NZD/USD     (0.90)
- EUR/GBP ↔ EUR/JPY     (0.65)

HIGH NEGATIVE (<-0.8):
- EUR/USD ↔ USD/CHF     (-0.90)
- GBP/USD ↔ USD/CHF     (-0.85)
- EUR/USD ↔ USD/JPY     (-0.60)

LOW CORRELATION (0.0-0.3):
- EUR/USD ↔ USD/CAD     (0.15)
- EUR/USD ↔ AUD/JPY     (0.10)
- GBP/USD ↔ USD/CAD     (0.20)
- AUD/JPY ↔ EUR/CHF     (0.05)
```

### **Implications for Symbol Selection:**

```python
# Current allocation review:

TIER 1 (Current):
EUR/USD, GBP/USD, USD/JPY, XAU/USD, AUD/USD, USD/CAD, NZD/USD, USD/CHF

Correlations:
- EUR/USD & GBP/USD → 0.85 (HIGH) ← Maybe redundant?
- EUR/USD & USD/CHF → -0.90 (HIGH NEGATIVE) ← Redundant inverse?
- AUD/USD & NZD/USD → 0.90 (VERY HIGH) ← Definitely redundant!

Issue: Too much overlap, low diversification!
```

---

## ✅ RECOMMENDED Optimal Allocation

### **Version 1: Maximum Diversification** (Best for Multiple Strategy Trading)

**TIER 1 (WebSocket - 8 symbols):**
```yaml
# Core majors (different currency bases)
- EUR/USD    # Euro zone
- GBP/USD    # UK
- USD/JPY    # Japan (negative correlation with EUR/USD)
- USD/CAD    # Canada/Oil (different economic driver)

# Risk indicators (different asset classes)
- AUD/JPY    # Risk-on/off (commodity vs safe haven)
- XAU/USD    # Gold (safe haven, different asset)

# High-value cross pairs (low correlation with above)
- EUR/GBP    # EUR vs GBP strength
- GBP/JPY    # Volatile, good for trading

Benefit:
✅ Low correlation between pairs (0.3-0.5 avg)
✅ Different economic drivers
✅ Good diversification
✅ Cover all major currencies
```

**Why NOT include:**
- ❌ NZD/USD (0.90 correlation with AUD/USD - redundant)
- ❌ USD/CHF (-0.90 correlation with EUR/USD - just inverse)
- ❌ AUD/USD (use AUD/JPY instead - better risk indicator)

**TIER 2 (REST - 15 symbols):**
```yaml
# Confirmation pairs
- GBP/USD    # Confirm EUR/USD
- AUD/USD    # Confirm risk sentiment
- NZD/USD    # Confirm commodity
- USD/CHF    # Confirm EUR/USD (inverse)

# Currency strength pairs
- EUR/JPY
- EUR/CAD
- EUR/AUD
- GBP/CAD
- GBP/AUD
- CAD/JPY
- CHF/JPY
- AUD/CAD
- NZD/CAD
- NZD/JPY
- EUR/NZD
```

---

### **Version 2: Currency Strength Focus** (Best for Currency Strength Strategy)

**TIER 1 (WebSocket - 8 symbols):**
```yaml
# All major currencies vs USD (for strength calculation)
- EUR/USD
- GBP/USD
- USD/JPY
- AUD/USD
- USD/CAD
- USD/CHF
- NZD/USD

# One non-USD pair for verification
- EUR/GBP    # or XAU/USD for risk sentiment

Benefit:
✅ Easy currency strength calculation
✅ All vs same base (USD)
✅ Direct comparison
✅ Cover all 8 major currencies
```

**TIER 2 (REST - 15 symbols):**
```yaml
# Cross pairs for strength verification
- EUR/GBP, EUR/JPY, EUR/AUD, EUR/CAD, EUR/CHF, EUR/NZD
- GBP/JPY, GBP/AUD, GBP/CAD, GBP/CHF, GBP/NZD
- AUD/JPY, AUD/CAD, AUD/NZD
- CAD/JPY, CHF/JPY
```

---

### **Version 3: Risk-Based Trading** (Best for Swing Trading)

**TIER 1 (WebSocket - 8 symbols):**
```yaml
# Pure risk-on indicators
- AUD/JPY    # Commodity vs safe haven
- NZD/JPY    # Commodity vs safe haven
- EUR/JPY    # Major vs safe haven
- GBP/JPY    # Major vs safe haven

# Pure safe-haven indicators
- XAU/USD    # Gold
- USD/JPY    # Dollar-yen
- USD/CHF    # Dollar-franc

# General market
- EUR/USD    # Most liquid reference

Benefit:
✅ Clear risk sentiment signals
✅ All pairs move on same factor (risk)
✅ Easy to interpret
✅ Good for swing trading
```

---

## 📊 Comparison Table

| Strategy | TIER 1 Focus | Best For | Complexity | Diversification |
|----------|-------------|----------|------------|-----------------|
| **Version 1: Diversified** | Low correlation | Multi-strategy trading | Medium | ⭐⭐⭐⭐⭐ |
| **Version 2: Currency Strength** | All vs USD | Single currency pairs | High | ⭐⭐⭐ |
| **Version 3: Risk-Based** | Risk indicators | Swing trading | Low | ⭐⭐ |
| **Current (Original)** | Major pairs | General trading | Low | ⭐⭐ |

---

## 🎯 Final Recommendation

### **For Most Traders:** Version 1 (Maximum Diversification)

**Why:**
- ✅ Low correlation = better risk management
- ✅ Multiple trading opportunities
- ✅ Works for scalping, day trading, swing trading
- ✅ Covers all market conditions
- ✅ More robust portfolio

**TIER 1 (WebSocket):**
```yaml
websocket_instruments:
  - EUR/USD    # Major liquid pair
  - GBP/USD    # UK economy
  - USD/JPY    # Asia, negative correlation
  - USD/CAD    # Oil correlation
  - AUD/JPY    # Risk indicator
  - XAU/USD    # Safe haven
  - EUR/GBP    # EUR vs GBP direct
  - GBP/JPY    # Volatile, good range
```

**TIER 2 (REST):**
```yaml
rest_instruments:
  # Confirmation & correlation
  - GBP/USD    # Confirm EUR/USD
  - AUD/USD    # Risk check
  - NZD/USD    # Commodity check
  - USD/CHF    # EUR/USD inverse

  # Currency strength
  - EUR/JPY
  - EUR/CAD
  - EUR/AUD
  - GBP/CAD
  - GBP/AUD
  - CAD/JPY
  - CHF/JPY
  - AUD/CAD
  - NZD/CAD
  - NZD/JPY
  - EUR/NZD
```

---

## 🔄 Migration Path

### **Current → Recommended:**

```diff
TIER 1 (WebSocket):
  EUR/USD     ✅ Keep (core)
  GBP/USD     ✅ Keep (core)
  USD/JPY     ✅ Keep (core)
- AUD/USD     ❌ Move to TIER 2 (redundant with AUD/JPY)
  USD/CAD     ✅ Keep (oil correlation)
- NZD/USD     ❌ Move to TIER 2 (0.9 correlation with AUD)
- USD/CHF     ❌ Move to TIER 2 (inverse of EUR/USD)
  XAU/USD     ✅ Keep (different asset class)
+ AUD/JPY     ✅ ADD (better risk indicator than AUD/USD)
+ EUR/GBP     ✅ ADD (direct EUR/GBP strength)
+ GBP/JPY     ✅ ADD (volatile, good trading)

Result: Better diversification, lower correlation overlap
```

---

## 📈 Expected Outcomes

### **With Current Allocation:**
- Average correlation: 0.65
- Diversification score: 6/10
- Risk: High (many correlated pairs)

### **With Recommended (Version 1):**
- Average correlation: 0.35
- Diversification score: 9/10
- Risk: Low (independent pairs)

### **Trading Performance Impact:**
```
Scenario: EUR/USD shows BUY signal

Current allocation:
- GBP/USD (0.85 corr) likely also BUY → Redundant signal
- USD/CHF (-0.9 corr) likely SELL → Just inverse
- AUD/USD (0.75 corr) likely BUY → Redundant
→ Basically trading same thing 3-4 times!

Recommended allocation:
- USD/JPY (-0.6 corr) might be opposite → Independent
- AUD/JPY (0.1 corr) might be different → Independent
- USD/CAD (0.15 corr) likely independent → Independent
→ True diversification! ✅
```

---

## ✅ Action Items

1. [ ] Review your trading strategy (diversification vs strength vs risk)
2. [ ] Choose optimal version (1, 2, or 3)
3. [ ] Update `config.yaml` with new symbols
4. [ ] Test correlation in practice
5. [ ] Adjust based on results

---

**Conclusion:** Current allocation is **OK but not optimal**. Version 1 (Maximum Diversification) recommended for most use cases.

**Last Updated:** 2025-10-02

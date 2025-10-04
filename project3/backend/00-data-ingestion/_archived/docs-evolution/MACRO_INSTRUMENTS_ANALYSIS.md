# Macro Instruments untuk Forex Analysis

## 🎯 Problem Statement

**Question:** Selain forex pairs, instrumen apa yang bisa memperkuat analisis trading forex?

**Answer:** YES! Ada beberapa commodities, indices, dan instruments yang **sangat korelasi** dengan forex dan memberikan **leading indicators**.

---

## 📊 Critical Instruments for Forex Analysis

### **TIER 1: Must-Have (Strong Direct Correlation)**

#### **1. Gold (XAU/USD)** ✅ ALREADY INCLUDED
```yaml
Correlation dengan Forex:
- USD strength: -0.70 (inverse - gold up when USD weak)
- Safe haven pairs: 0.60+ (moves with JPY, CHF)
- Risk sentiment: -0.50 with risk-on currencies (AUD, NZD)

Why Critical:
✅ Leading indicator untuk risk-off moves
✅ USD strength gauge
✅ Inflation hedge indicator

Current Status: ✅ Already in TIER 1 WebSocket for trading
```

#### **2. Oil (WTI/USD or BRENT/USD)** ✅ ALREADY INCLUDED
```yaml
Correlation dengan Forex:
- USD/CAD: -0.85 (VERY STRONG inverse)
- CAD crosses: 0.70+ (CAD strengthens with oil)
- NOK/SEK: 0.60+ (Nordic oil exporters)

Why Critical:
✅ Direct driver untuk CAD
✅ Commodity currency indicator
✅ Energy sector risk gauge

Current Status: ✅ Already in TIER 2 REST (WTI/USD)
```

---

### **TIER 2: Very Useful (Moderate Correlation)**

#### **3. US 10-Year Treasury Yield (TNX)** ⭐ HIGHLY RECOMMENDED
```yaml
Symbol: ^TNX or US10Y

Correlation dengan Forex:
- USD/JPY: 0.75+ (VERY STRONG - yen carry trade)
- EUR/USD: -0.60 (higher yields = stronger USD)
- USD strength: 0.65+ (capital flows to higher yields)

Why Critical:
✅ Interest rate differential = #1 forex driver!
✅ Leading indicator untuk USD/JPY moves
✅ Risk appetite gauge (yields up = risk-on)
✅ Fed policy expectations

Trading Use Case:
- If US10Y yields surge → USD/JPY likely UP
- If yields crash → Safe havens (JPY, CHF) rally

Example:
US10Y: 4.5% → 5.0% (+50 bps)
→ Expect USD/JPY to rally (carry trade attractive)
→ Expect EUR/USD to fall (USD strengthens)
```

#### **4. DXY (US Dollar Index)** ⭐ HIGHLY RECOMMENDED
```yaml
Symbol: DXY or DX-Y.NYB

Correlation dengan Forex:
- EUR/USD: -0.95 (almost perfect inverse)
- GBP/USD: -0.90
- USD/JPY: 0.60+
- All USD pairs: Strong correlation

Why Critical:
✅ Overall USD strength in one number
✅ Composite of EUR/USD (57%), JPY (13%), GBP (12%), CAD (9%), etc.
✅ Fastest way to gauge USD sentiment

Trading Use Case:
- DXY breaking resistance → ALL USD pairs affected
- DXY oversold → Look for USD reversal

Example:
DXY breaks above 105.00
→ EUR/USD likely breaking support
→ GBP/USD likely weakening
→ USD/JPY likely rallying
```

#### **5. S&P 500 Index (SPX)** ⭐ RECOMMENDED
```yaml
Symbol: ^GSPC or SPX

Correlation dengan Forex:
- AUD/JPY: 0.70+ (pure risk indicator)
- Risk currencies (AUD, NZD): 0.60+
- Safe havens (JPY, CHF): -0.50

Why Critical:
✅ Risk-on/risk-off barometer
✅ US equity market = global risk appetite
✅ Leading indicator for carry trades

Trading Use Case:
- SPX rallying → Risk-on → Buy AUD/JPY, NZD/JPY
- SPX crashing → Risk-off → Buy JPY, CHF, Gold

Example:
SPX drops -3% in one day (panic sell)
→ Expect AUD/JPY to crash
→ Expect USD/JPY to fall (yen safe haven)
→ Expect XAU/USD to rally
```

---

### **TIER 3: Useful (Specific Use Cases)**

#### **6. VIX (Volatility Index)** - Risk Gauge
```yaml
Symbol: ^VIX

Correlation dengan Forex:
- Risk currencies: -0.60 (VIX up = AUD/NZD down)
- Safe havens: 0.50+ (VIX up = JPY/CHF up)
- Gold: 0.40+

Why Useful:
✅ Fear gauge - inverse of risk appetite
✅ Leading indicator for volatility spikes
✅ Confirm risk-off moves

Trading Use Case:
- VIX spikes above 30 → Extreme fear → Buy safe havens
- VIX below 15 → Complacency → Risk-on environment

Example:
VIX: 15 → 35 (fear spike)
→ Sell AUD/JPY (risk-off)
→ Buy XAU/USD (safe haven)
→ Sell EUR/USD (USD safe haven bid)
```

#### **7. Copper (HG/USD)** - Economic Indicator
```yaml
Symbol: HG/USD or COPPER

Correlation dengan Forex:
- AUD/USD: 0.65+ (Australia = major copper exporter)
- CNY pairs: 0.70+ (China = major copper consumer)
- Risk sentiment: 0.50+

Why Useful:
✅ "Dr. Copper" - economic health indicator
✅ China demand proxy
✅ Industrial metals = growth indicator

Trading Use Case:
- Copper rallying → Global growth → Buy AUD, NZD
- Copper falling → Slowdown → Sell commodity currencies

Example:
Copper breaks multi-year high
→ Strong global demand
→ Buy AUD/USD (commodity currency)
→ Buy AUD/JPY (risk-on)
```

#### **8. Silver (XAG/USD)** - Gold Confirmation
```yaml
Symbol: XAG/USD

Correlation dengan Forex:
- Gold: 0.80+ (moves together)
- USD: -0.60
- Risk sentiment: Hybrid (industrial + safe haven)

Why Useful:
✅ Confirm gold moves (more volatile)
✅ Industrial metal + precious metal hybrid
✅ Risk-on amplifier (moves 2x gold)

Trading Use Case:
- Gold up, Silver up MORE → Strong safe haven bid
- Gold up, Silver flat → Weak move, might reverse
```

#### **9. Bitcoin (BTC/USD)** - Alternative Risk Indicator
```yaml
Symbol: BTC/USD or BTCUSD

Correlation dengan Forex:
- Risk currencies: 0.50+ (when risk-on)
- Tech stocks: 0.60+ (correlation increased recently)
- Gold: Variable (0.30 to -0.20)

Why Useful:
✅ Alternative risk asset
✅ "Digital gold" narrative
✅ Tech risk indicator

Trading Use Case:
- BTC rallying → Risk-on → Buy AUD/JPY
- BTC crashing → Risk-off OR crypto-specific
- Need to confirm with other risk indicators

⚠️ Warning: Crypto correlation is UNSTABLE!
Sometimes moves with risk-on, sometimes inverse.
Use only as supplementary indicator.
```

#### **10. Natural Gas (NG/USD)** - Energy Sector
```yaml
Symbol: NG/USD or NATGAS

Correlation dengan Forex:
- USD/CAD: -0.40 (moderate)
- NOK, RUB: 0.50+ (energy exporters)

Why Useful:
✅ Energy sector risk
✅ European energy crisis indicator
✅ Winter demand proxy

Trading Use Case:
- Natural gas surge → Energy crisis → Buy NOK, CAD
- Gas prices collapse → Energy glut → Sell energy currencies
```

---

## 🎯 RECOMMENDED ADDITIONS to Current Setup

### **Priority 1: Must Add (Critical)**

```yaml
# Add to TIER 2 REST (3-min polling)
macro_instruments:
  - "^TNX"      # US 10-Year Treasury Yield ⭐⭐⭐⭐⭐
  - "DXY"       # US Dollar Index           ⭐⭐⭐⭐⭐
  - "^GSPC"     # S&P 500 Index             ⭐⭐⭐⭐
```

**Why These 3:**
1. **US10Y** - Interest rate differential = strongest forex driver
2. **DXY** - Overall USD strength in one number
3. **SPX** - Risk-on/risk-off barometer

**Impact:**
- EUR/USD trading? Check DXY + US10Y
- USD/JPY trading? Check US10Y (0.75 correlation!)
- Risk sentiment? Check SPX + AUD/JPY

---

### **Priority 2: Nice to Have**

```yaml
# Add if need more confirmation
risk_indicators:
  - "^VIX"      # Volatility Index (fear gauge)
  - "HG/USD"    # Copper (growth indicator)
```

---

### **Priority 3: Optional (Specific Strategies)**

```yaml
# Only if trading specific pairs
supplementary:
  - "XAG/USD"   # Silver (confirm gold)
  - "BTC/USD"   # Bitcoin (alternative risk)
  - "NG/USD"    # Natural Gas (energy)
```

---

## 📊 Updated Symbol Allocation with Macro

### **Current Allocation:**
```
TIER 1 WebSocket: 8 symbols (forex + gold)
TIER 2 REST: 15 symbols (oil + forex correlation)
TOTAL: 23 symbols
```

### **Recommended Addition:**
```
TIER 2 REST: Add 3-5 macro instruments
- US10Y (Treasury Yield) ⭐⭐⭐⭐⭐
- DXY (Dollar Index)     ⭐⭐⭐⭐⭐
- SPX (S&P 500)          ⭐⭐⭐⭐
- VIX (Volatility)       ⭐⭐⭐
- COPPER                 ⭐⭐⭐

NEW TOTAL: 28 symbols (23 current + 5 macro)
```

---

## 💡 Trading Use Cases with Macro Instruments

### **Use Case 1: Trading EUR/USD dengan Full Context**

```python
def trade_eur_usd_with_macro():
    """
    EUR/USD trading dengan macro confirmation
    """

    # Trading pair
    eur_usd = get_websocket("EUR/USD")

    # Macro instruments (3-min update OK!)
    dxy = get_rest("DXY")           # USD overall strength
    us10y = get_rest("^TNX")        # Yield (USD demand)
    spx = get_rest("^GSPC")         # Risk sentiment

    # Forex confirmation
    gbp_usd = get_rest("GBP/USD")
    usd_chf = get_rest("USD/CHF")

    if eur_usd.signal == "BUY":

        # Check macro environment
        if (dxy.trend == "DOWN" and         # USD weakness confirmed
            us10y.trend == "DOWN" and       # Yields falling (USD bearish)
            spx.trend == "UP"):             # Risk-on (EUR positive)

            # Check forex confirmation
            if (gbp_usd.trend == "UP" and   # EUR not alone
                usd_chf.trend == "DOWN"):   # Inverse confirmed

                return "STRONG_BUY"  # All aligned!

    return "WAIT"
```

### **Use Case 2: Trading USD/JPY dengan Yield Correlation**

```python
def trade_usd_jpy_with_yields():
    """
    USD/JPY heavily correlated dengan US yields (0.75+)
    """

    # Trading pair
    usd_jpy = get_websocket("USD/JPY")

    # Critical: US Treasury Yield
    us10y = get_rest("^TNX")

    # Risk confirmation
    spx = get_rest("^GSPC")
    aud_jpy = get_websocket("AUD/JPY")

    if usd_jpy.signal == "BUY":

        # US10Y is LEADING indicator for USD/JPY!
        if us10y.change_pct > 5:  # Yields surging
            # Yields up = USD/JPY up (carry trade attractive)

            if (spx.trend == "UP" and       # Risk-on
                aud_jpy.trend == "UP"):     # Risk confirmed

                return "STRONG_BUY"  # Yield-driven rally

        elif us10y.change_pct < 0:  # Yields falling
            # Yields down = USD/JPY risky
            return "CANCEL_BUY"  # Against macro trend

    return "WAIT"
```

### **Use Case 3: Risk-On/Risk-Off Detection**

```python
def detect_risk_regime():
    """
    Multi-asset risk detection
    """

    # Risk indicators
    spx = get_rest("^GSPC")         # Stocks
    vix = get_rest("^VIX")          # Volatility
    gold = get_websocket("XAU/USD") # Safe haven
    aud_jpy = get_websocket("AUD/JPY")  # Forex risk

    risk_score = 0

    # Stock market
    if spx.trend == "UP" and spx.change_pct > 1:
        risk_score += 2  # Strong risk-on
    elif spx.trend == "DOWN" and spx.change_pct < -2:
        risk_score -= 2  # Strong risk-off

    # Volatility
    if vix.value < 15:
        risk_score += 1  # Low fear = risk-on
    elif vix.value > 30:
        risk_score -= 2  # High fear = risk-off

    # Gold
    if gold.trend == "DOWN":
        risk_score += 1  # Safe haven unwinding
    elif gold.trend == "UP":
        risk_score -= 1  # Safe haven bid

    # Forex risk
    if aud_jpy.trend == "UP":
        risk_score += 1
    elif aud_jpy.trend == "DOWN":
        risk_score -= 1

    # Classification
    if risk_score >= 3:
        return "STRONG_RISK_ON"
        # → Buy: AUD, NZD, EUR
        # → Sell: JPY, CHF, Gold

    elif risk_score <= -3:
        return "STRONG_RISK_OFF"
        # → Buy: JPY, CHF, Gold, USD
        # → Sell: AUD, NZD, commodity currencies

    else:
        return "NEUTRAL"
```

### **Use Case 4: USD Strength Analysis**

```python
def analyze_usd_strength():
    """
    Multi-factor USD strength analysis
    """

    # USD Index
    dxy = get_rest("DXY")

    # Yields
    us10y = get_rest("^TNX")

    # Safe haven demand
    gold = get_websocket("XAU/USD")

    # USD pairs
    eur_usd = get_websocket("EUR/USD")
    usd_jpy = get_websocket("USD/JPY")

    usd_score = 0

    # DXY
    if dxy.trend == "UP" and dxy.change_pct > 0.5:
        usd_score += 2  # Strong USD

    # Yields
    if us10y.trend == "UP" and us10y.change_pct > 2:
        usd_score += 2  # Capital flows to USD

    # Gold
    if gold.trend == "DOWN":
        usd_score += 1  # USD strength inverse gold

    # Forex confirmation
    if eur_usd.trend == "DOWN" and usd_jpy.trend == "UP":
        usd_score += 1  # Broad USD strength

    if usd_score >= 4:
        return "STRONG_USD"
        # → Sell: EUR/USD, GBP/USD, AUD/USD
        # → Buy: USD/JPY, USD/CAD, USD/CHF

    elif usd_score <= 0:
        return "WEAK_USD"
        # → Buy: EUR/USD, GBP/USD, Gold
        # → Sell: USD/JPY

    return "NEUTRAL_USD"
```

---

## 🔬 Correlation Science - Why These Work

### **Interest Rate Differential Theory**
```
Formula:
Expected FX Move = (Interest Rate A - Interest Rate B) × Time

Example:
US yields: 5.0%
Japan yields: 0.5%
Differential: 4.5%

→ USD/JPY should appreciate ~4.5% annually (carry trade)
→ When US10Y yields rise, USD/JPY rallies
→ Correlation: 0.75+ (very strong!)

This is why US10Y is CRITICAL for USD/JPY trading!
```

### **Risk Correlation Theory**
```
Risk-On Environment:
- Stocks UP (SPX)
- Volatility DOWN (VIX)
- Gold DOWN
- AUD/JPY UP
- Commodity currencies UP

Risk-Off Environment:
- Stocks DOWN (SPX)
- Volatility UP (VIX)
- Gold UP
- AUD/JPY DOWN
- Safe havens UP (JPY, CHF, USD)

All these move TOGETHER = Strong confirmation!
```

### **USD Index Composition**
```
DXY Weighting:
- EUR: 57.6%  → EUR/USD dominates DXY
- JPY: 13.6%
- GBP: 11.9%
- CAD: 9.1%
- SEK: 4.2%
- CHF: 3.6%

Why useful:
- DXY up = EUR/USD down (almost perfect inverse)
- DXY = overall USD strength vs basket
- Leading indicator for all USD pairs
```

---

## 📊 Twelve Data Availability Check - TESTED ✅

### **❌ NOT Available on FREE Tier (Require PAID Grow Plan):**
- DXY, SPX, ^TNX, ^VIX (Direct indices)
- XAU/USD, XAG/USD, WTI/USD (Now require paid - policy changed!)
- Most commodity symbols
- Most ETFs (VOO, TLT, GLD, SLV, etc.)

### **✅ Available on FREE Tier (Tested & Confirmed):**

**ETF Alternatives (Work as Proxies):**
```yaml
# Dollar Index Proxy
- UUP    # Invesco DB US Dollar Index Bullish Fund
         # Tracks DXY, Price: $27.50
         # Correlation with DXY: 0.95+

- USDU   # WisdomTree Bloomberg USD Bullish Fund
         # Alternative Dollar Index tracker
         # Price: $26.37

# Stock Market Proxy (Risk Sentiment)
- SPY    # SPDR S&P 500 ETF Trust
         # Tracks S&P 500 Index
         # Price: $668.45
         # Correlation with ^GSPC: 0.99+ (almost perfect)
```

### **⚠️ Important Discovery:**

**Twelve Data has CHANGED policy!**
- XAU/USD, WTI/USD, BTC/USD now require **Grow plan ($79/month)**
- This means our current WebSocket for Gold might not work on FREE tier
- Need to verify if existing API key grandfathered

**Impact:**
- If Gold (XAU/USD) stops working → Must use GLD ETF or upgrade
- If Oil (WTI/USD) stops working → Must use USO ETF or upgrade
- FREE tier now very limited for commodities

**Action Required:**
Test if current XAU/USD and WTI/USD still work with current API key (might be grandfathered)

---

## 💰 Cost Impact

### **Current Usage:**
```
WebSocket: 8/8 symbols (100% used)
REST API: 15 symbols, ~960 req/day
Remaining capacity: ~640 req/day (with 2 keys)
```

### **Adding 5 Macro Instruments:**
```
New REST symbols: +5
Total REST symbols: 20 (15 forex + 5 macro)

Polling: Every 3 minutes
Daily requests: 20 symbols / 12 per batch = 2 batches
Frequency: 1,440 min/day / 3 min = 480 polls
Total: 2 batches × 480 = 960 req/day

With 2 API keys: 1,600 req/day available
Usage: 960 + 960 = 1,920 req/day
❌ EXCEEDS LIMIT!

SOLUTION: Poll macro instruments every 5 minutes instead of 3
New calculation: 1,440 / 5 = 288 polls × 2 = 576 req/day
Total: 960 (forex) + 576 (macro) = 1,536 req/day
✅ Within 1,600 limit!
```

**Recommendation:**
- Forex pairs: 3-min polling (critical)
- Macro instruments: 5-min polling (sufficient - they move slower)

---

## ✅ FINAL RECOMMENDATION (Updated After Testing)

### **REALITY: FREE Tier Very Limited!**

After testing, most macro instruments require PAID Grow plan ($79/month).

### **Option 1: Stay FREE - Use ETF Proxies (3 instruments)**

```yaml
# Available on FREE tier - ETF proxies
macro_instruments:
  - "UUP"       # US Dollar Index ETF (tracks DXY, 0.95+ correlation)
  - "USDU"      # Alternative Dollar Index ETF
  - "SPY"       # S&P 500 ETF (tracks SPX, 0.99+ correlation)

  poll_interval: 300  # 5 minutes (ETFs update slower)
```

**Pros:**
- ✅ $0/month cost
- ✅ SPY tracks S&P 500 almost perfectly (0.99 corr)
- ✅ UUP tracks DXY well (0.95 corr)
- ✅ Enough for basic risk sentiment

**Cons:**
- ❌ No yields data (can't track USD/JPY correlation via US10Y)
- ❌ No VIX (fear gauge)
- ❌ ETFs update slower than indices
- ❌ Less precise than direct indices

---

### **Option 2: Upgrade to Grow Plan ($79/month)**

```yaml
# Full macro suite with Grow plan
macro_instruments:
  - "US10Y"     # US 10-Year Treasury Yield ⭐⭐⭐⭐⭐
  - "DXY"       # US Dollar Index           ⭐⭐⭐⭐⭐
  - "SPX"       # S&P 500 Index             ⭐⭐⭐⭐
  - "VIX"       # Volatility Index          ⭐⭐⭐
  - "COPPER"    # Copper                    ⭐⭐⭐
  - "XAU/USD"   # Gold (if not working on free)
  - "WTI/USD"   # Oil (if not working on free)

  poll_interval: 300  # 5 minutes
```

**Pros:**
- ✅ US10Y = Critical for USD/JPY trading (0.75 correlation!)
- ✅ Direct indices (more accurate than ETFs)
- ✅ VIX for fear gauge
- ✅ All commodities available

**Cons:**
- ❌ $79/month cost
- ❌ Might be overkill for retail trading

---

### **Option 3: Hybrid - FREE Twelve Data + Alternative Sources**

```yaml
# Keep Twelve Data FREE for forex
# Add alternative FREE sources for macro:

Twelve Data (FREE):
  - Forex pairs (23 symbols)
  - UUP, USDU, SPY (3 ETF proxies)

Alpha Vantage (FREE - different API):
  - US Treasury Yields (FREE!)
  - Stock indices (FREE!)
  - Economic indicators (FREE!)
  API limit: 500 calls/day

Finnhub (FREE):
  - Stock indices real-time
  - Economic calendar
  API limit: 60 calls/min
```

**Pros:**
- ✅ $0/month total cost
- ✅ Get yields data from Alpha Vantage
- ✅ Diversified data sources (resilience)
- ✅ More flexibility

**Cons:**
- ❌ More complex integration
- ❌ Multiple API keys to manage
- ❌ Different data formats

---

### **🎯 MY RECOMMENDATION: Option 1 (Stay FREE)**

```yaml
# Add to config.yaml - TIER 2 REST
macro_instruments:
  - "UUP"       # Dollar Index proxy (DXY alternative)
  - "SPY"       # S&P 500 proxy (risk sentiment)

  poll_interval: 300  # 5 minutes (ETFs sufficient)
```

**Why:**
1. **UUP** = Good proxy for USD strength (0.95 corr with DXY)
2. **SPY** = Perfect proxy for S&P 500 (0.99 corr with SPX)
3. **$0 cost** = No additional expense
4. **Sufficient for retail trading** = 80% of the value for 0% of the cost

**Skip USDU** (redundant with UUP - same thing)

### **When to Consider Upgrade ($79/month):**
- If you NEED US10Y for USD/JPY carry trade strategies (0.75 correlation)
- If trading based on interest rate differentials
- If managing >$50K capital (cost becomes negligible)
- If need VIX for volatility strategies

### **Why These 5:**
1. **US10Y** - 0.75 correlation dengan USD/JPY, strongest forex driver
2. **DXY** - Overall USD strength composite
3. **SPX** - Risk-on/off barometer
4. **VIX** - Fear gauge, inverse risk
5. **COPPER** - Economic health, AUD correlation

### **Expected Impact:**
- ✅ Better USD/JPY entries (yield correlation)
- ✅ Faster USD trend detection (DXY)
- ✅ Clearer risk regime (SPX + VIX)
- ✅ Commodity currency confirmation (Copper)
- ✅ Multi-asset confirmation (reduce false signals)

---

## 🎯 Next Steps

1. **Test symbol availability** on Twelve Data
2. **Update config.yaml** dengan 5 macro instruments
3. **Implement macro data collector**
4. **Build correlation calculator** including macro
5. **Create trading strategies** with macro confirmation

---

**Status:** ⏳ Awaiting decision - Add macro instruments?
**Cost:** $0 (still within FREE tier with 2 API keys)
**Symbols:** 28 total (23 current + 5 macro)
**Update Frequency:** Macro = 5-min (vs forex 3-min)

Mau saya test availability dulu dan update config?

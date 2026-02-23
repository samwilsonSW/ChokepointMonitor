# Financial Analysis Roadmap

> This is a living document for the long-term evolution of Chokepoint Monitor's financial analysis capabilities. No deadlines, no pressure — just a map of possibilities to explore when curiosity strikes.

---

## Philosophy

This project grows organically. Features get built when they become interesting, not because they're "required." The goal is a system that can surprise you with insights years from now.

---

## Option A: Conflict → Price Spike (Event Studies)

**Core Question**: When a major conflict event occurs near a chokepoint, what happens to prices?

### Implementation Ideas
- [ ] Manual event tagging interface — mark significant incidents from ACLED data
- [ ] Event window analysis — price movement [-7d, +7d] around tagged events
- [ ] Average response profiles — "typical" price impact by event type
- [ ] Outlier detection — events that *didn't* move markets (often more interesting)

### Data Needed
- Tagged event library (manual at first, maybe automated later)
- Price history aligned to event timestamps
- Baseline volatility (to distinguish "big move" from "normal noise")

### Future Enhancements
- [ ] Actor-specific responses (Houthi vs state military vs non-state actors)
- [ ] Severity scoring taxonomy (what makes an event "major?")
- [ ] Seasonal adjustment (conflicts during low-volume periods hit harder)

---

## Option B: Risk Premium Tracking (Chronic Risk)

**Core Question**: Does sustained background conflict correlate with sustained price elevation?

### Implementation Ideas
- [ ] Rolling correlation windows — 30d, 90d, 1yr correlations
- [ ] Conflict intensity indices — aggregate events/fatalities into daily scores
- [ ] Baseline deviation — how much above "peace time" prices are we?
- [ ] Regime detection — identifying structural breaks (new normal vs temporary spike)

### Data Needed
- Daily conflict intensity metrics per chokepoint
- Long price histories (2+ years minimum)
- Control variables (global supply, inventories, VIX)

### Future Enhancements
- [ ] Granger causality testing — does conflict lead prices or vice versa?
- [ ] Vector autoregression (VAR) models — multivariate time series
- [ ] Machine learning for non-linear relationships

---

## Option C: Tanker Stock Alpha (Equity Focus)

**Core Question**: Do tanker companies (FRO, STNG, etc.) outperform when route risk increases?

### Implementation Ideas
- [ ] Relative performance vs S&P 500 (are they beating the market?)
- [ ] Volatility expansion — do they become more volatile during crises?
- [ ] Peer comparison — which tanker companies are most sensitive to which chokepoints?
- [ ] Dividend/policy changes — do companies adjust payouts during high-risk periods?

### Data Needed
- Equity prices + volume
- Market cap and fleet composition data
- Sector indices for relative performance
- Earnings call transcripts (sentiment analysis potential)

### Future Enhancements
- [ ] Options market data — implied volatility as fear gauge
- [ ] Short interest tracking — are hedge funds betting against tankers during crises?
- [ ] Fleet positioning — where are their ships physically located? (AIS correlation)

---

## Option D: The Unified Layer (All of the Above)

**Core Question**: Can we build a composite "Chokepoint Risk Signal" that incorporates all dimensions?

### Vision
A single dashboard showing:
- Conflict intensity (from ACLED)
- Price responses (oil, tanker equities)
- Shipping costs (tanker rates, insurance)
- Market sentiment (news, VIX)
- Physical vessel movements (AIS divergences)

All aligned temporally and spatially. The goal isn't prediction — it's *understanding*.

### Long-term Architecture
```
┌─────────────────────────────────────────┐
│  Layer 4: Visualization & Interface    │
│  - Time series with event markers       │
│  - Correlation matrices                 │
│  - Interactive event drill-downs        │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│  Layer 3: Analysis Engine              │
│  - Event study calculations             │
│  - Rolling correlations                 │
│  - Anomaly detection                    │
│  - Attribution modeling                 │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│  Layer 2: Event Library                │
│  - Manually tagged significant events   │
│  - Automated event detection (future)   │
│  - Severity and impact classification   │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│  Layer 1: Data Ingestion               │
│  - ACLED conflict data ✅               │
│  - Financial prices (yfinance) 🔄       │
│  - Tanker rates (future)                │
│  - AIS vessel tracking (future)         │
│  - News/sentiment (future)              │
│  - Insurance/war risk (future)          │
└─────────────────────────────────────────┘
```

---

## Data Sources to Explore

### Immediate (Free/Easy)
- [x] Yahoo Finance (yfinance) — CL=F, BZ=F, FRO, STNG, NG=F
- [ ] FRED (Federal Reserve) — DXY, VIX, various economic indicators
- [ ] EIA — US inventory data, production stats

### Short-term (Some effort)
- [ ] Tanker rates — Baltic Exchange (expensive), Shipfix (freemium?), broker reports
- [ ] Brent-WTI spread — easily calculated from existing data
- [ ] Regional crude differentials — Dubai, Oman, Urals (Argus Media, Platts — pricey)

### Long-term (Complex/Expensive)
- [ ] AIS vessel tracking — MarineTraffic, Vesselfinder, Spire (API access)
- [ ] Port congestion — PortSEnergy, Lloyd's List, manual tracking
- [ ] War risk insurance — Lloyd's Market Association (LMA), limited public data
- [ ] News sentiment — Bloomberg, Reuters, RavenPack (institutional)
- [ ] Satellite imagery — Planet Labs, Sentinel (ship detection, port monitoring)

---

## Analysis Techniques to Learn

### Statistical
- [ ] Event study methodology (abnormal returns calculation)
- [ ] Rolling window correlations
- [ ] Granger causality testing
- [ ] Cointegration analysis (long-term equilibrium relationships)

### Machine Learning (Future)
- [ ] Feature engineering from conflict data
- [ ] Anomaly detection in price movements
- [ ] NLP for news/event extraction
- [ ] Time series forecasting (prophet, ARIMA, LSTM)

### Visualization
- [ ] Multi-axis time series (price + conflict intensity)
- [ ] Heatmaps (correlation matrices)
- [ ] Network graphs (shipping routes + conflict zones)

---

## Wild Ideas (Maybe Never, Maybe Someday)

- [ ] **Automated event detection** — ML model that flags "significant" ACLED events without manual tagging
- [ ] **Predictive modeling** — "Given current conflict levels, 30% chance of >5% Brent spike this week"
- [ ] **Alternative data fusion** — Satellite imagery of tanker queues, social media sentiment from port cities
- [ ] **Options market analysis** — Skew, term structure as fear indicators
- [ ] **Counterfactual simulation** — "What if Hormuz closed for 30 days?" (scenario modeling)
- [ ] **Real-time alerting** — Webhook notifications when correlation patterns shift
- [ ] **Research publication** — Academic paper on conflict-commodity relationships

---

## Immediate Next Steps (No Rush)

### Foundation Phase (Current)
1. **Backfill financial data** — 2 years daily OHLCV for all tickers
2. **Normalize schema** — Rename `Financial-Data-By-Date-And-Ticker` to `financial_prices_daily`
3. **Build `/prices` endpoint** — Serve time-series data to frontend
4. **Create `events_library` table** — Schema for manually tagged significant events

### Exploration Phase (Next)
5. **Manual event tagging** — Pick 10-15 major Hormuz/Bab el-Mandeb incidents, tag in database
6. **Event window prototype** — Python script to calculate price changes around tagged events
7. **Simple correlation calculation** — Rolling 30d correlation between conflict intensity and prices

### Integration Phase (Later)
8. **Frontend financial panel** — Time-series chart with conflict event markers
9. **Correlation results storage** — Save calculated correlations for historical tracking
10. **Interactive exploration** — Let users select date ranges, tickers, lag windows

---

## Guiding Questions

When deciding what to build next, ask:

1. **What am I curious about right now?** (Follow the curiosity)
2. **What data do I already have that I'm not using?** (Low-hanging fruit)
3. **What would surprise me if it were true?** (Hypothesis generation)
4. **What would I want to show someone in 5 years?** (Long-term value)
5. **What's the smallest version of this that still teaches me something?** (Scope control)

---

## Notes & Discoveries

*Use this space to jot down insights, dead ends, and unexpected findings as you explore.*

---

*Last updated: 2026-02-21*
*Document status: Living — edit freely as the project evolves*

# Financial Correlation Roadmap

> Complete implementation plan for oil price + conflict correlation analysis
> Created: 2026-03-09
> Updated: 2026-03-10

## Architecture Decision

**Data Fetch Strategy:** Fetch all data at page load (~3KB), filter client-side
- Max ~4 years × 52 weeks × 15 tickers = ~3,120 rows
- Single API call on mount, no repeated calls on slider changes
- Client filters by date range and ticker

**UI Layout:** 50/50 split view (map left, financial panel right)
- Desktop (>1024px): Side-by-side, resizable
- Tablet/Mobile (<1024px): Bottom drawer fallback
- Toggle modes: Default 50/50, Focus 75/25, Analysis 25/75

---

## Phase 1: Data Foundation ✅ COMPLETE

### 1.1 Weekly Aggregation View
**Status:** ✅ DONE
**Effort:** Low

Created `chokepoint_weekly_analysis` view joining weekly conflict aggregates with price data:
- Aligned to ACLED week boundaries (Sunday → Saturday, labeled by Saturday date)
- Financial aggregates: open, close, high, low, avg, volatility %, weekly change %
- Conflict aggregates: regional breakdown (Red Sea, Persian Gulf, Malacca) + totals
- Status flag: `events` / `none` / `pending` for ACLED latency handling

### 1.2 API Endpoint
**Status:** ✅ DONE
**Effort:** Low

Created `/weekly-analysis` endpoint:
- Returns all data (no date filtering — client handles it)
- ~100KB JSON max (4 years × 52 weeks × 15 tickers)
- Response includes: data array, count, ticker list, date range

---

## Phase 2: Frontend Components

### 2.1 Chart Visualization Design ⭐ PRIORITY #1
**Status:** 🔄 IN PROGRESS
**Effort:** Medium
**Depends on:** User decision

**Decision needed:** How to display conflict data alongside price?

Options to evaluate:
- **Dual-axis line chart:** Price on left Y, conflict intensity on right Y
- **Overlay bars:** Price line + conflict count as bars behind/on top
- **Separate mini charts:** Price chart + conflict sparkline stacked
- **Event markers:** Price line with vertical markers at conflict weeks

Considerations:
- How many tickers visible at once? (Probably just 1 selected)
- Should conflict be total events, fatalities, or regional subset?
- Color coding by region?
- Hover behavior: show both price and conflict data?

**Task:** Sketch options, pick one, then build.

### 2.2 Financial Panel Container
**Status:** ⏳ TODO
**Effort:** Medium
**Depends on:** 2.1

```
FinancialPanel.svelte      # Main container
├── ChartContainer.svelte  # Holds the chosen chart type
├── TickerSelector.svelte  # Dropdown to pick USO/CL=/BZ=/etc
├── RegionFilter.svelte    # Toggle: All regions vs Hormuz-only vs etc
└── CorrelationStats.svelte # r-value display
```

**Tasks:**
- [ ] Create `FinancialPanel.svelte` container
- [ ] Add to 50/50 split layout with map
- [ ] Wire to date slider store for reactive filtering
- [ ] Add ticker selector dropdown

### 2.3 Data Store & Client-Side Filtering
**Status:** ⏳ TODO
**Effort:** Low
**Depends on:** None

**Svelte store setup:**
```javascript
// stores/financialData.js
export const weeklyData = writable([]);
export const filteredData = derived([weeklyData, dateRange], ...);
export const selectedTicker = writable('USO');
export const selectedRegion = writable('all'); // all | red_sea | persian_gulf | malacca
```

**Tasks:**
- [ ] Fetch `/weekly-analysis` on app mount
- [ ] Client-side filter by date range when slider changes
- [ ] Client-side filter by ticker when selector changes
- [ ] Client-side filter by region (all events vs regional subset)

### 2.4 Correlation Calculation
**Status:** ⏳ TODO
**Effort:** Low
**Depends on:** 2.3

Client-side Pearson correlation from filtered data:
```javascript
// utils/correlation.js
export function pearsonCorrelation(x, y) { ... }

// Usage:
const r = pearsonCorrelation(
  filteredData.map(d => d.total_events),
  filteredData.map(d => d.avg_close)
);
```

**Tasks:**
- [ ] Implement `pearsonCorrelation()` utility
- [ ] Display r-value with interpretation (weak/moderate/strong)
- [ ] Show sample size ("n = 52 weeks")

---

## Phase 3: Analysis Features

### 3.1 Anomaly Detection
**Status:** ⏳ TODO
**Effort:** Medium
**Depends on:** 2.4

Identify interesting patterns:
- "High conflict, flat prices" → Market discounting risk
- "Price spike, no conflict" → Check for other news (OPEC, inventory reports)
- "Correlation breakdown" → Relationship changed

### 3.2 Event Study Reports
**Status:** ⏳ TODO
**Effort:** High
**Depends on:** 2.1

For major events, generate automatic analysis:
- Pre-event price trend
- Post-event price movement
- Comparison to similar historical events
- "Market reacted / didn't react" summary

### 3.3 Predictive Indicators (Stretch)
**Status:** ⏳ TODO
**Effort:** High

Build simple leading indicators:
- "Days since last Hormuz incident" → probability indicator
- Conflict intensity trend → directional signal
- Composite risk score combining multiple factors

---

## Phase 4: Polish & Integration

### 4.1 Responsive Refinements
**Status:** ⏳ TODO
**Effort:** Low

- Mobile: Bottom drawer with swipe-up handle
- Tablet: Collapsible side panel
- Desktop: Draggable split width

### 4.2 Performance Optimization
**Status:** ⏳ TODO
**Effort:** Low

- Data already pre-aggregated (weekly)
- Client-side filtering is instant
- Consider memoizing correlation calc if expensive

### 4.3 Data Quality Dashboard
**Status:** ⏳ TODO
**Effort:** Low

Hidden/admin view showing:
- Last data update timestamps
- Missing data gaps
- API response times

---

## Current Priorities (Ordered)

| Order | Task | Status | Why |
|-------|------|--------|-----|
| 1 | Chart visualization design | 🔄 IN PROGRESS | Blocks everything downstream |
| 2 | Financial panel container | ⏳ TODO | Structure for chart |
| 3 | Data store & filtering | ⏳ TODO | Reactive data flow |
| 4 | Correlation calculation | ⏳ TODO | Core value prop |

---

## Technical Decisions

**Data Volume:**
- Max: ~3,120 rows (4 years × 52 weeks × 15 tickers)
- Actual: ~520 rows (current 4 years × 5 tickers)
- Fetch once, filter client-side ✅

**Correlation Interpretation:**
- |r| < 0.3: Weak / No correlation
- 0.3 ≤ |r| < 0.7: Moderate correlation
- |r| ≥ 0.7: Strong correlation

**Week Alignment:**
- ACLED: Sunday → Saturday, labeled by Saturday date
- Financial data aggregated to same boundaries
- View uses `acled_week` as join key

---

## API Reference

**`GET /weekly-analysis`**

Returns all weekly data. No query params.

```json
{
  "data": [
    {
      "acled_week": "2024-01-06",
      "ticker": "USO",
      "weekly_open": 71.24,
      "weekly_close": 73.19,
      "weekly_high": 73.52,
      "weekly_low": 69.16,
      "avg_close": 71.52,
      "range_volatility_pct": 6.30,
      "weekly_change_pct": 2.74,
      "red_sea_events": 5,
      "red_sea_fatalities": 12,
      "persian_gulf_events": 3,
      "persian_gulf_fatalities": 8,
      "malacca_events": 0,
      "malacca_fatalities": 0,
      "total_events": 8,
      "total_fatalities": 20,
      "conflict_status": "events"
    },
    ...
  ],
  "count": 520,
  "tickers": ["USO", "CL=F", "BZ=F", "FRO", "STNG"],
  "date_range": {
    "min": "2024-01-06",
    "max": "2026-02-28"
  }
}
```

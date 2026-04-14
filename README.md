# Chokepoint Monitor

**🌐 Live Demo: https://chokepointmonitor.com**

[![Render](https://img.shields.io/badge/deployed%20on-Render-46E3B7.svg)](https://render.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Svelte](https://img.shields.io/badge/Svelte-FF3E00.svg?logo=svelte&logoColor=white)](https://svelte.dev/)
[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E.svg?logo=supabase&logoColor=white)](https://supabase.com/)

> **Portfolio Project**: A full-stack geospatial risk visualization system tracking global conflict events near critical maritime oil chokepoints. Built to demonstrate senior-level systems thinking, data pipeline architecture, and real-time geospatial analytics.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Live Demo](#live-demo)
- [Architecture](#architecture)
- [Technical Stack](#technical-stack)
- [Data Pipeline](#data-pipeline)
- [Key Features](#key-features)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [What I Learned](#what-i-learned)

---

## Overview

Chokepoint Monitor visualizes the relationship between geopolitical conflict and energy market volatility. The system tracks three critical maritime chokepoints:

| Chokepoint | Location | Daily Oil Flow | Strategic Importance |
|------------|----------|----------------|---------------------|
| **Strait of Hormuz** | Persian Gulf | ~21 million barrels | Primary route for Middle East oil exports |
| **Bab el-Mandeb** | Red Sea/Gulf of Aden | ~5 million barrels | Connects Mediterranean via Suez Canal |
| **Strait of Malacca** | Southeast Asia | ~16 million barrels | Primary route for Asian energy imports |

The application correlates armed conflict events (ACLED data) with financial market data (crude oil futures, tanker stocks) to surface potential risk signals.

---

## Live Demo

**🌍 https://chokepointmonitor.com**

### What to Try

1. **Explore the Heatmap**: Navigate to the Persian Gulf or Red Sea — darker clusters indicate higher conflict density
2. **Use the Date Slider**: Drag the range handles to filter events by time period (defaults to YTD, expands to 3-year history)
3. **Click a Geofence**: Click any chokepoint polygon to see conflict events within that region
4. **Open Insights Panel**: Click the "Insights" button to view financial correlation charts
5. **Select Different Tickers**: Try `CL=F` (WTI Crude), `BZ=F` (Brent), `FRO` (Frontline tankers), or `STNG` (Scorpio tankers)

---

## Architecture

### High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA SOURCES                                    │
├─────────────────┬─────────────────────────────┬─────────────────────────────┤
│   ACLED API     │      Yahoo Finance          │    GDELT (designed)         │
│   (Conflict     │      (Oil futures,          │    (News sentiment          │
│    events)      │       tanker stocks)        │     analysis)               │
└────────┬────────┴──────────────┬──────────────┴──────────────┬──────────────┘
         │                       │                             │
         ▼                       ▼                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA INGESTION LAYER                                 │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌────────────────────┐ │
│  │ import_acled_xlsx.py │  │ import_yfinance_     │  │ ingest_gdelt.py    │ │
│  │ (Batch geocoding,    │  │    data.py           │  │ (BigQuery, on ice) │ │
│  │  deduplication)      │  │ (Daily OHLCV fetch)  │  │                    │ │
│  └──────────┬───────────┘  └──────────┬───────────┘  └──────────┬─────────┘ │
└─────────────┼─────────────────────────┼─────────────────────────┼───────────┘
              │                         │                         │
              ▼                         ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SUPABASE (PostgreSQL + PostGIS)                      │
│  ┌────────────────────────┐  ┌────────────────────────────────────────────┐ │
│  │ conflict_events_       │  │ financial_prices_daily                     │ │
│  │   enriched             │  │ (ticker, date, OHLCV)                      │ │
│  │ (ACLED + geocoded)     │  └────────────────────────────────────────────┘ │
│  └──────────┬─────────────┘                                                   │
│             │                                                                 │
│  ┌──────────▼─────────────┐  ┌────────────────────────────────────────────┐ │
│  │ chokepoint_regions     │  │ weekly_analysis VIEW                       │ │
│  │ (GeoJSON polygons,     │  │ (JOIN conflicts + financials + aggregation)│ │
│  │  center points)        │  └────────────────────────────────────────────┘ │
│  └──────────┬─────────────┘                                                   │
│             │         ┌──────────────────────────────────────────────────┐   │
│             └────────►│ region_conflict_stats() RPC function             │   │
│                       │ (PostGIS ST_Contains for geofence queries)       │   │
│                       └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         API LAYER (FastAPI + Python)                         │
│                                                                              │
│  GET /conflicts              → GeoJSON conflict events with date filtering   │
│  GET /chokepoint-regions     → GeoJSON polygons for map rendering            │
│  GET /chokepoint-metrics     → Aggregated stats per region (count, risk)     │
│  GET /weekly-analysis        → Joined financial + conflict time series       │
│                                                                              │
│  ThreadPoolExecutor for async Supabase queries (sync client in async loop)   │
└─────────────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Svelte 5 + MapLibre)                       │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  Data Stores (Svelte stores)                                         │   │
│  │  ├── conflictStore: Two-phase loading (YTD → full history)           │   │
│  │  ├── financialStore: Weekly analysis with ticker/region filters      │   │
│  │  └── Derived stores: Recency calc, correlation stats, geofence metrics│  │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  Map Layers                                                          │   │
│  │  ├── Heatmap (recency-weighted density)                              │   │
│  │  ├── Conflict points (clickable clusters)                            │   │
│  │  └── Geofence polygons (risk-colored overlays)                       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  UI Components                                                       │   │
│  │  ├── RangeSlider (custom quarterly-tick date selector)               │   │
│  │  ├── FinancialDrawer (D3.js charts, correlation analysis)            │   │
│  │  └── ConflictPopup (event detail drawer)                             │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow: Conflict Event → Map Visualization

```
ACLED CSV/XLSX
     │
     ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Geocode locations│────►│ Supabase insert │────►│ PostGIS indexing│
│ (lat/lon cleanup)│     │ (batch upsert)  │     │ (spatial index) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                          │
                    ┌──────────────────────────────────────┘
                    ▼
           ┌─────────────────┐
           │ API: /conflicts │◄──── Date range query param
           │ (async handler) │
           └────────┬────────┘
                    │ GeoJSON FeatureCollection
                    ▼
           ┌─────────────────┐
           │ conflictStore   │◄──── Two-phase load:
           │ (Svelte store)  │      1. YTD (fast)
           │                 │      2. Full history (background)
           └────────┬────────┘
                    │
         ┌─────────┼─────────┐
         ▼         ▼         ▼
    ┌────────┐ ┌────────┐ ┌────────┐
    │ Heatmap│ │ Points │ │Geofence│
    │ Layer  │ │ Layer  │ │Metrics │
    └────────┘ └────────┘ └────────┘
```

### Client-Side Recency Calculation

A key architectural decision: **recency weighting happens client-side**, not server-side.

```
Server: Returns raw conflict events (no recency field)
              │
              ▼
Client: ┌─────────────────────────────────────────┐
        │ filteredDataWithRecency (derived store) │
        │                                         │
        │ For each event:                         │
        │   recency = (event_date - slider_start) │
        │             / (slider_end - slider_start)│
        │                                         │
        │ Result: 0.0 (oldest) → 1.0 (newest)     │
        └─────────────────────────────────────────┘
              │
              ▼
        Heatmap opacity/weight
        (newer events = more visible)
```

**Why this matters**: The heatmap visual density stays consistent regardless of how much historical data is loaded. Whether viewing 3 months or 3 years, the relative weighting within the selected range remains accurate.

---

## Technical Stack

### Backend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **API Framework** | FastAPI | Async Python API with auto-generated OpenAPI docs |
| **Database** | Supabase (PostgreSQL 15+) | Managed Postgres with PostGIS extensions |
| **Geospatial** | PostGIS | Spatial queries (`ST_Contains`, bounding box indexes) |
| **Data Ingestion** | Python + yfinance | ACLED pipeline + daily financial updates |
| **Task Scheduling** | GitHub Actions | Daily 5 PM CST financial data fetch |
| **Server** | Uvicorn | ASGI server for FastAPI |

### Frontend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | Svelte 5 | Reactive UI with compiled components (no VDOM) |
| **Build Tool** | Vite | Fast dev server, optimized production builds |
| **Maps** | MapLibre GL | Open-source Mapbox alternative for WebGL rendering |
| **Styling** | Skeleton UI + Tailwind | Pre-built Svelte components, utility CSS |
| **Charts** | D3.js | Custom financial correlation visualizations |
| **State** | Svelte Stores | Reactive data flow without external state library |

### Infrastructure

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Hosting** | Render | Single service (API + static files), Pro tier |
| **Database** | Supabase | Managed PostgreSQL with row-level security |
| **CDN** | Render + MapTiler | Static assets + map tile delivery |
| **CI/CD** | GitHub Actions | Automated daily data updates |

---

## Data Pipeline

### 1. Conflict Data (ACLED)

**Source**: [Armed Conflict Location & Event Data Project](https://acleddata.com/)

```python
# Pipeline: backend/import_acled_xlsx.py
ACLED XLSX → Geocode locations → Supabase upsert → PostGIS indexing

Key transformations:
- Normalize location strings to lat/lon
- Deduplicate by ACLED event ID
- Enrich with chokepoint proximity flags
- Aggregate to weekly buckets for analysis
```

**Schema**: `conflict_events_enriched`
- `acled_id` (unique identifier)
- `week` (ISO week date)
- `country`, `country_admin` (location hierarchy)
- `latitude`, `longitude` (geocoded coordinates)
- `event_type`, `sub_event_type` (violence categorization)
- `fatalities`, `no_of_events` (impact metrics)

### 2. Financial Data (Yahoo Finance)

**Source**: yfinance Python library

```python
# Pipeline: backend/import_yfinance_data.py + GitHub Actions
Tickers: ["CL=F", "BZ=F", "FRO", "STNG", "NG=F"]
        │      │      │      │       │
        │      │      │      │       └─ Natural Gas futures
        │      │      │      └─ Scorpio Tankers
        │      │      └─ Frontline Tankers
        │      └─ Brent Crude
        └─ WTI Crude

Schedule: Daily at 5:00 PM CST (after market close)
```

**Schema**: `financial_prices_daily`
- `date`, `ticker` (composite primary key)
- `open_price`, `high_price`, `low_price`, `close_price`
- `volume`

### 3. Weekly Analysis View

**Purpose**: Pre-computed JOIN for fast API response

```sql
-- Aggregates daily financials to weekly
-- Joins with weekly conflict summaries by region
-- Enables correlation analysis: oil prices vs. conflict events

CREATE VIEW weekly_analysis AS
SELECT 
  w.acled_week,
  w.ticker,
  AVG(f.close_price) as avg_close,
  -- ... price change calculations ...
  w.red_sea_events,
  w.persian_gulf_events,
  w.malacca_events,
  w.total_events,
  w.total_fatalities
FROM weekly_financials w
JOIN financial_prices_daily f 
  ON f.date BETWEEN w.week_start AND w.week_end
GROUP BY w.acled_week, w.ticker;
```

### 4. Geofence Risk Calculation

**Client-Side Logic** (recomputed on every slider change):

```javascript
// For each chokepoint region:
1. Get polygon GeoJSON
2. Filter conflict events to current date range
3. Point-in-polygon test for each event
4. Aggregate: count, fatalities, last event date
5. Calculate risk level:
   - HIGH: >20 events OR >50 fatalities OR event within 7 days
   - MEDIUM: 5-20 events OR 10-50 fatalities OR event within 30 days
   - LOW: <5 events AND <10 fatalities
```

---

## Key Features

### 1. Two-Phase Data Loading

**Problem**: 3 years of conflict data = slow initial load  
**Solution**: Load YTD immediately, fetch full history in background

```javascript
// On app mount:
await conflictStore.loadYTD();      // ~200ms, render immediately
conflictStore.loadFullHistory();     // ~2s, background, no blocking
```

### 2. Date Slider with Dynamic Filtering

- **Quarterly ticks**: Every 3 months for clean UX
- **Client-side filtering**: No server round-trip on slider change
- **Extended range**: End date +1 month to include full selected month
- **Visual feedback**: Thumb labels show MM/DD/YYYY

### 3. Heatmap Recency Weighting

- Newer events within the selected range appear more prominently
- Weighting recalculates client-side when slider changes
- Consistent visual density regardless of date range size

### 4. Geofence Interactions

- Click any chokepoint polygon to open event drawer
- Events filtered to those inside the clicked region
- Risk badges update dynamically with date slider

### 5. Financial Correlation Panel

- **Dual-axis charts**: Price (left) + Events (right)
- **Pearson correlation**: Statistical measure of price-event relationship
- **Region filtering**: View all regions or isolate one chokepoint
- **Ticker selection**: Compare across oil futures and tanker stocks

---

## Project Structure

```
ChokepointMonitor/
├── backend/
│   ├── api/
│   │   ├── main.py                 # FastAPI entry point
│   │   ├── fetch_conflict_events.py # ACLED data retrieval
│   │   ├── chokepoint_metrics.py   # Geofence aggregation
│   │   └── fetch_weekly_analysis.py # Financial correlation data
│   ├── gdelt_pipeline/             # (Abandoned: BigQuery news analysis for realtime conflict data)
│   ├── import_acled_xlsx.py        # ACLED ingestion
│   ├── import_yfinance_data.py     # Financial data ingestion
│   └── supabase_client.py          # Database connection
│
├── frontend-svelte/
│   ├── src/
│   │   ├── App.svelte              # Main layout, map init
│   │   ├── stores/
│   │   │   ├── conflicts.js        # Conflict data + slider state
│   │   │   └── financial.js        # Financial data + correlation
│   │   ├── lib/
│   │   │   ├── components/
│   │   │   │   ├── RangeSlider.svelte      # Custom date slider
│   │   │   │   ├── FinancialDrawer.svelte  # Charts panel
│   │   │   │   ├── FinancialPanel.svelte   # Chart internals
│   │   │   │   └── ConflictPopup.svelte    # Event details
│   │   │   ├── layers/
│   │   │   │   ├── heatmap.js      # Recency-weighted heatmap
│   │   │   │   ├── chokepoints.js  # Conflict point clusters
│   │   │   │   └── geofences.js    # Polygon overlays
│   │   │   └── api.js              # HTTP client
│   │   └── main.js                 # Vite entry
│   ├── dist/                       # Production build (served by FastAPI)
│   └── vite.config.js              # Proxy config for dev
│
├── .github/workflows/
│   └── daily_financial_update.yml  # Scheduled data pipeline
│
├── supabase/
│   └── migrations/                 # Schema definitions
│
└── package.json                    # Root monorepo scripts
```

---

## Getting Started

### Prerequisites

- **Node.js**: v22.12+ (LTS)
- **Python**: 3.10+
- **MapTiler API Key**: [Get one free](https://cloud.maptiler.com/)

### Quick Start

```bash
# 1. Clone and enter directory
git clone https://github.com/samwilsonSW/ChokepointMonitor.git
cd ChokepointMonitor

# 2. Install all dependencies (Node + Python)
npm run install:all

# 3. Configure environment
cp .env.example .env
# Edit .env with your SUPABASE_URL, SUPABASE_KEY, and MAPTILER_KEY

# 4. Run dev servers (frontend + backend)
npm run dev
```

### Available Scripts

| Command | Description |
|---------|-------------|
| `npm run install:all` | Install Node + Python dependencies |
| `npm run dev` | Run both frontend and backend in parallel |
| `npm run dev:frontend` | Svelte dev server only (Vite) |
| `npm run dev:backend` | FastAPI server only (Uvicorn) |
| `npm run render:build` | Production build for Render |
| `npm run render:start` | Production server for Render |

### Environment Variables

```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-service-key
MAPTILER_KEY=your-maptiler-api-key

# Optional (for local dev)
VITE_MAPTILER_KEY=your-maptiler-api-key  # Injected at build time
```

**Built by [Sam Wilson](https://github.com/samwilsonSW)**  
*Geospatial risk visualization for critical maritime chokepoints*
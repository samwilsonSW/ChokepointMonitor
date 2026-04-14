# Chokepoint Monitor

**🌐 Live Demo: [chokepointmonitor.com](https://chokepointmonitor.com)**

[![Deployed on Render](https://img.shields.io/badge/deployed%20on-Render-46E3B7.svg)](https://render.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Svelte](https://img.shields.io/badge/Svelte-FF3E00.svg?logo=svelte&logoColor=white)](https://svelte.dev/)
[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E.svg?logo=supabase&logoColor=white)](https://supabase.com/)

A full-stack geospatial risk visualization tool that correlates armed conflict events with energy market data across three critical maritime oil chokepoints: the Strait of Hormuz, Bab el-Mandeb, and the Strait of Malacca.

---

## What It Does

Chokepoint Monitor ingests conflict event data from [ACLED](https://acleddata.com/) and financial time-series data from Yahoo Finance, stores them in a PostGIS-enabled PostgreSQL database, and surfaces them through an interactive map with heatmaps, geofenced regions, and a financial correlation panel.

| Chokepoint | Daily Oil Flow | Strategic Importance |
|---|---|---|
| **Strait of Hormuz** | ~21M barrels | Primary route for Middle East oil exports |
| **Bab el-Mandeb** | ~5M barrels | Connects Mediterranean via Suez Canal |
| **Strait of Malacca** | ~16M barrels | Primary route for Asian energy imports |

---

## Try It

1. **Explore the heatmap** — Navigate to the Persian Gulf or Red Sea. Darker clusters = higher conflict density.
2. **Use the date slider** — Filter events by time period (defaults to YTD, expands to 3-year history).
3. **Click a geofence** — Click any chokepoint polygon to see conflict events within that region.
4. **Open the Insights panel** — View financial correlation charts with risk metrics.
5. **Switch tickers** — Try `CL=F` (WTI Crude), `BZ=F` (Brent), `FRO` (Frontline Tankers), or `STNG` (Scorpio Tankers).

---

## Architecture

The backend is a FastAPI service backed by Supabase (PostgreSQL + PostGIS). Conflict data is ingested via a Python pipeline from ACLED exports; financial data is fetched daily from Yahoo Finance via a GitHub Actions cron job. The frontend is Svelte 5 with MapLibre GL for WebGL map rendering and D3.js for correlation charts.

A key design decision: recency weighting for the heatmap is computed client-side on every slider change, so visual density stays consistent whether you're viewing 3 months or 3 years of data — no server round-trip needed.

---

## Tech Stack

**Backend**: FastAPI · PostgreSQL 15 + PostGIS · Supabase · Python · Uvicorn  
**Frontend**: Svelte 5 · MapLibre GL · D3.js · Tailwind CSS · Skeleton UI  
**Infrastructure**: Render · GitHub Actions (daily data pipeline) · Vite

---

## Getting Started

### Prerequisites
- Node.js v22.12+
- Python 3.10+
- MapTiler API key ([free tier available](https://cloud.maptiler.com/))

### Quick Start

```bash
git clone https://github.com/samwilsonSW/ChokepointMonitor.git
cd ChokepointMonitor
npm run install:all
cp .env.example .env
# Add your SUPABASE_URL, SUPABASE_KEY, and MAPTILER_KEY to .env
npm run dev
```

### Scripts

| Command | Description |
|---|---|
| `npm run install:all` | Install Node + Python dependencies |
| `npm run dev` | Run frontend + backend in parallel |
| `npm run dev:frontend` | Svelte dev server only |
| `npm run dev:backend` | FastAPI server only |
| `npm run render:build` | Production build for Render |
| `npm run render:start` | Production server for Render |

---

## What I Learned

---

**Built by [Sam Wilson](https://github.com/samwilsonSW)**

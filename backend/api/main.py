from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from datetime import date
from .fetch_conflict_events import fetch_conflict_events, conflicts_to_geojson
from .chokepoint_metrics import fetch_chokepoint_metrics

app = FastAPI(title="Chokepoint Monitor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import asyncio
from concurrent.futures import ThreadPoolExecutor

# Thread pool for running sync Supabase calls
_executor = ThreadPoolExecutor(max_workers=4)

@app.get("/conflicts")
async def get_conflicts(start_date: str = None):
    # Run sync Supabase call in thread pool to avoid blocking event loop
    rows = await asyncio.get_event_loop().run_in_executor(
        _executor,
        fetch_conflict_events,
        start_date,
        True  # chokepoints_only
    )
    geojson = conflicts_to_geojson(rows)
    return geojson


@app.get("/chokepoint-metrics")
async def get_chokepoint_metrics(start_date: str = None):
    """
    Get aggregated conflict metrics for each chokepoint region.

    Returns metrics including event counts, fatalities, risk levels,
    and geospatial data for rendering region polygons and badges.
    """
    metrics = await asyncio.get_event_loop().run_in_executor(
        _executor,
        fetch_chokepoint_metrics,
        start_date
    )
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": m["geojson_polygon"],
                "properties": {
                    "name": m["name"],
                    "display_name": m["display_name"],
                    "center_lat": m["center_lat"],
                    "center_lon": m["center_lon"],
                    "event_count": m["event_count"],
                    "total_events": m["total_events"],
                    "total_fatalities": m["total_fatalities"],
                    "last_event_date": m["last_event_date"],
                    "risk_level": m["risk_level"]
                }
            }
            for m in metrics
        ]
    }

  

# app.mount("/", StaticFiles(directory="frontend-svelte/dist", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    # This tells uvicorn to run the "app" object in this file
    uvicorn.run(app, host="0.0.0.0", port=8000)

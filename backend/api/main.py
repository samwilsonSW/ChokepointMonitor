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

@app.get("/conflicts")
def get_conflicts(start_date: str = None):
  rows = fetch_conflict_events(start_date=start_date, chokepoints_only=True)
#   rows = fetch_conflict_events(start_date=start_date)
  geojson = conflicts_to_geojson(rows)
  return geojson


@app.get("/chokepoint-metrics")
def get_chokepoint_metrics(start_date: str = None):
    """
    Get aggregated conflict metrics for each chokepoint region.
    
    Returns metrics including event counts, fatalities, risk levels,
    and geospatial data for rendering region polygons and badges.
    """
    metrics = fetch_chokepoint_metrics(start_date=start_date)
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

  
# If no endpoint is found ({BASE_URL}/conflicts for example), look in frontend for file
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    # This tells uvicorn to run the "app" object in this file
    uvicorn.run(app, host="0.0.0.0", port=8000)

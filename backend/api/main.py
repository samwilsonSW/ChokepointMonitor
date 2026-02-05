from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

"""API entry for conflict analytics.

Use package execution so relative imports resolve correctly:

    python -m backend.api.main

"""

from .fetch_conflict_events import fetch_conflict_events, conflicts_to_geojson

app = FastAPI(title="Chokepoint Monitor API")

# Allow frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Endpoints

@app.get("/conflicts")
def get_conflicts(
  start_date: str | None = Query(None, description="YYYY-MM-DD"),
  end_date: str | None = Query(None, description="YYYY-MM-DD"),
):
  rows = fetch_conflict_events(start_date=start_date, end_date=end_date)
  geojson = conflicts_to_geojson(rows)
  return geojson


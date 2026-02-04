from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

"""API entry for conflict analytics.

Use package execution so relative imports resolve correctly:

    python -m backend.api.main

"""

from .fetch_conflict_events import fetch_conflict_events, conflicts_to_geojson

app = FastAPI(title="Conflict Analytics API")

# Allow frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

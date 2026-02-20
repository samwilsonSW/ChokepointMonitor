from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from datetime import date
from .fetch_conflict_events import fetch_conflict_events, conflicts_to_geojson

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
  rows = fetch_conflict_events(start_date=start_date)
  geojson = conflicts_to_geojson(rows)
  return geojson

  
# If no endpoint is found ({BASE_URL}/conflicts for example), look in frontend for file
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    # This tells uvicorn to run the "app" object in this file
    uvicorn.run(app, host="0.0.0.0", port=8000)

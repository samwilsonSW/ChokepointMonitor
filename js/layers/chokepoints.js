import { getConflictGeoJSON } from '../api.js';

export async function addConflictsLayer(map) {
    // 1. Fetch the data from your FastAPI backend
    const geojsonData = await getConflictGeoJSON();

    if (!geojsonData) {
        console.error("Failed to load conflict GeoJSON");
        return;
    }

    // 2. Add the data source to the map
    map.addSource('conflict-events', {
        type: 'geojson',
        data: geojsonData
    });

    // 3. Add the visual layer (Circles)
    map.addLayer({
        id: 'conflict-circles',
        type: 'circle',
        source: 'conflict-events',
        paint: {
            // Size circles based on fatalities or just a constant
            'circle-radius': [
                'interpolate', ['linear'], ['zoom'],
                3, 2,  // At zoom 3, radius is 2px
                10, 8  // At zoom 10, radius is 8px
            ],
            'circle-color': '#ff4d4d', // Red for conflict
            'circle-opacity': 0.7,
            'circle-stroke-width': 1,
            'circle-stroke-color': '#ffffff'
        }
    });

    console.log("Conflict layer added to map");
}
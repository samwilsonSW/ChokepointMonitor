import { getConflictGeoJSON } from '../api.js';

let mapSource;

export async function addConflictsLayer(map) {
    mapSource = map;
    // 1. Fetch the data from your FastAPI backend
    const geojsonData = await getConflictGeoJSON();

    if (!geojsonData) {
        console.error("Failed to load conflict GeoJSON");
        return;
    }
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
}

document.getElementById('apply-filter').addEventListener('click', async () => {
    if (!mapSource) return; // Safety check: don't run if map isn't ready
    
    const newDate = document.getElementById('date-input').value;
    const data = await getConflictGeoJSON(newDate);
    
    // Use the correct source ID ('conflict-events' from your previous function)
    const source = mapSource.getSource('conflict-events'); 
    if (source) {
        source.setData(data);
    }
});
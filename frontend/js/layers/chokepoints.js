import { getConflictGeoJSON } from '../api.js';

export async function addConflictsLayer(map) {
    // 1. Fetch the data from your FastAPI backend
    console.log("im finna go get some geoJson files")
    const geojsonData = await getConflictGeoJSON();
    console.log("i got em blud")

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

document.getElementById('apply-filter').addEventListener('click', async () => {
    console.log("Start date hit")
    const newDate = document.getElementById('date-input').value;
    if (!newDate) return;

    // 1. Remove the existing layer/source or update the data
    const data = await getConflictGeoJSON(newDate);
    
    // 2. Update the map source
    if (map.getSource('conflicts')) {
        map.getSource('conflicts').setData(data);
    }
});
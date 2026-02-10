import { getConflictGeoJSON } from '../api.js';

let mapSource;
let activeHeatmapSourceId = null;

export async function addConflictsLayer(map) {
    mapSource = map;
    
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
                3, 3,  // At zoom 3, radius is 2px
                10, 8  // At zoom 10, radius is 8px
            ],
            'circle-color': '#ff4d4d', // Red for conflict
            'circle-opacity': 0.7,
            'circle-stroke-width': 1,
            'circle-stroke-color': '#ffffff'
        }
    });

    // pop up for conflict information
    map.on('mouseenter', 'conflict-circles', () => {
        map.getCanvas().style.cursor = 'pointer';
    });

    // Change it back when leaving
    map.on('mouseleave', 'conflict-circles', () => {
        map.getCanvas().style.cursor = '';
    });

    map.on('click', 'conflict-circles', (e) => {
        // e.features[0] contains the data for the specific circle clicked
        const coordinates = e.features[0].geometry.coordinates.slice();
        const props = e.features[0].properties;

        // Ensure that if the map is zoomed out such that multiple
        // copies of the feature are visible, the popup appears
        // over the copy being pointed to.
        while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
            coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
        }

        // Create the HTML content using your Python-defined properties
        const html = `
            <div style="font-family: sans-serif; padding: 5px;">
                <h3 style="margin: 0 0 5px 0;">${props.event_type || 'Conflict Event'}</h3>
                <p><strong>Country:</strong> ${props.country}</p>
                <p><strong>Date:</strong> ${props.week}</p>
                <p><strong>Fatalities:</strong> ${props.fatalities}</p>
                <p><strong>Sub-type:</strong> ${props.sub_event_type}</p>
            </div>
        `;

        new maplibregl.Popup()
            .setLngLat(coordinates)
            .setHTML(html)
            .addTo(map);
    });
}

document.getElementById('apply-filter').addEventListener('click', async () => {
    if (!mapSource) return; 
    
    const newDate = document.getElementById('date-input').value;
    const data = await getConflictGeoJSON(newDate);
    
    const source = mapSource.getSource('conflict-events'); 
    if (source) {
        source.setData(data);
    }
});
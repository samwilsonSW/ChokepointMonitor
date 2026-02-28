// Conflict events layer with popups

export async function addConflictsLayer(map, geoJsonData) {
    
    if (!geoJsonData) {
        console.error("Failed to load conflict GeoJSON");
        return;
    }
    map.addSource('conflict-events', {
        type: 'geojson',
        data: geoJsonData
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
            'circle-color': '#f04dff', // Red for conflict
            'circle-opacity': 0.2,
            'circle-stroke-width': 0.5,
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
        const coordinates = e.features[0].geometry.coordinates.slice();
        
        // 1. Get ALL features under the click, not just the first one
        const features = e.features;
        const count = features.length;

        // Fix for map wrapping
        while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
            coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
        }

        // 2. Build the HTML dynamically
        // If there's more than one, we show a "Summary" header
        let html = `<div style="font-family: sans-serif; padding: 5px; max-height: 200px; overflow-y: auto;">`;
        
        if (count > 1) {
            html += `<h3 style="margin: 0 0 10px 0; color: #f04dff;">${count} Events at this location</h3><hr>`;
        }

        // 3. Loop through each event found at this pixel
        features.forEach((feature, index) => {
            const props = feature.properties;
            html += `
                <div style="${index > 0 ? 'border-top: 1px solid #eee; margin-top: 10px; pt: 5px;' : ''}">
                    <h4 style="margin: 0 0 5px 0;">${props.event_type || 'Conflict Event'}</h4>
                    <p style="margin: 2px 0;"><strong>Date:</strong> ${props.week}</p>
                    <p style="margin: 2px 0;"><strong>Fatalities:</strong> ${props.fatalities}</p>
                    <p style="margin: 2px 0; font-size: 0.9em; color: #666;">${props.sub_event_type}</p>
                </div>
            `;
        });

        html += `</div>`;

        new maplibregl.Popup()
            .setLngLat(coordinates)
            .setHTML(html)
            .addTo(map);
    });
}
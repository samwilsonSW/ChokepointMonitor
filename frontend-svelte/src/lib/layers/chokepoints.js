/**
 * @param {Object} map - MapLibre instance
 * @param {Object} geoJsonData - Conflict data
 * @param {Function} onSelect - The openConflictDrawer function from App.svelte
*/

export async function addConflictsLayer(map, geoJsonData, onSelect) {
    if (!geoJsonData) {
        console.error("Failed to load conflict GeoJSON");
        return;
    }
    
    // Sources
    map.addSource('conflict-events', {
        type: 'geojson',
        data: geoJsonData
    });

    map.addSource('selected-point', {
        type: 'geojson',
        data: {
            type: 'FeatureCollection',
            features: []
        }
    });

    // >Sources

    // Layers

    // invisible hitbox for points, makes clicking easier without needing to make the visible circles bigger
    map.addLayer({
        id: 'conflict-hitbox',
        type: 'circle',
        source: 'conflict-events',
        paint: {
            'circle-radius': 12,
            'circle-opacity': 0
        }
    });

    // visible layer
    map.addLayer({
        id: 'conflict-circles',
        type: 'circle',
        source: 'conflict-events',
        paint: {
            'circle-radius': 4,
            'circle-color': '#f04dff',
            'circle-opacity': 0.2,
            'circle-stroke-width': 0.5,
            'circle-stroke-color': '#ffffff'
        }
    });

    // highlights selected point with a bright green halo and center dot
    map.addLayer({
        id: 'selected-point-highlight',
        type: 'circle',
        source: 'selected-point',
        paint: {
            'circle-radius': [
                'interpolate', ['linear'], ['zoom'],
                3, 15,
                10, 35
            ],
            'circle-color': 'transparent',
            'circle-stroke-width': 3,
            'circle-stroke-color': '#00ff88',  // Bright green
            'circle-opacity': 0,
            'circle-stroke-opacity': 0.9
        }
    });

    // show center of highlighted point with a smaller solid circle
    map.addLayer({
        id: 'selected-point-center',
        type: 'circle',
        source: 'selected-point',
        paint: {
            'circle-radius': [
                'interpolate', ['linear'], ['zoom'],
                3, 6,
                10, 12
            ],
            'circle-color': '#00ff88',
            'circle-opacity': 0.8
        }
    });
    // >Layers

    // Hovers & Clicks
    map.on('mouseenter', 'conflict-circles', () => {
        map.getCanvas().style.cursor = 'pointer';
    });

    map.on('mouseleave', 'conflict-circles', () => {
        map.getCanvas().style.cursor = '';
    });

    map.on('click', 'conflict-circles', (e) => {
        const features = e.features;
        const coordinates = e.features[0].geometry.coordinates.slice();

        // update highlight source to clicked point
        map.getSource('selected-point').setData({
            type: 'FeatureCollection',
            features: [{
                type: 'Feature',
                geometry: {
                    type: 'Point',
                    coordinates: coordinates
                },
                properties: {}
            }]
        });

        // zoom into location
        map.flyTo({
            center: coordinates,
            zoom: 6,  
            offset: [-210, 0],  // Shift left (-210 length of sidebar)
            duration: 800,  // ms animation duration
            essential: true
        });

        const onMoveEnd = () => {
            if (onSelect) {
                onSelect(features, coordinates);  // Pass coordinates too
            }
            map.off('moveend', onMoveEnd);
        };
        
        map.once('moveend', onMoveEnd);
    });

    (window).clearMapHighlight = () => {
        map.getSource('selected-point').setData({
            type: 'FeatureCollection',
            features: []
        });
    };
}

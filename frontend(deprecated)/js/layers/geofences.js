// Geofence layer with polygon overlays and risk badges for chokepoint regions

/**
 * Add geofence polygon layers and risk badges to the map
 * @param {Object} map - MapLibre map instance
 * @param {Object} metricsGeoJSON - GeoJSON FeatureCollection with chokepoint metrics
 */
export async function addGeofenceLayers(map, metricsGeoJSON) {
    if (!metricsGeoJSON || !metricsGeoJSON.features) {
        console.error("Invalid metrics data for geofences");
        return;
    }

    // Add source for geofence polygons
    map.addSource('chokepoint-geofences', {
        type: 'geojson',
        data: metricsGeoJSON
    });

    // Add polygon fill layer with risk-based coloring
    map.addLayer({
        id: 'geofence-fill',
        type: 'fill',
        source: 'chokepoint-geofences',
        paint: {
            'fill-color': [
                'match',
                ['get', 'risk_level'],
                'high', 'rgba(255, 0, 0, 0.15)',
                'medium', 'rgba(255, 165, 0, 0.12)',
                'low', 'rgba(0, 255, 0, 0.08)',
                'rgba(128, 128, 128, 0.05)'
            ],
            'fill-opacity': 0.6
        }
    });

    // Add polygon border layer
    map.addLayer({
        id: 'geofence-border',
        type: 'line',
        source: 'chokepoint-geofences',
        paint: {
            'line-color': [
                'match',
                ['get', 'risk_level'],
                'high', '#ff3333',
                'medium', '#ff9933',
                'low', '#33cc33',
                '#999999'
            ],
            'line-width': 2,
            'line-dasharray': [3, 2]
        }
    });

    // Add click handler for polygon popups
    map.on('click', 'geofence-fill', (e) => {
        const feature = e.features[0];
        const props = feature.properties;
        const coordinates = [props.center_lon, props.center_lat];

        // const riskColor = {
        //     'high': '#ff3333',
        //     'medium': '#ff9933',
        //     'low': '#33cc33',
        //     'none': '#999999'
        // }[props.risk_level] || '#999999';


        // Choosing to remove "risk level" for now, its making claims that cant be verified or trusted right now.

        // const html = `
        //     <div style="font-family: sans-serif; padding: 10px; min-width: 200px;">
        //         <h3 style="margin: 0 0 10px 0; color: ${riskColor};">${props.display_name}</h3>
        //         <div style="margin-bottom: 8px;">
        //             <span style="font-weight: bold;">Risk Level:</span>
        //             <span style="color: ${riskColor}; text-transform: uppercase; font-weight: bold;">
        //                 ${props.risk_level}
        //             </span>
        //         </div>
        //         <div style="margin-bottom: 5px;">
        //             <span style="font-weight: bold;">Events:</span> ${props.event_count}
        //         </div>
        //         <div style="margin-bottom: 5px;">
        //             <span style="font-weight: bold;">Total Fatalities:</span> ${props.total_fatalities}
        //         </div>
        //         ${props.last_event_date ? `
        //         <div style="margin-bottom: 5px; font-size: 0.9em; color: #666;">
        //             Last event: ${props.last_event_date}
        //         </div>
        //         ` : ''}
        //     </div>
        // `;

        const html = `
            <div style="font-family: sans-serif; padding: 10px; min-width: 200px;">
                <div style="margin-bottom: 5px;">
                    <span style="font-weight: bold;">Events:</span> ${props.event_count}
                </div>
                <div style="margin-bottom: 5px;">
                    <span style="font-weight: bold;">Total Fatalities:</span> ${props.total_fatalities}
                </div>
                ${props.last_event_date ? `
                <div style="margin-bottom: 5px; font-size: 0.9em; color: #666;">
                    Last event: ${props.last_event_date}
                </div>
                ` : ''}
            </div>
        `;

        new maplibregl.Popup()
            .setLngLat(coordinates)
            .setHTML(html)
            .addTo(map);
    });

    // Change cursor on hover
    map.on('mouseenter', 'geofence-fill', () => {
        map.getCanvas().style.cursor = 'pointer';
    });

    map.on('mouseleave', 'geofence-fill', () => {
        map.getCanvas().style.cursor = '';
    });

    // Add risk badges as custom HTML markers
    addRiskBadges(map, metricsGeoJSON);
}

/**
 * Add floating risk badge markers at chokepoint centers
 * @param {Object} map - MapLibre map instance
 * @param {Object} metricsGeoJSON - GeoJSON with chokepoint metrics
 */
function addRiskBadges(map, metricsGeoJSON) {
    // Remove existing badges first
    const existingBadges = document.querySelectorAll('.chokepoint-risk-badge');
    existingBadges.forEach(badge => badge.remove());

    metricsGeoJSON.features.forEach(feature => {
        const props = feature.properties;
        
        // Skip if no events
        if (props.event_count === 0) return;

        const el = document.createElement('div');
        el.className = 'chokepoint-risk-badge';
        
        const riskColors = {
            'high': { bg: '#ff3333', text: 'white' },
            'medium': { bg: '#ff9933', text: 'white' },
            'low': { bg: '#33cc33', text: 'white' }
        };
        const colors = riskColors[props.risk_level] || { bg: '#999999', text: 'white' };

        el.style.cssText = `
            background: ${colors.bg};
            color: ${colors.text};
            padding: 6px 12px;
            border-radius: 16px;
            font-family: sans-serif;
            font-size: 12px;
            font-weight: bold;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            cursor: pointer;
            white-space: nowrap;
            pointer-events: auto;
        `;
        
        el.innerHTML = `
            ${props.display_name}
            <span style="margin-left: 6px; opacity: 0.9;">${props.event_count}</span>
        `;

        // Add click handler to show popup
        el.addEventListener('click', () => {
            const coordinates = [props.center_lon, props.center_lat];
            
            const html = `
                <div style="font-family: sans-serif; padding: 10px; min-width: 200px;">
                    <h3 style="margin: 0 0 10px 0; color: ${colors.bg};">${props.display_name}</h3>
                    <div style="margin-bottom: 8px;">
                        <span style="font-weight: bold;">Risk Level:</span>
                        <span style="color: ${colors.bg}; text-transform: uppercase; font-weight: bold;">
                            ${props.risk_level}
                        </span>
                    </div>
                    <div style="margin-bottom: 5px;">
                        <span style="font-weight: bold;">Events:</span> ${props.event_count}
                    </div>
                    <div style="margin-bottom: 5px;">
                        <span style="font-weight: bold;">Total Fatalities:</span> ${props.total_fatalities}
                    </div>
                    ${props.last_event_date ? `
                    <div style="margin-bottom: 5px; font-size: 0.9em; color: #666;">
                        Last event: ${props.last_event_date}
                    </div>
                    ` : ''}
                </div>
            `;

            new maplibregl.Popup()
                .setLngLat(coordinates)
                .setHTML(html)
                .addTo(map);
        });

        new maplibregl.Marker({ element: el, anchor: 'center' })
            .setLngLat([props.center_lon, props.center_lat])
            .addTo(map);
    });
}

/**
 * Update geofence data when filters change
 * @param {Object} map - MapLibre map instance
 * @param {Object} newMetricsGeoJSON - Updated GeoJSON with new metrics
 */
export function updateGeofenceData(map, newMetricsGeoJSON) {
    const source = map.getSource('chokepoint-geofences');
    if (source) {
        source.setData(newMetricsGeoJSON);
    }
    
    // Refresh risk badges
    addRiskBadges(map, newMetricsGeoJSON);
}

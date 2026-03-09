import maplibregl from 'maplibre-gl';
import GeofencePopup from '../components/GeofencePopup.svelte';
import { mountPopupComponent, unmountPopupComponent } from '../utils/popupMount.js';

export async function addGeofenceLayers(map, metricsGeoJSON) {
    if (!metricsGeoJSON || !metricsGeoJSON.features) {
        console.error("Invalid metrics data for geofences");
        return;
    }

    map.addSource('chokepoint-geofences', {
        type: 'geojson',
        data: metricsGeoJSON
    });

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

    let currentPopup = null;
    let currentPopupContainer = null;

    map.on('click', 'geofence-fill', (e) => {
        const feature = e.features[0];
        const props = feature.properties;
        const coordinates = [props.center_lon, props.center_lat];

        // Clean up previous popup
        if (currentPopup) {
            if (currentPopupContainer) {
                unmountPopupComponent(currentPopupContainer);
            }
            currentPopup.remove();
        }

        const popupContainer = mountPopupComponent(GeofencePopup, {
            name: props.display_name,
            eventCount: props.event_count,
            fatalities: props.total_fatalities,
            riskLevel: props.risk_level,
            lastEventDate: props.last_event_date
        });
        
        currentPopupContainer = popupContainer;

        currentPopup = new maplibregl.Popup({ 
            maxWidth: '280px',
            closeOnClick: false
        })
            .setLngLat(coordinates)
            .setDOMContent(popupContainer)
            .addTo(map);

        currentPopup.on('close', () => {
            unmountPopupComponent(popupContainer);
            currentPopupContainer = null;
        });
    });

    map.on('mouseenter', 'geofence-fill', () => {
        map.getCanvas().style.cursor = 'pointer';
    });

    map.on('mouseleave', 'geofence-fill', () => {
        map.getCanvas().style.cursor = '';
    });

    addRiskBadges(map, metricsGeoJSON);
}

function addRiskBadges(map, metricsGeoJSON) {
    const existingBadges = document.querySelectorAll('.chokepoint-risk-badge');
    existingBadges.forEach(badge => badge.remove());

    let currentPopup = null;
    let currentPopupContainer = null;

    metricsGeoJSON.features.forEach(feature => {
        const props = feature.properties;
        
        if (props.event_count === 0) return;

        const el = document.createElement('div');
        el.className = 'chokepoint-risk-badge';
        
        const riskStyles = {
            'high': { bg: '#ef4444', text: 'white' },
            'medium': { bg: '#f59e0b', text: 'white' },
            'low': { bg: '#10b981', text: 'white' }
        };
        const style = riskStyles[props.risk_level] || { bg: '#6b7280', text: 'white' };

        el.style.background = style.bg;
        el.style.color = style.text;
        
        el.innerHTML = `
            <span>${props.display_name}</span>
            <span style="margin-left: 4px; opacity: 0.8;">${props.event_count}</span>
        `;

        el.addEventListener('click', () => {
            const coordinates = [props.center_lon, props.center_lat];
            
            // Clean up previous popup
            if (currentPopup) {
                if (currentPopupContainer) {
                    unmountPopupComponent(currentPopupContainer);
                }
                currentPopup.remove();
            }
            
            const popupContainer = mountPopupComponent(GeofencePopup, {
                name: props.display_name,
                eventCount: props.event_count,
                fatalities: props.total_fatalities,
                riskLevel: props.risk_level,
                lastEventDate: props.last_event_date
            });
            
            currentPopupContainer = popupContainer;

            currentPopup = new maplibregl.Popup({ 
                maxWidth: '280px',
                closeOnClick: false
            })
                .setLngLat(coordinates)
                .setDOMContent(popupContainer)
                .addTo(map);

            currentPopup.on('close', () => {
                unmountPopupComponent(popupContainer);
                currentPopupContainer = null;
            });
        });

        new maplibregl.Marker({ element: el, anchor: 'center' })
            .setLngLat([props.center_lon, props.center_lat])
            .addTo(map);
    });
}

export function updateGeofenceData(map, newMetricsGeoJSON) {
    const source = map.getSource('chokepoint-geofences');
    if (source) {
        source.setData(newMetricsGeoJSON);
        addRiskBadges(map, newMetricsGeoJSON);
    }
}

/**
 * Initialize geofence layers if they don't exist, or update if they do
 * Safe to call multiple times - handles both initial load and updates
 */
export function initGeofenceLayers(map, metricsGeoJSON) {
    const source = map.getSource('chokepoint-geofences');
    if (source) {
        // Layers already exist, just update data
        updateGeofenceData(map, metricsGeoJSON);
    } else {
        // Initial load
        addGeofenceLayers(map, metricsGeoJSON);
    }
}

import maplibregl from 'maplibre-gl';
import ConflictPopup from '../components/ConflictPopup.svelte';
import { mountPopupComponent, unmountPopupComponent } from '../utils/popupMount.js';

export async function addConflictsLayer(map, geoJsonData) {
    if (!geoJsonData) {
        console.error("Failed to load conflict GeoJSON");
        return;
    }
    
    map.addSource('conflict-events', {
        type: 'geojson',
        data: geoJsonData
    });

    map.addLayer({
        id: 'conflict-circles',
        type: 'circle',
        source: 'conflict-events',
        paint: {
            'circle-radius': [
                'interpolate', ['linear'], ['zoom'],
                3, 3,
                10, 8
            ],
            'circle-color': '#f04dff',
            'circle-opacity': 0.2,
            'circle-stroke-width': 0.5,
            'circle-stroke-color': '#ffffff'
        }
    });

    map.on('mouseenter', 'conflict-circles', () => {
        map.getCanvas().style.cursor = 'pointer';
    });

    map.on('mouseleave', 'conflict-circles', () => {
        map.getCanvas().style.cursor = '';
    });

    let currentPopup = null;
    let currentPopupContainer = null;

    map.on('click', 'conflict-circles', (e) => {
        const coordinates = e.features[0].geometry.coordinates.slice();
        const features = e.features;

        // Clean up previous popup
        if (currentPopup) {
            if (currentPopupContainer) {
                unmountPopupComponent(currentPopupContainer);
            }
            currentPopup.remove();
        }

        while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
            coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
        }

        const popupContainer = mountPopupComponent(ConflictPopup, {
            events: features
        });
        
        currentPopupContainer = popupContainer;
        
        currentPopup = new maplibregl.Popup({ 
            maxWidth: '320px',
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
}

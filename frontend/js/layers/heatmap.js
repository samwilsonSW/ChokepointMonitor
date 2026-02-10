import { getConflictGeoJSON } from '../api.js'

let mapSource;
let activeHeatmapSourceId = null;

// Recency controls opacity (safety-focused)
export async function addConflictHeatmap1Recency(map) {
  console.log("Loading heatmap now")
  mapSource = map;

  const geojsonData = await getConflictGeoJSON();

  map.addSource('conflict-heatmap', {
    type: 'geojson',
    data: geojsonData
  });

  activeHeatmapSourceId = 'conflict-heatmap';

  // Older events (faded)
  map.addLayer({
    id: 'conflict-heat-recency-old',
    type: 'heatmap',
    source: 'conflict-heatmap',
    filter: ['<=', ['get', 'recency'], 0.66],
    paint: {
      'heatmap-weight': 0.6,

      'heatmap-intensity': [
        'interpolate', ['linear'], ['zoom'],
        0, 0.6,
        9, 1.6
      ],

      'heatmap-radius': [
        'interpolate', ['linear'], ['zoom'],
        0, 8,
        6, 18,
        14, 42
      ],

      'heatmap-color': [
        'interpolate', ['linear'], ['heatmap-density'],
        0, 'rgba(0,0,0,0)',
        0.3, 'rgba(0,120,255,0.45)',
        0.6, 'rgba(255,255,0,0.6)',
        0.9, 'rgba(255,80,0,0.7)'
      ],

      'heatmap-opacity': 0.3
    }
  });

  // Recent events (bright)
  map.addLayer({
    id: 'conflict-heat-recency-recent',
    type: 'heatmap',
    source: 'conflict-heatmap',
    filter: ['>', ['get', 'recency'], 0.66],
    paint: {
      'heatmap-weight': 0.6,

      'heatmap-intensity': [
        'interpolate', ['linear'], ['zoom'],
        0, 0.6,
        9, 1.6
      ],

      'heatmap-radius': [
        'interpolate', ['linear'], ['zoom'],
        0, 8,
        6, 18,
        14, 42
      ],

      'heatmap-color': [
        'interpolate', ['linear'], ['heatmap-density'],
        0, 'rgba(0,0,0,0)',
        0.3, 'rgba(0,120,255,0.45)',
        0.6, 'rgba(255,255,0,0.6)',
        0.9, 'rgba(255,80,0,0.7)'
      ],

      'heatmap-opacity': 0.85
    }
  });
}

// Recency directly impacts density, not visibility. Best for risk?
export async function addConflictHeatmap2RecencyAffectsDensity(map) {
  console.log("Loading heatmap now")
  mapSource = map;

  const geojsonData = await getConflictGeoJSON();

  map.addSource('conflict-heatmap', {
    type: 'geojson',
    data: geojsonData
  });

  activeHeatmapSourceId = 'conflict-heatmap';

  map.addLayer({
    id: 'conflict-heat-recency-weight',
    type: 'heatmap',
    source: 'conflict-heatmap',
    paint: {
      'heatmap-weight': [
        '*',
        ['get', 'recency'],
        0.8
      ],

      'heatmap-intensity': [
        'interpolate', ['linear'], ['zoom'],
        0, 0.5,
        9, 1.4
      ],

      'heatmap-radius': [
        'interpolate', ['linear'], ['zoom'],
        0, 6,
        6, 16,
        14, 38
      ],

      'heatmap-color': [
        'interpolate', ['linear'], ['heatmap-density'],
        0, 'rgba(0,0,0,0)',
        0.25, 'rgba(0,150,255,0.5)',
        0.5, 'rgba(0,255,120,0.6)',
        0.75, 'rgba(255,200,0,0.65)',
        1, 'rgba(255,0,0,0.75)'
      ],

      'heatmap-opacity': 0.8
    }
  });
}

// Analyst View
export async function addConflictHeatmap3LayeredTimeWindows(map) {
  console.log("Loading heatmap now")
  mapSource = map;

  const geojsonData = await getConflictGeoJSON();

  map.addSource('conflict-heatmap', {
    type: 'geojson',
    data: geojsonData
  });

  activeHeatmapSourceId = 'conflict-heatmap';

  map.addLayer({
    id: 'conflict-heat-recent',
    type: 'heatmap',
    source: 'conflict-heatmap',
    filter: ['>', ['get', 'recency'], 0.66],
    paint: {
      'heatmap-intensity': 1.6,
      'heatmap-radius': [
        'interpolate', ['linear'], ['zoom'],
        0, 6,
        14, 30
      ],
      'heatmap-opacity': 0.9
    }
  });
}

document.getElementById('apply-filter').addEventListener('click', async () => {
  if (!mapSource || !activeHeatmapSourceId) return;

  const newDate = document.getElementById('date-input').value;
  const data = await getConflictGeoJSON(newDate);

  const source = mapSource.getSource(activeHeatmapSourceId);
  if (source) {
    source.setData(data);
  }
});

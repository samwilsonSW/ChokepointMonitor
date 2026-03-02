<script>
  import { onMount } from 'svelte';
  import maplibregl from 'maplibre-gl';
  import 'maplibre-gl/dist/maplibre-gl.css';
  import { getConflictGeoJSON, getChokepointMetrics } from './lib/api.js';
  import { addConflictsLayer } from './lib/layers/chokepoints.js';
  import { addGeofenceLayers, updateGeofenceData } from './lib/layers/geofences.js';
  import { addConflictHeatmap2RecencyAffectsDensity } from './lib/layers/heatmap.js';

  let mapContainer; // Reference to the DIV
  let map;
  let dateInput = "";

  onMount(async () => {
    // Initialize Map
    map = new maplibregl.Map({
      container: mapContainer,
      style: `https://api.maptiler.com/maps/dataviz/style.json?key=${import.meta.env.VITE_MAPTILER_KEY}`,
      center: [66.0, 10.0],
      zoom: 3
    });

    map.on('load', async () => {
      const [geoJsonData, metricsData] = await Promise.all([
        getConflictGeoJSON(),
        getChokepointMetrics()
      ]);

      await addConflictsLayer(map, geoJsonData);
      await addGeofenceLayers(map, metricsData);
      await addConflictHeatmap2RecencyAffectsDensity(map, geoJsonData);
    });
  });

  async function applyFilter() {
    if (!dateInput) return;
    const [newGeoJson, newMetrics] = await Promise.all([
      getConflictGeoJSON(dateInput),
      getChokepointMetrics(dateInput)
    ]);

    map.getSource('conflict-events')?.setData(newGeoJson);
    map.getSource('conflict-heatmap')?.setData(newGeoJson);
    updateGeofenceData(map, newMetrics);
  }
</script>

<div class="controls">
  <input type="date" bind:value={dateInput} />
  <button on:click={applyFilter}>Apply Filter</button>
</div>

<div id="map" bind:this={mapContainer}></div>

<style>
  #map {
    width: 100%;
    height: 100vh;
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100vh;
    z-index: 1; /* Ensure it's not behind the Skeleton background */
  }
  .controls {
    position: absolute;
    top: 10px;
    left: 10px;
    z-index: 100;
    background: white;
    padding: 10px;
    border-radius: 4px;
  }
</style>
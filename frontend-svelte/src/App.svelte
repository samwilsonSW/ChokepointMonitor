<script>
  import { onMount } from 'svelte';
  import { AppBar } from '@skeletonlabs/skeleton-svelte';
  import maplibregl from 'maplibre-gl';
  import 'maplibre-gl/dist/maplibre-gl.css';
  import { getConflictGeoJSON, getChokepointMetrics } from './lib/api.js';
  import { addConflictsLayer } from './lib/layers/chokepoints.js';
  import { addGeofenceLayers, updateGeofenceData } from './lib/layers/geofences.js';
  import { addConflictHeatmap2RecencyAffectsDensity } from './lib/layers/heatmap.js';

  let mapContainer;
  let map;
  let dateInput = "";

  onMount(async () => {
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

<div class="layout">
  <AppBar class="shrink-0">
    <svelte:fragment slot="lead">
      <strong class="text-xl">Chokepoint Monitor</strong>
    </svelte:fragment>
    
    <svelte:fragment slot="trail">
      <div class="flex items-center gap-2">
        <input 
          type="date" 
          bind:value={dateInput}
          class="input" 
        />
        <button 
          class="btn preset-filled-primary"
          on:click={applyFilter}
          disabled={!dateInput}
        >
          Apply Filter
        </button>
      </div>
    </svelte:fragment>
  </AppBar>

  <div class="map-container" bind:this={mapContainer}></div>
</div>

<style>
  .layout {
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100vh;
    overflow: hidden;
  }
  
  .map-container {
    flex: 1;
    position: relative;
    min-height: 0;
  }
  
  :global(.maplibregl-map) {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
  }
</style>

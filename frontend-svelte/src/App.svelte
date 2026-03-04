<script>
  import { onMount } from 'svelte';

  // skeleton components
  import { AppBar, Dialog, Portal } from '@skeletonlabs/skeleton-svelte';
  import { fly, fade } from 'svelte/transition';
  import ConflictPopup from './lib/components/ConflictPopup.svelte';


  import maplibregl from 'maplibre-gl';
  import 'maplibre-gl/dist/maplibre-gl.css';
  import { getConflictGeoJSON, getChokepointMetrics } from './lib/api.js';
  import { addConflictsLayer } from './lib/layers/chokepoints.js';
  import { addGeofenceLayers, updateGeofenceData } from './lib/layers/geofences.js';
  import { addConflictHeatmap2RecencyAffectsDensity } from './lib/layers/heatmap.js';

  let isDrawerOpen = false;
  let selectedEvents = [];
  let mapContainer;
  let map;
  let dateInput = "";

  function openConflictDrawer(events) {
    selectedEvents = events;
    isDrawerOpen = true;
  }

// Required for v3 to sync state when clicking the backdrop/esc key
  function handleOpenChange(details) {
    isDrawerOpen = details.open;
  }

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

      await addConflictsLayer(map, geoJsonData, openConflictDrawer);
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


<Dialog open={isDrawerOpen} onOpenChange={(e) => isDrawerOpen = e.open}>
  <Dialog.Trigger />

  <Portal>
    <Dialog.Backdrop class="fixed inset-0 z-[9999] bg-black/40 backdrop-blur-sm" />

    <Dialog.Content 
      class="fixed inset-y-0 right-0 z-[10000] w-full max-w-[420px] bg-surface-900 border-l border-white/10 shadow-2xl flex flex-col"
      
    >
      <header class="p-4 border-b border-white/10 flex justify-between items-center bg-surface-800">
        <h2 class="text-xl font-bold text-white">Conflict Events</h2>
        <Dialog.CloseTrigger class="btn hover:bg-white/10 rounded-full p-2 text-white">
          ✕
        </Dialog.CloseTrigger>
      </header>

      <div class="flex-1 overflow-y-auto p-4">
        <ConflictPopup events={selectedEvents} />
      </div>
    </Dialog.Content>
  </Portal>
</Dialog>
  

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

<script>
  import { onMount } from 'svelte';

  // skeleton components
  import { AppBar, Dialog, Portal, Slider } from '@skeletonlabs/skeleton-svelte';
  import { fly, fade } from 'svelte/transition';
  import ConflictPopup from './lib/components/ConflictPopup.svelte';

  import maplibregl from 'maplibre-gl';
  import 'maplibre-gl/dist/maplibre-gl.css';
  import { conflictStore, sliderTicks, dateRangeLabel, sliderThumbLabels, filteredDataWithRecency, geofenceMetrics, pointInPolygon } from './stores/conflicts.js';
  import { addConflictsLayer } from './lib/layers/chokepoints.js';
  import { initGeofenceLayers } from './lib/layers/geofences.js';
  import { addConflictHeatmap2RecencyAffectsDensity } from './lib/layers/heatmap.js';

  let isDrawerOpen = false;
  let selectedEvents = [];
  let mapContainer;
  let map;
  let clearMapHighlight = null;

  // Local slider state (bound to RangeSlider)
  let localSliderValue = [0, 0];
  
  // Sync local slider with store
  $: localSliderValue = $conflictStore.sliderValue;

  function openConflictDrawer(events) {
    selectedEvents = events;
    isDrawerOpen = true;
  }

  $: if (!isDrawerOpen && typeof clearMapHighlight === 'function') {
    clearMapHighlight();
  }

  function handleOpenChange(details) {
    isDrawerOpen = details.open;
    if (details.open === false && clearMapHighlight) {
      clearMapHighlight();
    }
  }

  /**
   * Handle slider value changes with debounce
   */
  let sliderDebounce;
  function handleSliderChange(e) {
    localSliderValue = e.value;
    clearTimeout(sliderDebounce);
    sliderDebounce = setTimeout(() => {
      conflictStore.setSliderValue(e.value);
    }, 50);
  }

  /**
   * Update map sources when filtered data changes
   * Uses filteredDataWithRecency for consistent heatmap weighting relative to slider
   */
  $: if (map && $filteredDataWithRecency.length >= 0) {
    const geojson = {
      type: 'FeatureCollection',
      features: $filteredDataWithRecency
    };

    if (map.getSource('conflict-events')) {
      map.getSource('conflict-events').setData(geojson);
    }
    if (map.getSource('conflict-heatmap')) {
      map.getSource('conflict-heatmap').setData(geojson);
    }
  }

  /**
   * Update geofence layers when metrics change
   * Reacts to date slider changes for dynamic region stats
   */
  $: if (map && $geofenceMetrics.features.length > 0) {
    initGeofenceLayers(map, $geofenceMetrics, handleGeofenceClick);
  }

  /**
   * Handle geofence click - open drawer with events inside polygon
   */
  function handleGeofenceClick(geometry, properties) {
    const polygon = geometry?.coordinates?.[0];
    if (!polygon || !$filteredDataWithRecency.length) return;

    // Filter events to those inside this geofence polygon
    const eventsInGeofence = $filteredDataWithRecency.filter(event => {
      const lon = event.geometry?.coordinates?.[0];
      const lat = event.geometry?.coordinates?.[1];
      if (lon == null || lat == null) return false;
      return pointInPolygon(lon, lat, polygon);
    });

    if (eventsInGeofence.length > 0) {
      openConflictDrawer(eventsInGeofence);
    }
  }

  onMount(async () => {
    map = new maplibregl.Map({
      container: mapContainer,
      style: `https://api.maptiler.com/maps/dataviz/style.json?key=${import.meta.env.VITE_MAPTILER_KEY}`,
      center: [66.0, 10.0],
      zoom: 3
    });

    map.on('load', async () => {
      // Phase 1: Load YTD data and region definitions
      const { geoJson: ytdGeoJson } = await conflictStore.loadYTD();

      // Render initial layers
      const layerResult = await addConflictsLayer(map, ytdGeoJson, openConflictDrawer);
      clearMapHighlight = layerResult?.clearMapHighlight || null;
      await addConflictHeatmap2RecencyAffectsDensity(map, ytdGeoJson);
      // Geofences initialize via reactive $geofenceMetrics once data loads

      // Phase 2: Background load full history
      await conflictStore.loadFullHistory();
      // Geofences auto-update via reactive $geofenceMetrics
    });
  });
</script>

<div class="layout">
  <AppBar class="shrink-0">
    <svelte:fragment slot="lead">
      <strong class="text-xl">Chokepoint Monitor</strong>
    </svelte:fragment>
    
    <svelte:fragment slot="trail">
      <!-- Date Range Slider - full width below AppBar -->
    </svelte:fragment>
  </AppBar>

  <!-- Full-width Date Range Slider -->
  <div class="slider-container bg-surface-800 border-b border-surface-700 px-4 py-2 pb-6">
    <div class="flex items-center gap-4">
      <span class="text-sm text-surface-300 whitespace-nowrap">Date Range:</span>
      {#if $sliderTicks.length > 0}
        <div class="flex-1 min-w-0">
          <!--
            Slider from @skeletonlabs/skeleton-svelte
            Docs: https://www.skeleton.dev/docs/svelte/framework-components/slider
            Uses compound component pattern for range selection
          -->
          <Slider
            value={localSliderValue}
            min={$conflictStore.dataRange.min}
            max={$conflictStore.dataRange.max}
            step={null}
            onValueChange={handleSliderChange}
          >
            <Slider.Control>
              <Slider.Track class="bg-surface-600 h-2 rounded-full">
                <Slider.Range class="bg-primary-500 h-2 rounded-full" />
              </Slider.Track>
              <!-- Thumb 0 with floating label -->
              <Slider.Thumb index={0} class="thumb-with-label w-4 h-4 bg-primary-500 rounded-full border-2 border-surface-900 relative group">
                <Slider.HiddenInput />
                <span class="thumb-label absolute -top-7 left-1/2 -translate-x-1/2 bg-surface-700 text-surface-100 text-xs px-2 py-0.5 rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                  {$sliderThumbLabels[0]}
                </span>
              </Slider.Thumb>
              <!-- Thumb 1 with floating label -->
              <Slider.Thumb index={1} class="thumb-with-label w-4 h-4 bg-primary-500 rounded-full border-2 border-surface-900 relative group">
                <Slider.HiddenInput />
                <span class="thumb-label absolute -top-7 left-1/2 -translate-x-1/2 bg-surface-700 text-surface-100 text-xs px-2 py-0.5 rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                  {$sliderThumbLabels[1]}
                </span>
              </Slider.Thumb>
            </Slider.Control>
            <Slider.MarkerGroup>
              {#each $sliderTicks as tick}
                <Slider.Marker value={tick.value}>
                  <span class="text-xs text-surface-400 whitespace-nowrap">{tick.label}</span>
                </Slider.Marker>
              {/each}
            </Slider.MarkerGroup>
          </Slider>
        </div>
        <span class="text-xs text-surface-400 whitespace-nowrap">
          {$dateRangeLabel}
        </span>
      {:else}
        <span class="text-sm text-surface-400">Loading date range...</span>
      {/if}
    </div>
  </div>

  <div class="map-container" bind:this={mapContainer}></div>
</div>

<Dialog open={isDrawerOpen} onOpenChange={handleOpenChange}>
  <Dialog.Trigger />

  <Portal>
    <Dialog.Backdrop class="fixed inset-0 z-[9999] bg-black/20" />

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

  .slider-container {
    width: 100%;
    flex-shrink: 0;
  }

  /* Add margin below tick marks for readability */
  :global([data-part="marker-group"]) {
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
  }

  /* Always show thumb labels on mobile/touch, hover on desktop */
  @media (hover: none) {
    :global(.thumb-label) {
      opacity: 1 !important;
    }
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

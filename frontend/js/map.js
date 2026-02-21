import { getConflictGeoJSON } from './api.js';
import { addConflictsLayer } from './layers/chokepoints.js';
import {
  addConflictHeatmap1Recency,
  addConflictHeatmap2RecencyAffectsDensity,
  addConflictHeatmap3LayeredTimeWindows,
  addConflictHeatmap4MaptilerExample
} from './layers/heatmap.js';

// MapTiler API key - inject at build time or use env var
const API_KEY = window.MAPTILER_API_KEY || '';
const MAP_STYLE = `https://api.maptiler.com/maps/dataviz/style.json?key=${API_KEY}`;

// initialize maplibre here: https://maplibre.org/maplibre-gl-js/docs/
const map = new maplibregl.Map({
    container: 'map', // Matches the ID in index.html
    style: MAP_STYLE, // The Basemap (Dataviz Theme)
    center: [66.0, 10.0], // Longitude, Latitude (Centered on Arabian Sea/Oman)
    zoom: 3, // Zoom level (Shows Hormuz to Bab el-Mandeb)
    attributionControl: false // Cleaner look (we add attribution manually if needed later)
});

map.on('load', async () => {
    console.log("Map Loaded Successfully");

    var geoJsonData = await getConflictGeoJSON(map);

    try {
        await addConflictsLayer(map, geoJsonData);
        console.log("Conflict layers initialized.");
    } catch (error) {
        console.error("Error loading layer:", error);
    }

    // try {
    //     await addConflictHeatmap1Recency(map, geoJsonData);
    //     console.log("Heatmap 1 loaded")
    // } catch (error) {
    //     console.error("Error loading heatmap layer 1: ", error)
    // }

    // this is probably the best one for now.
    try {
        await addConflictHeatmap2RecencyAffectsDensity(map, geoJsonData);
        console.log("Heatmap 2 loaded")
    } catch (error) {
        console.error("Error loading heatmap layer 2: ", error)
    }

    // try {
    //     await addConflictHeatmap3LayeredTimeWindows(map, geoJsonData);
    //     console.log("Heatmap 3 loaded")
    // } catch (error) {
    //     console.error("Error loading heatmap layer 3: ", error)
    // }

    // try {
    //     await addConflictHeatmap4MaptilerExample(map, geoJsonData);
    //     console.log("Heatmap 4 loaded")
    // } catch (error) {
    //     console.error("Error loading heatmap layer 4: ", error)
    // }
    

    console.log("All layers complete");
});

document.getElementById('apply-filter').addEventListener('click', async () => {
  const newDate = document.getElementById('date-input').value;
  if (!newDate) return;

  // Fetch new data based on selected date
  const newGeoJsonData = await getConflictGeoJSON(newDate);
  if (!newGeoJsonData) return;

  // Update conflict events source
  const eventsSource = map.getSource('conflict-events');
  if (eventsSource) {
    eventsSource.setData(newGeoJsonData);
  }

  // Update heatmap source if it exists
  const heatmapSource = map.getSource('conflict-heatmap');
  if (heatmapSource) {
    heatmapSource.setData(newGeoJsonData);
  }
});
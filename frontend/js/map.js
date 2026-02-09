import { addConflictsLayer } from './layers/chokepoints.js';

// paste api key from MAPTILER here
const API_KEY = 'RXe2SMk0wpdfxaCW7RfG';
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
    try {
        await addConflictsLayer(map);
        console.log("Conflict layers initialized.");
    } catch (error) {
        console.error("Error loading layers:", error);
    }
    console.log("Arrived")
});
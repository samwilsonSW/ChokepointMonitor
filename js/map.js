import { addConflictsLayer } from './layers/chokepoints.js';

// paste api key from MAPTILER here
const API_KEY = 'RXe2SMk0wpdfxaCW7RfG';
const MAP_STYLE = `https://api.maptiler.com/maps/dataviz/style.json?key=${API_KEY}`;

// initialize maplibre here: https://maplibre.org/maplibre-gl-js/docs/
const map = new maplibregl.Map({
    container: 'map', // Matches the ID in index.html
    style: MAP_STYLE, // The Basemap (Dataviz Theme)
    center: [55.0, 18.0], // Longitude, Latitude (Centered on Arabian Sea/Oman)
    zoom: 5, // Zoom level (Shows Hormuz to Bab el-Mandeb)
    attributionControl: false // Cleaner look (we add attribution manually if needed later)
});

// 3. Lifecycle Hooks
map.on('load', async () => {
    console.log("Map Loaded Successfully");
    // This is where we will eventually load our Conflict & Tanker layers
    try {
        // Use the function we imported
        await addConflictsLayer(map);
        console.log("Conflict layers initialized.");
    } catch (error) {
        console.error("Error loading layers:", error);
    }
});
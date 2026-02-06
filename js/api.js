// api.js

const API_BASE_URL = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8000" 
    : window.location.origin; // Dynamically uses the Codespace or Production URL

export async function getConflictGeoJSON(startDate = null, endDate = null) {
    let url = `${API_BASE_URL}/conflicts`;
    const params = new URLSearchParams();
    
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    if (params.toString()) {
        url += `?${params.toString()}`;
    }

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        return data; // This is your GeoJSON FeatureCollection
    } catch (error) {
        console.error("Could not fetch conflict data:", error);
        return null;
    }
}
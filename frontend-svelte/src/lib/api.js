const API_BASE_URL = ""; 

export async function getConflictGeoJSON(startDate = null) {
    let url = `${API_BASE_URL}/conflicts`;
    if (startDate) {
        url += `?start_date=${encodeURIComponent(startDate)}`;
    }

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log(`Found ${data.features.length} conflicts`);
        return data;
    } catch (error) {
        console.error("Could not fetch conflict data:", error);
        return null;
    }
}

export async function getChokepointMetrics(startDate = null) {
    let url = `${API_BASE_URL}/chokepoint-metrics`;
    if (startDate) {
        url += `?start_date=${encodeURIComponent(startDate)}`;
    }

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log(`Loaded metrics for ${data.features.length} chokepoint regions`);
        return data;
    } catch (error) {
        console.error("Could not fetch chokepoint metrics:", error);
        return null;
    }
}

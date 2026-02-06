const API_BASE_URL = ""; 

const getOneYearAgo = () => {
    const d = new Date();
    d.setFullYear(d.getFullYear() - 1);
    return d.toISOString().split('T')[0];
};

export async function getConflictGeoJSON(startDate = getOneYearAgo(), endDate = null) {
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
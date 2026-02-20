const API_BASE_URL = ""; 

// const getOneYearAgo = () => {
//     const d = new Date();
//     d.setFullYear(d.getFullYear() - 1);
//     return d.toISOString().split('T')[0];
// };

export async function getConflictGeoJSON(startDate = null) {
    let url = `${API_BASE_URL}/conflicts`;
    if (startDate) {
        url += `?start_date=${startDate}`;
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
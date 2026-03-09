import { writable, derived } from 'svelte/store';
import { getConflictGeoJSON, getChokepointRegions } from '../lib/api.js';

/**
 * Conflict Data Store
 * 
 * Manages two-phase data loading and client-side filtering.
 * 
 * Usage:
 *   import { conflictStore } from './stores/conflicts.js';
 *   
 *   // In component:
 *   conflictStore.loadYTD(); // Start loading
 *   $conflictStore.filteredData; // Access filtered data
 */

function createConflictStore() {
  const { subscribe, set, update } = writable({
    // Raw data
    allData: [],

    // Filtered data for display
    filteredData: [],

    // Chokepoint region definitions (polygons, centers)
    regions: [],

    // Loading state: 'idle' | 'ytd-loading' | 'ytd-ready' | 'full-loading' | 'complete'
    loadState: 'idle',

    // Date range from API
    dataRange: {
      min: null,  // earliest date in dataset
      max: null   // latest date (from meta.data_through)
    },

    // Current slider selection [startTimestamp, endTimestamp]
    sliderValue: [0, 0]
  });

  return {
    subscribe,

    /**
     * Phase 1: Load YTD data (Jan 1 current year → now)
     * Fast initial load for immediate render
     */
    async loadYTD() {
      update(s => ({ ...s, loadState: 'ytd-loading' }));

      const now = new Date();
      const ytdStart = new Date(now.getFullYear(), 0, 1);
      const startStr = ytdStart.toISOString().split('T')[0];

      try {
        const [geoJson, regions] = await Promise.all([
          getConflictGeoJSON(startStr),
          getChokepointRegions()
        ]);

        if (geoJson?.features) {
          const maxDate = geoJson.meta?.data_through || startStr;

          update(s => ({
            ...s,
            allData: geoJson.features,
            filteredData: geoJson.features,
            regions: regions?.features || [],
            loadState: 'ytd-ready',
            dataRange: {
              min: ytdStart.getTime(),
              max: new Date(maxDate).getTime()
            },
            sliderValue: [ytdStart.getTime(), new Date(maxDate).getTime()]
          }));

          return { geoJson, regions };
        }
      } catch (error) {
        console.error('YTD load error:', error);
        update(s => ({ ...s, loadState: 'idle' }));
        throw error;
      }
    },

    /**
     * Phase 2: Load full 3-year history in background
     * Dynamically calculated: current year - 3
     */
    async loadFullHistory() {
      update(s => ({ ...s, loadState: 'full-loading' }));

      const now = new Date();
      const threeYearStart = new Date(now.getFullYear() - 3, 0, 1);
      const startStr = threeYearStart.toISOString().split('T')[0];

      try {
        const geoJson = await getConflictGeoJSON(startStr);

        if (geoJson?.features) {
          const maxDate = geoJson.meta?.data_through || new Date().toISOString();

          update(s => {
            // Keep current slider position if valid, otherwise expand to full range
            const newMin = threeYearStart.getTime();
            const newMax = new Date(maxDate).getTime();

            let sliderValue = s.sliderValue;
            if (sliderValue[0] < newMin) sliderValue[0] = newMin;
            if (sliderValue[1] > newMax) sliderValue[1] = newMax;

            // Re-filter with new data + current slider
            const filtered = geoJson.features.filter(event => {
              const eventTime = new Date(event.properties.week).getTime();
              return eventTime >= sliderValue[0] && eventTime <= sliderValue[1];
            });

            return {
              ...s,
              allData: geoJson.features,
              filteredData: filtered,
              loadState: 'complete',
              dataRange: { min: newMin, max: newMax },
              sliderValue
            };
          });

          return { geoJson };
        }
      } catch (error) {
        console.error('Full history load error:', error);
        update(s => ({ ...s, loadState: 'complete' }));
        throw error;
      }
    },

    /**
     * Update slider value and re-filter client-side
     * Called on slider change — instant, no server request
     */
    setSliderValue(value) {
      update(s => {
        const [startTime, endTime] = value;
        
        // Add one month to end time to include full selected month
        const endDate = new Date(endTime);
        endDate.setMonth(endDate.getMonth() + 1);
        const extendedEnd = endDate.getTime();
        
        const filtered = s.allData.filter(event => {
          const eventTime = new Date(event.properties.week).getTime();
          return eventTime >= startTime && eventTime < extendedEnd;
        });
        
        return {
          ...s,
          sliderValue: value,
          filteredData: filtered
        };
      });
    },

    /**
     * Get current state value (non-reactive)
     */
    getState() {
      let current;
      subscribe(s => { current = s; })();
      return current;
    }
  };
}

export const conflictStore = createConflictStore();

/**
 * Derived store for slider tick marks
 * Generates quarterly ticks (every 3 months) between min and max dates
 * 
 * To change step values:
 *   - Monthly: d.setMonth(d.getMonth() + 1)
 *   - Quarterly: d.setMonth(d.getMonth() + 3) [current]
 *   - Yearly: d.setMonth(d.getMonth() + 12)
 */
export const sliderTicks = derived(conflictStore, $store => {
  const { dataRange } = $store;
  if (!dataRange.min || !dataRange.max) return [];

  const ticks = [];
  const d = new Date(dataRange.min);
  d.setDate(1); // First of month

  const endDate = new Date(dataRange.max);

  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  while (d <= endDate) {
    ticks.push({
      value: d.getTime(),
      label: `${monthNames[d.getMonth()]} ${d.getFullYear()}`
    });
    d.setMonth(d.getMonth() + 3); // Quarterly ticks
  }

  return ticks;
});

/**
 * Helper: format timestamp as MM/DD/YYYY
 */
function formatDateMMDDYYYY(timestamp) {
  const d = new Date(timestamp);
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  const yyyy = d.getFullYear();
  return `${mm}/${dd}/${yyyy}`;
}

/**
 * Derived store for formatted date range display
 * Format: MM/DD/YYYY - MM/DD/YYYY
 */
export const dateRangeLabel = derived(conflictStore, $store => {
  const { sliderValue, loadState } = $store;

  if (loadState === 'idle' || loadState === 'ytd-loading') {
    return 'Loading...';
  }
  if (loadState === 'ytd-ready' || loadState === 'full-loading') {
    return 'YTD loaded • fetching history...';
  }

  return `${formatDateMMDDYYYY(sliderValue[0])} - ${formatDateMMDDYYYY(sliderValue[1])}`;
});

/**
 * Derived store for current slider thumb labels (tooltips)
 * Returns [startLabel, endLabel] in MM/DD/YYYY format
 */
export const sliderThumbLabels = derived(conflictStore, $store => {
  const { sliderValue, loadState } = $store;

  if (loadState === 'idle' || loadState === 'ytd-loading') {
    return ['', ''];
  }

  return [formatDateMMDDYYYY(sliderValue[0]), formatDateMMDDYYYY(sliderValue[1])];
});

/**
 * Compute recency values (0.0-1.0) for events relative to current slider range
 * Events at slider start = 0.0, events at slider end = 1.0
 */
function computeRecencyForSlider(events, sliderStart, sliderEnd) {
  if (!events.length || sliderStart >= sliderEnd) {
    return events.map(e => ({ ...e, properties: { ...e.properties, recency: 0.5 } }));
  }

  return events.map(event => {
    const eventTime = new Date(event.properties.week).getTime();
    // Clamp to slider range
    const clampedTime = Math.max(sliderStart, Math.min(eventTime, sliderEnd));
    const recency = (clampedTime - sliderStart) / (sliderEnd - sliderStart);
    return {
      ...event,
      properties: {
        ...event.properties,
        recency: Math.max(0.0, Math.min(1.0, recency))
      }
    };
  });
}

/**
 * Derived store: filtered data with recency computed relative to current slider range
 * This ensures heatmap weighting is consistent regardless of full dataset size
 */
export const filteredDataWithRecency = derived(conflictStore, $store => {
  const { filteredData, sliderValue, loadState } = $store;

  if (loadState === 'idle' || loadState === 'ytd-loading' || !filteredData.length) {
    return [];
  }

  return computeRecencyForSlider(filteredData, sliderValue[0], sliderValue[1]);
});

/**
 * Point-in-polygon test using ray casting algorithm
 * Supports GeoJSON polygon format (array of [lon, lat] coordinates)
 */
function pointInPolygon(lon, lat, polygon) {
  // polygon is expected as [[lon, lat], [lon, lat], ...]
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const xi = polygon[i][0], yi = polygon[i][1];
    const xj = polygon[j][0], yj = polygon[j][1];

    if (((yi > lat) !== (yj > lat)) &&
        (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi)) {
      inside = !inside;
    }
  }
  return inside;
}

/**
 * Calculate risk level based on event metrics
 */
function calculateRiskLevel(eventCount, fatalities, lastEventDate) {
  if (eventCount === 0) return 'none';

  // Check recency
  if (lastEventDate) {
    const lastDate = new Date(lastEventDate);
    const daysSince = (Date.now() - lastDate.getTime()) / (1000 * 60 * 60 * 24);

    if (daysSince <= 7) return 'high';
    if (daysSince <= 30 && eventCount >= 5) return 'medium';
  }

  // Check volume thresholds
  if (eventCount > 20 || fatalities > 50) return 'high';
  if (eventCount >= 5 || fatalities >= 10) return 'medium';

  return 'low';
}

/**
 * Compute geofence metrics from filtered conflict events
 * Calculates event counts, fatalities, and risk levels for each region
 */
function computeGeofenceMetrics(regions, events) {
  if (!regions.length || !events.length) {
    return {
      type: 'FeatureCollection',
      features: regions.map(r => ({
        ...r,
        properties: {
          ...r.properties,
          event_count: 0,
          total_events: 0,
          total_fatalities: 0,
          last_event_date: null,
          risk_level: 'none'
        }
      }))
    };
  }

  const features = regions.map(region => {
    const props = region.properties;
    const polygon = region.geometry?.coordinates?.[0] || [];

    // Find events within this region's polygon
    const containedEvents = events.filter(e => {
      const lon = e.geometry?.coordinates?.[0];
      const lat = e.geometry?.coordinates?.[1];
      if (lon == null || lat == null) return false;
      return pointInPolygon(lon, lat, polygon);
    });

    const eventCount = containedEvents.length;
    const totalEvents = containedEvents.reduce((sum, e) =>
      sum + (e.properties?.no_of_events || 0), 0);
    const totalFatalities = containedEvents.reduce((sum, e) =>
      sum + (e.properties?.fatalities || 0), 0);

    const lastEventDate = containedEvents.length > 0
      ? containedEvents
          .map(e => e.properties?.week)
          .filter(Boolean)
          .sort()
          .pop()
      : null;

    const riskLevel = calculateRiskLevel(eventCount, totalFatalities, lastEventDate);

    return {
      type: 'Feature',
      geometry: region.geometry,
      properties: {
        name: props.name,
        display_name: props.display_name,
        center_lat: props.center_lat,
        center_lon: props.center_lon,
        event_count: eventCount,
        total_events: totalEvents,
        total_fatalities: totalFatalities,
        last_event_date: lastEventDate,
        risk_level: riskLevel
      }
    };
  });

  return { type: 'FeatureCollection', features };
}

/**
 * Derived store: geofence metrics calculated from filtered events
 * Updates dynamically when date slider changes
 */
export const geofenceMetrics = derived(conflictStore, $store => {
  const { regions, filteredData, loadState } = $store;

  if (loadState === 'idle' || loadState === 'ytd-loading') {
    return { type: 'FeatureCollection', features: [] };
  }

  return computeGeofenceMetrics(regions, filteredData);
});

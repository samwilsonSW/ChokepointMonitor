import { writable, derived } from 'svelte/store';
import { getConflictGeoJSON, getChokepointMetrics } from './lib/api.js';

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
        const [geoJson, metrics] = await Promise.all([
          getConflictGeoJSON(startStr),
          getChokepointMetrics(startStr)
        ]);

        if (geoJson?.features) {
          const maxDate = geoJson.meta?.data_through || startStr;
          
          update(s => ({
            ...s,
            allData: geoJson.features,
            filteredData: geoJson.features,
            loadState: 'ytd-ready',
            dataRange: {
              min: ytdStart.getTime(),
              max: new Date(maxDate).getTime()
            },
            sliderValue: [ytdStart.getTime(), new Date(maxDate).getTime()]
          }));
          
          return { geoJson, metrics };
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
        const [geoJson, metrics] = await Promise.all([
          getConflictGeoJSON(startStr),
          getChokepointMetrics(startStr)
        ]);

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
          
          return { geoJson, metrics };
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
 * Generates month-boundary ticks between min and max dates
 * 
 * To change step values, modify generateMonthTicks:
 *   - Weekly: increment by 7 days
 *   - Quarterly: filter month % 3 === 0
 *   - Yearly: only month === 0
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
    d.setMonth(d.getMonth() + 1);
  }
  
  return ticks;
});

/**
 * Derived store for formatted date range display
 */
export const dateRangeLabel = derived(conflictStore, $store => {
  const { sliderValue, loadState } = $store;
  
  if (loadState === 'idle' || loadState === 'ytd-loading') {
    return 'Loading...';
  }
  if (loadState === 'ytd-ready' || loadState === 'full-loading') {
    return 'YTD loaded • fetching history...';
  }
  
  const start = new Date(sliderValue[0]);
  const end = new Date(sliderValue[1]);
  
  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  
  return `${monthNames[start.getMonth()]} ${start.getFullYear()} - ${monthNames[end.getMonth()]} ${end.getFullYear()}`;
});

import { writable, derived } from 'svelte/store';
import { getWeeklyAnalysis } from '../lib/api.js';

/**
 * Financial Data Store
 *
 * Manages weekly financial + conflict data with client-side filtering.
 * Fetches all data on init (~520 rows currently, max ~3KB), filters client-side.
 *
 * Usage:
 *   import { financialStore, createFilteredFinancialData } from './stores/financial.js';
 *
 *   // In component:
 *   financialStore.load(); // Start loading
 *   $filteredData; // Access filtered data
 */

function createFinancialStore() {
  const { subscribe, set, update } = writable({
    // Raw data from API
    allData: [],

    // Loading state: 'idle' | 'loading' | 'ready' | 'error'
    loadState: 'idle',

    // Available tickers from API
    tickers: [],

    // Date range from API
    dateRange: {
      min: null,
      max: null
    },

    // User selections
    selectedTicker: 'CL=F',
    selectedRegion: 'all' // 'all' | 'red_sea' | 'persian_gulf' | 'malacca'
  });

  return {
    subscribe,

    /**
     * Load all weekly analysis data on app init
     */
    async load() {
      update(s => ({ ...s, loadState: 'loading' }));

      try {
        const data = await getWeeklyAnalysis();
        console.log('Financial API response:', data);

        // Handle null/undefined response or missing data property
        if (!data || !data.data || !Array.isArray(data.data)) {
          console.error('Invalid data structure from API:', data);
          update(s => ({ ...s, loadState: 'error' }));
          return null;
        }

        console.log(`Loaded ${data.data.length} financial records. First record:`, data.data[0]);

        // Extract tickers from data if not provided separately
        let tickers = data.tickers || [];
        if (!tickers.length && data.data.length > 0) {
          // Extract unique tickers from the data itself
          const uniqueTickers = new Set(data.data.map(d => d.ticker).filter(Boolean));
          tickers = Array.from(uniqueTickers).sort();
        }
        console.log('Available tickers:', tickers);

        // Use first available ticker if current selection isn't in the list
        const currentTicker = tickers.find(t => t === 'USO') || tickers[0] || 'USO';
        console.log('Using ticker:', currentTicker);

        update(s => ({
          ...s,
          allData: data.data,
          tickers: tickers,
          selectedTicker: currentTicker,
          dateRange: {
            min: data.date_range?.min ? new Date(data.date_range.min).getTime() : null,
            max: data.date_range?.max ? new Date(data.date_range.max).getTime() : null
          },
          loadState: 'ready'
        }));
        return data;
      } catch (error) {
        console.error('Financial data load error:', error);
        update(s => ({ ...s, loadState: 'error' }));
        throw error;
      }
    },

    /**
     * Set selected ticker
     */
    setTicker(ticker) {
      update(s => ({ ...s, selectedTicker: ticker }));
    },

    /**
     * Set selected region filter
     */
    setRegion(region) {
      update(s => ({ ...s, selectedRegion: region }));
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

export const financialStore = createFinancialStore();

/**
 * Derived store: filter financial data by date range (from conflict store) and selections
 * Depends on conflictStore for date slider range
 */
export function createFilteredFinancialData(conflictStore) {
  return derived([financialStore, conflictStore], ([$financial, $conflict]) => {
    const { allData, selectedTicker, selectedRegion, loadState } = $financial;
    const { sliderValue, loadState: conflictLoadState } = $conflict;

    // Financial data must be ready
    if (loadState !== 'ready') {
      return [];
    }

    // Conflict store must have loaded enough to have slider values
    // Valid states: 'ytd-ready', 'full-loading', 'complete'
    const validConflictStates = ['ytd-ready', 'full-loading', 'complete'];
    if (!validConflictStates.includes(conflictLoadState)) {
      return [];
    }

    // Must have slider values
    if (!sliderValue || !Array.isArray(sliderValue) || sliderValue.length !== 2) {
      return [];
    }

    const [startTime, endTime] = sliderValue;

    // Validate time range
    if (typeof startTime !== 'number' || typeof endTime !== 'number' || startTime >= endTime) {
      return [];
    }

    const filtered = allData.filter(d => {
      // Filter by ticker
      if (d.ticker !== selectedTicker) return false;

      // Filter by date range
      const weekTime = new Date(d.acled_week).getTime();
      if (isNaN(weekTime)) {
        console.warn('Invalid date:', d.acled_week);
        return false;
      }
      if (weekTime < startTime || weekTime > endTime) return false;

      return true;
    });
    
    console.log(`Financial filter: ${allData.length} total, ${filtered.length} after ticker (${selectedTicker}) and date filter (${new Date(startTime).toISOString().split('T')[0]} to ${new Date(endTime).toISOString().split('T')[0]})`);
    
    return filtered.map(d => {
      // Apply region filter to conflict counts
      let events = d.total_events;
      let fatalities = d.total_fatalities;

      if (selectedRegion !== 'all') {
        events = d[`${selectedRegion}_events`] || 0;
        fatalities = d[`${selectedRegion}_fatalities`] || 0;
      }

      return {
        ...d,
        filtered_events: events,
        filtered_fatalities: fatalities
      };
    });
  });
}

/**
 * Calculate Pearson correlation coefficient between two arrays
 * Handles edge cases: mismatched lengths, empty arrays, zero variance, NaN/Infinity values
 */
export function pearsonCorrelation(x, y) {
  // Validate inputs
  if (!Array.isArray(x) || !Array.isArray(y)) return 0;
  const n = x.length;
  if (n !== y.length || n === 0) return 0;

  // Filter out invalid values (NaN, Infinity, null, undefined)
  const validPairs = [];
  for (let i = 0; i < n; i++) {
    const xi = x[i];
    const yi = y[i];
    if (
      typeof xi === 'number' && isFinite(xi) &&
      typeof yi === 'number' && isFinite(yi)
    ) {
      validPairs.push([xi, yi]);
    }
  }

  const m = validPairs.length;
  if (m < 2) return 0; // Need at least 2 points for correlation

  let sumX = 0, sumY = 0;
  for (const [xi, yi] of validPairs) {
    sumX += xi;
    sumY += yi;
  }

  const meanX = sumX / m;
  const meanY = sumY / m;

  let sumXY = 0, sumX2 = 0, sumY2 = 0;
  for (const [xi, yi] of validPairs) {
    const dx = xi - meanX;
    const dy = yi - meanY;
    sumXY += dx * dy;
    sumX2 += dx * dx;
    sumY2 += dy * dy;
  }

  // Zero variance check (all values identical)
  if (sumX2 === 0 || sumY2 === 0) return 0;

  const denominator = Math.sqrt(sumX2 * sumY2);
  if (denominator === 0) return 0;

  return sumXY / denominator;
}

/**
 * Derived store: correlation stats for current filtered data
 */
export function createCorrelationStats(filteredDataStore) {
  return derived(filteredDataStore, $data => {
    if (!$data || $data.length < 2) {
      return { r: 0, n: 0, interpretation: 'Insufficient data' };
    }

    const prices = $data.map(d => d.avg_close);
    const events = $data.map(d => d.filtered_events);

    const r = pearsonCorrelation(prices, events);

    // Handle NaN result
    if (isNaN(r) || !isFinite(r)) {
      return { r: 0, n: $data.length, interpretation: 'Unable to calculate' };
    }

    let interpretation;
    const absR = Math.abs(r);
    if (absR < 0.3) interpretation = 'Weak / No correlation';
    else if (absR < 0.7) interpretation = 'Moderate correlation';
    else interpretation = 'Strong correlation';

    return {
      r: parseFloat(r.toFixed(3)),
      n: $data.length,
      interpretation
    };
  });
}

/**
 * Derived store: chart-ready data formatted for dual-axis display
 */
export function createChartData(filteredDataStore) {
  return derived(filteredDataStore, $data => {
    if (!$data || !$data.length) return null;

    return $data.map(d => ({
      date: d.acled_week,
      price: d.avg_close,
      priceChange: d.weekly_change_pct,
      volatility: d.range_volatility_pct,
      redSeaEvents: d.red_sea_events || 0,
      persianGulfEvents: d.persian_gulf_events || 0,
      malaccaEvents: d.malacca_events || 0,
      totalEvents: d.filtered_events
    }));
  });
}

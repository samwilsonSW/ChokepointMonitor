import { writable, derived } from 'svelte/store';
import { getWeeklyAnalysis } from '../lib/api.js';

/**
 * Financial Data Store
 *
 * Manages weekly financial + conflict data with client-side filtering.
 * Fetches all data on init (~520 rows currently, max ~3KB), filters client-side.
 *
 * Usage:
 *   import { financialStore, filteredFinancialData } from './stores/financial.js';
 *
 *   // In component:
 *   financialStore.load(); // Start loading
 *   $filteredFinancialData; // Access filtered data
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
    selectedTicker: 'USO',
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

        if (data?.data) {
          update(s => ({
            ...s,
            allData: data.data,
            tickers: data.tickers || [],
            dateRange: {
              min: data.date_range?.min ? new Date(data.date_range.min).getTime() : null,
              max: data.date_range?.max ? new Date(data.date_range.max).getTime() : null
            },
            loadState: 'ready'
          }));
          return data;
        }
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

    if (loadState !== 'ready' || conflictLoadState === 'idle') {
      return [];
    }

    const [startTime, endTime] = sliderValue;

    return allData.filter(d => {
      // Filter by ticker
      if (d.ticker !== selectedTicker) return false;

      // Filter by date range
      const weekTime = new Date(d.acled_week).getTime();
      if (weekTime < startTime || weekTime > endTime) return false;

      return true;
    }).map(d => {
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
 */
export function pearsonCorrelation(x, y) {
  const n = x.length;
  if (n !== y.length || n === 0) return 0;

  const sumX = x.reduce((a, b) => a + b, 0);
  const sumY = y.reduce((a, b) => a + b, 0);
  const sumXY = x.reduce((sum, xi, i) => sum + xi * y[i], 0);
  const sumX2 = x.reduce((sum, xi) => sum + xi * xi, 0);
  const sumY2 = y.reduce((sum, yi) => sum + yi * yi, 0);

  const numerator = n * sumXY - sumX * sumY;
  const denominator = Math.sqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));

  if (denominator === 0) return 0;
  return numerator / denominator;
}

/**
 * Derived store: correlation stats for current filtered data
 */
export function createCorrelationStats(filteredDataStore) {
  return derived(filteredDataStore, $data => {
    if ($data.length < 2) {
      return { r: 0, n: 0, interpretation: 'Insufficient data' };
    }

    const prices = $data.map(d => d.avg_close);
    const events = $data.map(d => d.filtered_events);

    const r = pearsonCorrelation(prices, events);

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
    if (!$data.length) return null;

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

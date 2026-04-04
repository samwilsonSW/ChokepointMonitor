<script>
  import { onMount, createEventDispatcher } from 'svelte';
  import { scaleLinear, scaleBand } from 'd3-scale';
  import { line } from 'd3-shape';
  import { axisBottom, axisLeft, axisRight } from 'd3-axis';
  import { select } from 'd3-selection';

  // Props
  export let data = [];
  export let ticker = 'USO';
  export let correlationStats = { r: 0, n: 0, interpretation: '' };
  export let availableTickers = ['USO', 'BNO', 'UCO', 'SCO'];
  export let selectedRegion = 'all';

  // Event dispatcher for interactions
  const dispatch = createEventDispatcher();

  // Chart refs
  let svgElement;
  let containerElement;
  let width = 600;
  let height = 350;
  const margin = { top: 20, right: 60, bottom: 60, left: 60 };

  // Region colors (match FinancialPanel)
  const regionColors = {
    redSea: '#ef4444',
    persianGulf: '#f97316',
    malacca: '#22c55e'
  };

  // Region filter options
  const regionOptions = [
    { value: 'all', label: 'All Regions' },
    { value: 'redSea', label: 'Red Sea' },
    { value: 'persianGulf', label: 'Persian Gulf' },
    { value: 'malacca', label: 'Malacca' }
  ];

  // Filter data based on selected region
  $: filteredData = selectedRegion === 'all' 
    ? data 
    : data.map(d => ({
        ...d,
        displayEvents: d[selectedRegion + 'Events'] || 0,
        redSeaEvents: selectedRegion === 'redSea' ? d.redSeaEvents : 0,
        persianGulfEvents: selectedRegion === 'persianGulf' ? d.persianGulfEvents : 0,
        malaccaEvents: selectedRegion === 'malacca' ? d.malaccaEvents : 0
      }));

  // Resize observer for responsive chart
  onMount(() => {
    if (!containerElement) return;

    const resizeObserver = new ResizeObserver(entries => {
      for (const entry of entries) {
        width = entry.contentRect.width;
        height = Math.max(300, entry.contentRect.height - 80); // Leave room for legend
      }
    });

    resizeObserver.observe(containerElement);
    return () => resizeObserver.disconnect();
  });

  // Redraw chart when data or dimensions change
  $: if (svgElement && filteredData.length > 0 && width > 0) {
    drawChart();
  }

  function drawChart() {
    const svg = select(svgElement);
    svg.selectAll('*').remove();

    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Scales
    const xScale = scaleBand()
      .domain(filteredData.map(d => d.date))
      .range([0, innerWidth])
      .padding(0.2);

    const yPriceScale = scaleLinear()
      .domain([
        Math.min(...filteredData.map(d => d.price)) * 0.95,
        Math.max(...filteredData.map(d => d.price)) * 1.05
      ])
      .range([innerHeight, 0]);

    const maxEvents = Math.max(...filteredData.map(d =>
      d.redSeaEvents + d.persianGulfEvents + d.malaccaEvents
    ), 1);

    const yEventsScale = scaleLinear()
      .domain([0, maxEvents * 1.2])
      .range([innerHeight, 0]);

    const priceLine = line()
      .x(d => (xScale(d.date) || 0) + xScale.bandwidth() / 2)
      .y(d => yPriceScale(d.price));

    const barWidth = Math.max(4, xScale.bandwidth() * 0.6);

    // Grid lines
    g.append('g')
      .attr('class', 'grid')
      .call(axisLeft(yPriceScale)
        .tickSize(-innerWidth)
      )
      .selectAll('line')
      .attr('stroke', 'rgba(255,255,255,0.1)');

    g.select('.grid').select('.domain').remove();

    // Stacked bars for events by region
    filteredData.forEach(d => {
      const x = (xScale(d.date) || 0) + (xScale.bandwidth() - barWidth) / 2;
      let yOffset = innerHeight;

      if (d.redSeaEvents > 0) {
        const barHeight = innerHeight - yEventsScale(d.redSeaEvents);
        yOffset -= barHeight;
        g.append('rect')
          .attr('x', x)
          .attr('y', yOffset)
          .attr('width', barWidth)
          .attr('height', barHeight)
          .attr('fill', regionColors.redSea)
          .attr('opacity', 0.8);
      }

      if (d.persianGulfEvents > 0) {
        const barHeight = innerHeight - yEventsScale(d.persianGulfEvents);
        yOffset -= barHeight;
        g.append('rect')
          .attr('x', x)
          .attr('y', yOffset)
          .attr('width', barWidth)
          .attr('height', barHeight)
          .attr('fill', regionColors.persianGulf)
          .attr('opacity', 0.8);
      }

      if (d.malaccaEvents > 0) {
        const barHeight = innerHeight - yEventsScale(d.malaccaEvents);
        yOffset -= barHeight;
        g.append('rect')
          .attr('x', x)
          .attr('y', yOffset)
          .attr('width', barWidth)
          .attr('height', barHeight)
          .attr('fill', regionColors.malacca)
          .attr('opacity', 0.8);
      }
    });

    // Price line
    g.append('path')
      .datum(filteredData)
      .attr('fill', 'none')
      .attr('stroke', '#3b82f6')
      .attr('stroke-width', 2)
      .attr('d', priceLine);

    // Price dots
    g.selectAll('.price-dot')
      .data(filteredData)
      .enter()
      .append('circle')
      .attr('class', 'price-dot')
      .attr('cx', d => (xScale(d.date) || 0) + xScale.bandwidth() / 2)
      .attr('cy', d => yPriceScale(d.price))
      .attr('r', 3)
      .attr('fill', '#3b82f6');

    // X Axis
    const xAxis = g.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(axisBottom(xScale)
        // Adjust the modulo (e.g., % 2 or % 4) depending on how many weeks you want to skip
        .tickValues(xScale.domain().filter((_, i) => i % 1 === 0)) 
        .tickFormat(d => d) // Simply return the week string/value
      );

    xAxis.selectAll('text')
      .attr('transform', 'rotate(-45)')
      .style('text-anchor', 'end')
      .attr('fill', 'rgba(255,255,255,0.6)');

    xAxis.select('.domain').attr('stroke', 'rgba(255,255,255,0.3)');
    xAxis.selectAll('.tick line').attr('stroke', 'rgba(255,255,255,0.3)');

    // Left Y Axis (Price)
    const yPriceAxis = g.append('g')
      .call(axisLeft(yPriceScale).ticks(6).tickFormat(d => `$${d.toFixed(0)}`));

    yPriceAxis.selectAll('text').attr('fill', '#3b82f6');
    yPriceAxis.select('.domain').attr('stroke', '#3b82f6');
    yPriceAxis.selectAll('.tick line').attr('stroke', '#3b82f6');

    // Right Y Axis (Events)
    const yEventsAxis = g.append('g')
      .attr('transform', `translate(${innerWidth},0)`)
      .call(axisRight(yEventsScale).ticks(6));

    yEventsAxis.selectAll('text').attr('fill', 'rgba(255,255,255,0.6)');
    yEventsAxis.select('.domain').attr('stroke', 'rgba(255,255,255,0.3)');
    yEventsAxis.selectAll('.tick line').attr('stroke', 'rgba(255,255,255,0.3)');

    // Axis labels
    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0 - margin.left + 15)
      .attr('x', 0 - innerHeight / 2)
      .attr('text-anchor', 'middle')
      .attr('fill', '#3b82f6')
      .attr('font-size', '12px')
      .text(`${ticker} Price ($)`);

    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', innerWidth + margin.right - 15)
      .attr('x', 0 - innerHeight / 2)
      .attr('text-anchor', 'middle')
      .attr('fill', 'rgba(255,255,255,0.6)')
      .attr('font-size', '12px')
      .text('Conflict Events');
  }

  function handleTickerChange(event) {
    dispatch('tickerChange', { ticker: event.target.value });
  }

  function handleRegionChange(event) {
    dispatch('regionChange', { region: event.target.value });
  }

  // Get interpretation color based on correlation strength
  $: correlationColor = Math.abs(correlationStats.r) > 0.5 
    ? 'text-warning-500' 
    : Math.abs(correlationStats.r) > 0.3 
      ? 'text-surface-300' 
      : 'text-surface-500';
</script>

<div class="h-full flex flex-col bg-surface-900">
  <!-- Header - Financial Insights -->
  <div class="mb-4 pb-4 border-b border-surface-700">
    <h2 class="text-2xl font-bold text-white mb-1">Financial Insights</h2>
    <p class="text-md text-surface-200 font-mono">{ticker}</p>
  </div>

  <!-- Controls Section -->
  <div class="space-y-3 mb-4">
    <!-- Ticker Selector -->
    <div class="flex flex-col gap-1">
      <label class="text-xs text-surface-400 uppercase tracking-wide">Ticker
        <select 
          class="input preset-tonal-surface border-surface-600 text-white text-sm py-2 px-3 rounded"
          value={ticker}
          on:change={handleTickerChange}
        >
          {#each availableTickers as t}
            <option value={t} class="bg-surface-800 text-white">{t}</option>
          {/each}
        </select>
      </label>
    </div>

    <!-- Region Filter -->
    <div class="flex flex-col gap-1">
      <label class="text-xs text-surface-400 uppercase tracking-wide">Region Filter
        <select 
          class="input preset-tonal-surface border-surface-600 text-white text-sm py-2 px-3 rounded"
          bind:value={selectedRegion}
          on:change={handleRegionChange}
        >
          {#each regionOptions as option}
            <option value={option.value}>{option.label}</option>
          {/each}
        </select>
      </label>
    </div>
  </div>

  <!-- Correlation Stats -->
  <div class="preset-tonal-surface p-3 rounded-lg border border-surface-600 mb-4">
    <div class="flex justify-between items-center">
      <div class="flex gap-4 text-sm">
        <span class="text-surface-400">
          r = <span class="font-mono {correlationColor}">{correlationStats.r}</span>
        </span>
        <span class="text-surface-400">
          n = <span class="text-white font-mono">{correlationStats.n}</span>
        </span>
      </div>
      <span class="text-xs text-surface-500 italic">{correlationStats.interpretation}</span>
    </div>
  </div>

  <!-- Chart Container -->
  <div class="flex-1 min-h-0" bind:this={containerElement}>
    {#if data.length > 0}
      <svg bind:this={svgElement} width={width} height={height} class="w-full">
        <!-- Chart rendered by D3 -->
      </svg>

      <!-- Legend -->
      <div class="flex justify-center gap-4 mt-3 text-xs flex-wrap">
        <div class="flex items-center gap-1">
          <span class="w-3 h-3 rounded" style="background: #3b82f6;"></span>
          <span class="text-surface-400">{ticker} Price</span>
        </div>
        <div class="flex items-center gap-1">
          <span class="w-3 h-3 rounded" style="background: {regionColors.redSea};"></span>
          <span class="text-surface-400">Red Sea</span>
        </div>
        <div class="flex items-center gap-1">
          <span class="w-3 h-3 rounded" style="background: {regionColors.persianGulf};"></span>
          <span class="text-surface-400">Persian Gulf</span>
        </div>
        <div class="flex items-center gap-1">
          <span class="w-3 h-3 rounded" style="background: {regionColors.malacca};"></span>
          <span class="text-surface-400">Malacca</span>
        </div>
      </div>
    {:else}
      <div class="flex items-center justify-center h-full text-surface-500">
        <span>No financial data available</span>
      </div>
    {/if}
  </div>
</div>
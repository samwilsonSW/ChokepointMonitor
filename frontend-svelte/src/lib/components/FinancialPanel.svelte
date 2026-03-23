<script>
  import { onMount } from 'svelte';
  import { scaleLinear, scaleBand } from 'd3-scale';
  import { line, area } from 'd3-shape';
  import { axisBottom, axisLeft, axisRight } from 'd3-axis';
  import { select } from 'd3-selection';

  export let chartData = [];
  export let ticker = 'USO';
  export let correlationStats = { r: 0, n: 0, interpretation: '' };

  let svgElement;
  let containerElement;
  let width = 800;
  let height = 400;
  const margin = { top: 20, right: 60, bottom: 50, left: 60 };

  // Color scheme for regions
  const regionColors = {
    redSea: '#ef4444',      // Red-500
    persianGulf: '#f97316', // Orange-500
    malacca: '#22c55e'      // Green-500
  };

  // Resize observer for responsive chart
  onMount(() => {
    if (!containerElement) return;

    const resizeObserver = new ResizeObserver(entries => {
      for (const entry of entries) {
        width = entry.contentRect.width;
        height = Math.max(300, entry.contentRect.height);
      }
    });

    resizeObserver.observe(containerElement);
    return () => resizeObserver.disconnect();
  });

  $: if (svgElement && chartData.length > 0) {
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
      .domain(chartData.map(d => d.date))
      .range([0, innerWidth])
      .padding(0.2);

    const yPriceScale = scaleLinear()
      .domain([
        Math.min(...chartData.map(d => d.price)) * 0.95,
        Math.max(...chartData.map(d => d.price)) * 1.05
      ])
      .range([innerHeight, 0]);

    const maxEvents = Math.max(...chartData.map(d =>
      d.redSeaEvents + d.persianGulfEvents + d.malaccaEvents
    ), 1);

    const yEventsScale = scaleLinear()
      .domain([0, maxEvents * 1.2])
      .range([innerHeight, 0]);

    // Price line
    const priceLine = line()
      .x(d => (xScale(d.date) || 0) + xScale.bandwidth() / 2)
      .y(d => yPriceScale(d.price));

    // Stacked bar data preparation
    const barWidth = Math.max(4, xScale.bandwidth() * 0.6);

    // Grid lines (horizontal)
    g.append('g')
      .attr('class', 'grid')
      .call(axisLeft(yPriceScale)
        .tickSize(-innerWidth)
        .tickFormat('')
      )
      .selectAll('line')
      .attr('stroke', 'rgba(255,255,255,0.1)');

    g.select('.grid').select('.domain').remove();

    // Stacked bars for events by region
    chartData.forEach(d => {
      const x = (xScale(d.date) || 0) + (xScale.bandwidth() - barWidth) / 2;
      let yOffset = innerHeight;

      // Red Sea events (bottom)
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

      // Persian Gulf events (middle)
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

      // Malacca events (top)
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

    // Price line (on top of bars)
    g.append('path')
      .datum(chartData)
      .attr('fill', 'none')
      .attr('stroke', '#3b82f6') // Blue-500
      .attr('stroke-width', 2)
      .attr('d', priceLine);

    // Price dots
    g.selectAll('.price-dot')
      .data(chartData)
      .enter()
      .append('circle')
      .attr('class', 'price-dot')
      .attr('cx', d => (xScale(d.date) || 0) + xScale.bandwidth() / 2)
      .attr('cy', d => yPriceScale(d.price))
      .attr('r', 3)
      .attr('fill', '#3b82f6');

    // X Axis (dates)
    const xAxis = g.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(axisBottom(xScale)
        .tickValues(xScale.domain().filter((_, i) => i % Math.ceil(chartData.length / 8) === 0))
        .tickFormat(d => {
          const date = new Date(d);
          return `${date.getMonth() + 1}/${date.getFullYear().toString().slice(2)}`;
        })
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

    // Right Y Axis (Events) - always show, even with 0 events
    const yEventsAxis = g.append('g')
      .attr('transform', `translate(${innerWidth},0)`)
      .call(axisRight(yEventsScale).ticks(6).tickFormat(d => Math.round(d)));

    yEventsAxis.selectAll('text')
      .attr('fill', '#fbbf24')  // Amber-400 for visibility
      .attr('font-size', '11px');
    yEventsAxis.select('.domain').attr('stroke', '#fbbf24');
    yEventsAxis.selectAll('.tick line').attr('stroke', '#fbbf24').attr('opacity', 0.5);

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
</script>

<div class="financial-panel h-full flex flex-col bg-surface-900 border-l border-surface-700">
  <!-- Header -->
  <div class="p-4 border-b border-surface-700">
    <h2 class="text-lg font-bold text-white">Financial Analysis</h2>
  </div>

  <!-- Controls -->
  <div class="p-4 border-b border-surface-700 space-y-3">
    <slot name="controls" />
  </div>

  <!-- Stats -->
  <div class="px-4 py-2 border-b border-surface-700 bg-surface-800">
    <div class="flex justify-between items-center text-sm">
      <div class="flex gap-4">
        <span class="text-surface-400">
          Correlation: <span class="text-white font-mono">{correlationStats.r}</span>
        </span>
        <span class="text-surface-400">
          n = <span class="text-white font-mono">{correlationStats.n}</span>
        </span>
      </div>
      <span class="text-xs text-surface-500">{correlationStats.interpretation}</span>
    </div>
  </div>

  <!-- Chart Container -->
  <div class="flex-1 min-h-0 p-4 w-full" bind:this={containerElement}>
    {#if chartData.length > 0}
      <svg bind:this={svgElement} width={width} height={height} class="w-full h-full">
        <!-- Chart rendered here -->
      </svg>

      <!-- Legend -->
      <div class="flex justify-center gap-4 mt-2 text-xs">
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
        <span>No data available for selected range</span>
      </div>
    {/if}
  </div>
</div>

<script>
  export let name = '';
  export let eventCount = 0;
  export let fatalities = 0;
  export let riskLevel = 'low';
  export let lastEventDate = null;
  
  const riskColors = {
    high: 'preset-filled-error-500',
    medium: 'preset-filled-warning-500', 
    low: 'preset-filled-success-500'
  };
  
  $: riskClass = riskColors[riskLevel] || 'preset-filled-surface-500';
</script>

<div class="card preset-filled-surface-100 p-4 min-w-[240px]">
  <h3 class="font-bold text-xl text-surface-900 mb-3">{name}</h3>
  
  <div class="grid grid-cols-2 gap-2 mb-3">
    <div class="preset-tonal-surface p-2 rounded text-center">
      <div class="font-bold text-lg text-surface-900">{eventCount}</div>
      <div class="text-xs text-surface-500 uppercase">Events</div>
    </div>
    <div class="preset-tonal-surface p-2 rounded text-center">
      <div class="font-bold text-lg text-surface-900">{fatalities}</div>
      <div class="text-xs text-surface-500 uppercase">Fatalities</div>
    </div>
  </div>
  
  <span class="badge {riskClass} text-xs uppercase font-bold">
    {riskLevel} Risk
  </span>
  
  {#if lastEventDate}
    <div class="text-sm text-surface-500 mt-2">
      Last event: {lastEventDate}
    </div>
  {/if}
</div>

<script>
  export let events = [];
  
  $: eventCount = events.length;
  // Get country from first event (all should be same location)
  $: country = events[0]?.properties?.country || events[0]?.properties?.admin1 || 'Unknown Location';
  $: coordinates = events[0]?.geometry?.coordinates || [];
  $: admin = events[0]?.properties?.country_admin || 'Unknown Admin';
  $: firstEventDate = events[events.length - 1]?.properties?.week || 'Unknown Date';
</script>

<div class="h-full flex flex-col">
  <!-- Country Header - Big and prominent -->
  <div class="mb-4 pb-4 border-b border-surface-700">
    <h2 class="text-2xl font-bold text-white mb-1">{country} - {admin}</h2>
    {#if coordinates.length === 2}
      <p class="text-xs text-surface-300 font-mono">
        {coordinates[1].toFixed(4)}, {coordinates[0].toFixed(4)}
      </p>
    {/if}
    <p class="text-sm text-surface-400 mt-2">
      {eventCount} event{eventCount > 1 ? 's' : ''} at this location since {firstEventDate}
    </p>
  </div>
  <div class="flex-1 overflow-y-auto space-y-3">
    {#each events as event}
      {@const props = event.properties}
      <div class="preset-tonal-surface p-3 rounded-lg border-l-[3px] border-l-surface-300">
        <div class="font-semibold text-surface-100 text-sm">
          {props.event_type || 'Conflict Event'}
        </div>
        <div class="flex gap-4 mt-1 text-xs text-surface-600">
          <span>📅 {props.week || 'Unknown'}</span>
          <span>💀 {props.fatalities || 0} fatalities</span>
        </div>
        {#if props.sub_event_type}
          <div class="text-xs text-surface-500 italic mt-1">
            {props.sub_event_type}
          </div>
        {/if}
      </div>
    {/each}
  </div>
</div>

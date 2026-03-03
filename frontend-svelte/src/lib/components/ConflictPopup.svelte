<script>
  export let events = [];
  
  $: eventCount = events.length;
</script>

<div class="card preset-filled-surface-100 p-4 min-w-[300px] max-h-[320px] overflow-y-auto">
  <header class="pb-3 mb-3 border-b border-surface-300">
    <h3 class="font-bold text-primary-500">
      {eventCount} Event{eventCount > 1 ? 's' : ''} at this location
    </h3>
  </header>
  
  <div class="flex flex-col gap-3">
    {#each events as event}
      {@const props = event.properties}
      <div class="preset-tonal-surface p-3 rounded-lg border-l-[3px] border-l-primary-500">
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

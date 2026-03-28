<script>
  /**
   * Simple dual-thumb range slider
   * Props:
   * - value: [min, max] array
   * - min: number
   * - max: number  
   * - onChange: function called with { value: [min, max] }
   * - ticks: array of { value, label } for markers (optional)
   * - thumbLabels: [label1, label2] for tooltips (optional)
   */
  let { value = [0, 100], min = 0, max = 100, onChange, ticks = [], thumbLabels = ['', ''] } = $props();
  
  let sliderEl = $state(null);
  let dragging = $state(null); // 0 or 1 for which thumb
  
  function percent(val) {
    return ((val - min) / (max - min)) * 100;
  }
  
  function valueFromPercent(pct) {
    return min + (pct / 100) * (max - min);
  }
  
  function handlePointerDown(e, index) {
    e.preventDefault();
    dragging = index;
    
    function handleMove(e) {
      if (!sliderEl) return;
      const rect = sliderEl.getBoundingClientRect();
      const pct = Math.max(0, Math.min(100, ((e.clientX - rect.left) / rect.width) * 100));
      const newVal = Math.round(valueFromPercent(pct));
      
      const newValues = [...value];
      // Constrain: left thumb can't pass right, right can't pass left
      if (index === 0) {
        newValues[0] = Math.min(newVal, value[1]);
      } else {
        newValues[1] = Math.max(newVal, value[0]);
      }
      
      if (onChange) onChange({ value: newValues });
    }
    
    function handleUp() {
      dragging = null;
      window.removeEventListener('pointermove', handleMove);
      window.removeEventListener('pointerup', handleUp);
    }
    
    window.addEventListener('pointermove', handleMove);
    window.addEventListener('pointerup', handleUp);
  }
  
  function handleTrackClick(e) {
    if (!sliderEl) return;
    const rect = sliderEl.getBoundingClientRect();
    const pct = ((e.clientX - rect.left) / rect.width) * 100;
    const clickVal = valueFromPercent(pct);
    
    // Move the closest thumb
    const dist0 = Math.abs(clickVal - value[0]);
    const dist1 = Math.abs(clickVal - value[1]);
    
    const newValues = [...value];
    if (dist0 < dist1) {
      newValues[0] = Math.min(Math.round(clickVal), value[1]);
    } else {
      newValues[1] = Math.max(Math.round(clickVal), value[0]);
    }
    
    if (onChange) onChange({ value: newValues });
  }
</script>

<div class="w-full">
  <!-- Track -->
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div 
    bind:this={sliderEl}
    class="relative h-2 bg-surface-600 rounded-full cursor-pointer"
    onclick={handleTrackClick}
  >
    <!-- Selected range -->
    <div 
      class="absolute h-2 bg-primary-500 rounded-full"
      style="left: {percent(value[0])}%; width: {percent(value[1]) - percent(value[0])}%"
    ></div>
    
    <!-- Thumb 0 -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
      class="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-primary-500 rounded-full border-2 border-surface-900 cursor-grab active:cursor-grabbing group"
      style="left: {percent(value[0])}%; transform: translate(-50%, -50%)"
      onpointerdown={(e) => handlePointerDown(e, 0)}
      role="slider"
      aria-valuemin={min}
      aria-valuemax={max}
      aria-valuenow={value[0]}
      tabindex="0"
    >
      <!-- Tooltip -->
      {#if thumbLabels[0]}
        <span class="absolute -top-7 left-1/2 -translate-x-1/2 bg-surface-700 text-surface-100 text-xs px-2 py-0.5 rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
          {thumbLabels[0]}
        </span>
      {/if}
    </div>
    
    <!-- Thumb 1 -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
      class="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-primary-500 rounded-full border-2 border-surface-900 cursor-grab active:cursor-grabbing group"
      style="left: {percent(value[1])}%; transform: translate(-50%, -50%)"
      onpointerdown={(e) => handlePointerDown(e, 1)}
      role="slider"
      aria-valuemin={min}
      aria-valuemax={max}
      aria-valuenow={value[1]}
      tabindex="0"
    >
      <!-- Tooltip -->
      {#if thumbLabels[1]}
        <span class="absolute -top-7 left-1/2 -translate-x-1/2 bg-surface-700 text-surface-100 text-xs px-2 py-0.5 rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
          {thumbLabels[1]}
        </span>
      {/if}
    </div>
  </div>
  
  <!-- Ticks/Markers -->
  {#if ticks.length > 0}
    <div class="relative h-6 mt-1">
      {#each ticks as tick}
        <span 
          class="absolute text-xs text-surface-400 whitespace-nowrap transform -translate-x-1/2"
          style="left: {percent(tick.value)}%"
        >
          {tick.label}
        </span>
      {/each}
    </div>
  {/if}
</div>

# UI Enhancements Roadmap

> Non-urgent UI improvements to tackle after core features are stable.
> Last updated: 2026-03-08

## Date Slider Improvements

### 1. Week-Based Steps
**Current:** Slider steps by individual days  
**Desired:** Step by weeks (matching ACLED data granularity)  
**Why:** ACLED data is weekly aggregated, so day-level precision is misleading

### 2. Editable Date Range Input
**Current:** Static text showing "MM/DD/YYYY - MM/DD/YYYY"  
**Desired:** Click-to-edit input field with the same format  
**Why:** Power users can type exact dates instead of fiddling with slider

---

## Visual Design Overhaul

### 3. Modernize Theme (Less Flat)
**Current:** Flat, utilitarian Skeleton default theme  
**Desired:** More depth, subtle shadows, layered cards, refined typography  
**Notes:** 
- Keep it professional (this is a geopolitical tool, not a game)
- Consider subtle glassmorphism for overlays
- Better visual hierarchy between map and controls

### 4. Color Scheme Refresh
**Current:** Default Skeleton slate/surface colors  
**Desired:** Distinctive palette that fits "global conflict/maritime" theme  
**Ideas:**
- Deep navy/slate base (maritime feel)
- Amber/crimson accents for alerts/high-risk areas
- Better contrast for accessibility

---

## Drawer/Detail Panel

### 5. Richer Conflict Details
**Current:** Basic event list in drawer  
**Desired:** More contextual information per event:
- [ ] Event timeline/chronology view
- [ ] Related events clustering ("this is part of a series of 12 events")
- [ ] Source links to ACLED for verification
- [ ] Trend indicators (increasing/decreasing conflict in this region)
- [ ] Quick-filter buttons ("show all events from this country")

### 6. Chokepoint-Specific Insights
**Current:** Generic event list  
**Desired:** Chokepoint-aware analysis:
- [ ] "Why this matters" context per chokepoint
- [ ] Historical baseline comparison ("2x normal activity")
- [ ] Vessel traffic impact estimates (when AIS data available)

---

## Polish Items

- [ ] Loading states/transitions (currently abrupt)
- [ ] Empty state messaging (no conflicts in selected range)
- [ ] Keyboard shortcuts (arrow keys for date navigation?)
- [ ] Mobile responsive refinements (drawer behavior on small screens)

---

## Completed ✓

- [x] Date slider styling (quarterly labels, floating date tooltips, mm/dd/yyyy format)
- [x] Client-side recency calculation (consistent heatmap regardless of dataset size)

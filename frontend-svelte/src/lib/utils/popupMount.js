import { mount, unmount } from 'svelte';

/**
 * Mount a Svelte component to a DOM element for MapLibre popup
 * @param {typeof SvelteComponent} Component - Svelte component class
 * @param {Object} props - Props to pass to component
 * @returns {HTMLElement} - Container element with mounted component
 */
export function mountPopupComponent(Component, props = {}) {
  const container = document.createElement('div');
  const component = mount(Component, {
    target: container,
    props
  });
  
  // Store reference for cleanup
  container._svelteComponent = component;
  
  return container;
}

/**
 * Cleanup a mounted popup component
 * @param {HTMLElement} container 
 */
export function unmountPopupComponent(container) {
  if (container?._svelteComponent) {
    unmount(container._svelteComponent);
    delete container._svelteComponent;
  }
}

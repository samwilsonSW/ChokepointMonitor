import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'
import tailwindcss from "@tailwindcss/vite"

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    tailwindcss(),
    svelte()
  ],
  // Point to the root directory to find the unified .env file
  envDir: '../', 
  server: {
    proxy: {
      '/conflicts': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/chokepoint-metrics': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/chokepoint-regions': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
});
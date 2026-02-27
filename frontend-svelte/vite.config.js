import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'
import tailwindcss from "@tailwindcss/vite"

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    tailwindcss(),
    svelte()
  ],
  server: {
    proxy: {
      // When the frontend asks for /conflicts, Vite grabs it from port 8000
      '/conflicts': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/chokepoint-metrics': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
});
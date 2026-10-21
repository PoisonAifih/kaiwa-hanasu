import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// API proxy
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})

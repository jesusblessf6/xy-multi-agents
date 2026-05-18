import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/requirements': 'http://localhost:8001',
      '/projects': 'http://localhost:8001',
      '/pipeline': 'http://localhost:8001',
      '/agents': 'http://localhost:8001',
      '/health': 'http://localhost:8001',
    },
  },
})

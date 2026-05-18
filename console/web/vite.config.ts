import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3001,
    proxy: {
      '/auth': 'http://localhost:8002',
      '/agents': 'http://localhost:8002',
      '/reviews': 'http://localhost:8002',
      '/projects': 'http://localhost:8002',
      '/dashboard': 'http://localhost:8002',
      '/users': 'http://localhost:8002',
      '/health': 'http://localhost:8002',
    },
  },
})

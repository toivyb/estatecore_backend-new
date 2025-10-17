import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3006,
    host: true,
    allowedHosts: ['localhost', '127.0.0.1', 'fssphq.fsspcctv.org'],
    proxy: {
      '/api': {
        target: 'http://localhost:5009',
        changeOrigin: true,
        secure: false,
      },
      '/dashboard': {
        target: 'http://localhost:5009',
        changeOrigin: true,
        secure: false,
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets'
  }
})
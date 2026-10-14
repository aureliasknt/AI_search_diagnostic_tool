import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: true,          // dengar di semua interface (bisa diakses HP lewat IP LAN)
    allowedHosts: true,  // izinkan akses via hostname tunnel publik (trycloudflare dsb.)
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})

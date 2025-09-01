// frontend/vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)), // ← alias '@/...'
    },
  },
  server: {
    port: 5173,
    proxy: {
      // всё, что начинается на /users, /wallet, /predictions, /themes, /tasks —
      // переписываем в /api/...
      //'^/(users|wallet|predictions|themes|tasks)': {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        //rewrite: (path) => `/api${path}`,
      },
    },
  },
})

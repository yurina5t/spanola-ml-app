// frontend/vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // всё, что начинается на /users, /wallet, /predictions, /themes, /tasks —
      // переписываем в /api/...
      '^/(users|wallet|predictions|themes|tasks)': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => `/api${path}`,
      },
    },
  },
})

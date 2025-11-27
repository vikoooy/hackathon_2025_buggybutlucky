import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: [['babel-plugin-react-compiler']],
      },
    }),
    tailwindcss(),
  ],

  server: {
    port: 3001,
    proxy: {
      "/audio": {
        target: "http://192.168.1.129:8000",
        changeOrigin: true,
        secure: false,
      },
    },
  },
})

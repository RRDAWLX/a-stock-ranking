import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { readFileSync } from 'fs'

const config = JSON.parse(readFileSync(new URL('../config.json', import.meta.url), 'utf-8'))

export default defineConfig({
  plugins: [react()],
  server: {
    port: config.frontend.port
  },
  define: {
    __BACKEND_PORT__: JSON.stringify(config.backend.port),
    // 支持环境变量配置后端主机地址
    __BACKEND_HOST__: JSON.stringify(process.env.VITE_BACKEND_HOST || 'localhost')
  }
})
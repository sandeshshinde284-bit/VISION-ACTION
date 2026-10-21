import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import path from 'node:path'

// Resolve absolute OS paths for backend data writes on Sandesh's Windows system
// This is critical because Vite/Chokidar resolves paths absolutely and bypasses relative ignores!
const backendDir = path.resolve(__dirname, '../backend')
const dataDir = path.resolve(__dirname, '../data')
const tempDir = path.resolve(__dirname, '../temp_docs')

// https://vite.dev/config/
export default defineConfig({
  base: './',
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    watch: {
      // Forcefully ignore absolute paths to prevent any HMR reloads on local database writes
      ignored: [
        `${backendDir}/**`,
        `${dataDir}/**`,
        `${tempDir}/**`
      ]
    }
  }
})

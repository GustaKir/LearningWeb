import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from '@vue/cli-service'
import path from 'path'

export default defineConfig({
  transpileDependencies: true,
  devServer: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  configureWebpack: {
    resolve: {
      extensions: ['.js', '.vue', '.json'],
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    }
  }
}) 
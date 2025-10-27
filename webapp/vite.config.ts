import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
// import { VitePWA } from 'vite-plugin-pwa' // Disabled for Telegram Mini Apps
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  base: '/webapp/',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  plugins: [
    react(),
    // PWA disabled for Telegram Mini Apps - service workers can interfere with Telegram's iframe
    // VitePWA({
    //   registerType: 'autoUpdate',
    //   injectRegister: false,
    //   devOptions: {
    //     enabled: false,
    //   },
    //   workbox: {
    //     clientsClaim: true,
    //     skipWaiting: true,
    //     cleanupOutdatedCaches: true,
    //   },
    //   manifest: {
    //     name: 'Pirates Expedition Mini App',
    //     short_name: 'Pirates Expedition',
    //     description: 'Telegram Mini App for Pirates Expedition Management',
    //     theme_color: '#8B4513',
    //     background_color: '#F5DEB3',
    //     display: 'standalone',
    //     orientation: 'portrait',
    //     scope: '/webapp/',
    //     start_url: '/webapp/',
    //     icons: [
    //       {
    //         src: '/webapp/pirate-icon-192.png',
    //         sizes: '192x192',
    //         type: 'image/png'
    //       },
    //       {
    //         src: '/webapp/pirate-icon-512.png',
    //         sizes: '512x512',
    //         type: 'image/png'
    //       }
    //     ]
    //   }
    // })
  ],
  define: {
    global: 'globalThis',
    'process.env': {},
    'import.meta.env.VITE_API_URL': JSON.stringify(process.env.VITE_API_URL || ''),
  },
  optimizeDeps: {
    esbuildOptions: {
      define: {
        global: 'globalThis',
      },
    },
    include: ['socket.io-client'],
  },
  server: {
    host: true,
    port: 3000,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        secure: false,
      },
      '/health': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        secure: false,
      },
      '/socket.io': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        secure: false,
        ws: true,
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    commonjsOptions: {
      transformMixedEsModules: true,
    },
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['react', 'react-dom'],
          'ui': ['styled-components', 'framer-motion'],
          'charts': ['recharts'],
          'telegram': ['@telegram-apps/sdk'],
          'websocket': ['socket.io-client']
        },
        // Add globals to prevent undefined destructuring
        globals: {
          Request: 'Request',
          Response: 'Response'
        }
      }
    },
    // Target modern browsers that support Fetch API
    target: 'esnext',
    // Polyfill node globals
    polyfillModulePreload: true
  }
})
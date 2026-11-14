import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { viteStaticCopy } from 'vite-plugin-static-copy'

const CESIUM_SOURCE = 'node_modules/cesium/Build/Cesium'
// Cesium loads its workers, assets and widgets at runtime from this path.
// stripBase: 4 drops 'node_modules/cesium/Build/Cesium' from the copied paths.
const CESIUM_BASE_URL = 'cesium'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    viteStaticCopy({
      targets: [
        { src: `${CESIUM_SOURCE}/ThirdParty`, dest: CESIUM_BASE_URL, rename: { stripBase: 4 } },
        { src: `${CESIUM_SOURCE}/Workers`, dest: CESIUM_BASE_URL, rename: { stripBase: 4 } },
        { src: `${CESIUM_SOURCE}/Assets`, dest: CESIUM_BASE_URL, rename: { stripBase: 4 } },
        { src: `${CESIUM_SOURCE}/Widgets`, dest: CESIUM_BASE_URL, rename: { stripBase: 4 } },
      ],
    }),
  ],
  define: {
    CESIUM_BASE_URL: JSON.stringify(`/${CESIUM_BASE_URL}`),
  },
  build: {
    // CesiumJS is a large library; it is split into its own chunk.
    chunkSizeWarningLimit: 6000,
  },
})

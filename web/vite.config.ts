// Raphi web SOLA (y la que muestra el escritorio): la cáscara mínima de Tiqsi con el módulo web de Raphi, que sirven
// raphi.sola o raphi.escritorio (web/dist). Desde la raíz: `npm run web:construir` (o `npm run web` con la API en 8040).
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const aqui = (ruta: string) => fileURLToPath(new URL(ruta, import.meta.url))

export default defineConfig({
  root: aqui('./sola'),
  plugins: [react()],
  // Tiqsi web llega por enlace: sin seguirlo, sus importaciones de React y MUI se resuelven aquí (una sola copia).
  resolve: { preserveSymlinks: true },
  build: { outDir: aqui('./dist'), emptyOutDir: true, chunkSizeWarningLimit: 1600 },
  server: { port: 5340, strictPort: true, proxy: { '/api': { target: 'http://127.0.0.1:8040', ws: true } } },
})

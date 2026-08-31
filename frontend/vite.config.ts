import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/projects': 'http://localhost:8080',
      '/healthz': 'http://localhost:8080',
      '/assets/upload-url': 'http://localhost:8080',
      '/worker': 'http://localhost:8080',
    },
  },
  preview: {
    port: 4173,
    host: '127.0.0.1',
  },
  build: {
    assetsDir: 'app-assets',
    outDir: 'dist',
    emptyOutDir: true,
  },
});

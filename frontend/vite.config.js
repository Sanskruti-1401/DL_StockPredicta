import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath } from 'url';
import { dirname } from 'path';
var __dirname = dirname(fileURLToPath(import.meta.url));
export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            '@': "".concat(__dirname, "/src"),
        },
    },
    server: {
        port: 3000,
        open: true,
        proxy: {
            '/api': {
                target: process.env.VITE_API_URL || 'http://localhost:8000',
                changeOrigin: true,
                rewrite: function (path) { return path.replace(/^\/api/, ''); },
            },
        },
    },
    build: {
        outDir: 'dist',
        sourcemap: false,
        minify: 'terser',
        terserOptions: {
            compress: {
                drop_console: true,
            },
        },
    },
    define: {
        'process.env.REACT_APP_API_URL': JSON.stringify(process.env.VITE_API_URL || 'http://localhost:8000'),
    },
});

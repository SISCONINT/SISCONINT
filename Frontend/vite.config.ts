import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "node:path";

export default defineConfig(({mode})=>{
  const env = loadEnv(mode, process.cwd(), '');

  return{
    plugins: [react(), tailwindcss()],
    resolve: { alias: { "@": path.resolve(__dirname, "src") } },
    server: {
      proxy: {
        "/api": {
          target: env.VITE_BACK_URL || 'https://sisconint-backend.onrender.com',
          changeOrigin: true
        },
      },
    },
  }
});
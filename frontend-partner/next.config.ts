import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* Stability fixes for dev mode */
  experimental: {
    // Disable Turbopack if it's causing crashes on Windows
    // turbo: false, 
  },
  // Restrict scanning to the project directory
  typescript: {
    ignoreBuildErrors: true, 
  },
};

export default nextConfig;

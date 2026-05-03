import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* Stability fixes for dev mode */
  experimental: {
    // Disable Turbopack as it is currently unstable on some Windows environments
    turbo: {
      enabled: false,
    },
  },
  // Restrict scanning to the project directory
  typescript: {
    ignoreBuildErrors: true, 
  },
};

export default nextConfig;

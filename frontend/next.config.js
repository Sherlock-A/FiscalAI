/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,
  // Webpack config for MapLibre GL (canvas dependency)
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      canvas: false,
    };
    return config;
  },
};

module.exports = nextConfig;

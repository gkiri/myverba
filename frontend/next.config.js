/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'export',
    // Disable server-side features when exporting
    images: {
      unoptimized: true,
    },
    // Disable API routes
    rewrites: () => [],
  };
  
  // Set assetPrefix only in production/export mode
  if (process.env.NODE_ENV === 'production') {
    nextConfig.assetPrefix = '/static';
  }
  
  module.exports = nextConfig;
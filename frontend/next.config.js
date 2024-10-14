/** @type {import('next').NextConfig} */
const nextConfig = {
    // Disable server-side features when exporting
    images: {
      unoptimized: true,
    },
    // Remove rewrites configuration as it's not compatible with static export
};

// Set assetPrefix only in production/export mode
if (process.env.NODE_ENV === 'production') {
    nextConfig.assetPrefix = '/static';
}

module.exports = nextConfig;

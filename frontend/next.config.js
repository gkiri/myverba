/** @type {import('next').NextConfig} */
const nextConfig = {
    // "output": "export", // This line is removed or commented out
    assetPrefix: process.env.NODE_ENV === 'production' ? '/static' : '', // Directly assign assetPrefix
};

module.exports = nextConfig; 
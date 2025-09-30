#!/bin/bash
set -e

echo "=== EstateCore Frontend Build Script ==="
echo "Node version: $(node --version)"
echo "NPM version: $(npm --version)"
echo "Current directory: $(pwd)"

# Navigate to frontend directory
echo "Changing to frontend directory..."
cd estatecore_frontend

echo "Installing dependencies..."
npm ci --prefer-offline --no-audit

echo "Setting environment variables..."
export NODE_ENV=production
export VITE_API_BASE_URL=${VITE_API_BASE_URL:-"https://estatecore-backend-sujs.onrender.com"}

echo "Building React application..."
npm run build

echo "Verifying build output..."
if [ -d "dist" ]; then
    echo "✅ Build successful! Output directory created."
    ls -la dist/
else
    echo "❌ Build failed! No dist directory found."
    exit 1
fi

echo "=== Build Complete ==="
#!/bin/bash
# Render Frontend Build Script for EstateCore

echo "Starting EstateCore Frontend Build..."
echo "Current directory: $(pwd)"
echo "Node version: $(node --version)"
echo "NPM version: $(npm --version)"

# Change to frontend directory
echo "Changing to frontend directory..."
cd estatecore_frontend || {
    echo "Error: estatecore_frontend directory not found!"
    exit 1
}

echo "Frontend directory contents:"
ls -la

# Install dependencies
echo "Installing dependencies..."
npm ci --only=production || npm install

# Set production environment
export NODE_ENV=production
export VITE_API_BASE_URL=${VITE_API_BASE_URL:-"https://estatecore-backend-sujs.onrender.com"}

echo "Environment variables:"
echo "NODE_ENV: $NODE_ENV"
echo "VITE_API_BASE_URL: $VITE_API_BASE_URL"

# Build the application
echo "Building React application..."
npm run build

echo "Build completed!"
echo "Checking build output..."
if [ -d "dist" ]; then
    echo "Build output directory:"
    ls -la dist/
    echo "Index.html size: $(du -h dist/index.html 2>/dev/null || echo 'not found')"
else
    echo "Error: dist directory not found after build!"
    exit 1
fi

echo "Frontend build successful! 🚀"
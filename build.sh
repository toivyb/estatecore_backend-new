#!/bin/bash
# Force Node.js build for Netlify

echo "Starting build process..."
echo "Current directory: $(pwd)"
echo "Directory contents: $(ls -la)"

# Change to frontend directory
cd estatecore_frontend || exit 1

echo "Frontend directory contents: $(ls -la)"

# Install dependencies
echo "Installing dependencies..."
npm install

# Build the application
echo "Building application..."
npm run build

echo "Build completed!"
echo "Build output directory:"
ls -la dist/
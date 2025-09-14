#!/bin/bash

# EstateCore Appwrite Functions Deployment Script
# Prerequisites: Appwrite CLI installed and logged in

PROJECT_ID="68b6e4240013f757c47b"
ENDPOINT="https://nyc.cloud.appwrite.io/v1"

echo "🚀 Deploying EstateCore Appwrite Functions..."
echo "Project ID: $PROJECT_ID"
echo "Endpoint: $ENDPOINT"
echo ""

# Set the client configuration
echo "📱 Configuring Appwrite client..."
appwrite client --endpoint $ENDPOINT --projectId $PROJECT_ID

# Function 1: Dashboard Metrics
echo ""
echo "📊 Deploying dashboard-metrics function..."
cd functions/dashboard-metrics
appwrite functions create \
    --functionId "dashboard-metrics" \
    --name "Dashboard Metrics" \
    --runtime "node-19.0" \
    --execute "users" \
    --events "" \
    --schedule "" \
    --timeout 30 \
    --enabled true

appwrite functions createDeployment \
    --functionId "dashboard-metrics" \
    --entrypoint "src/main.js" \
    --code . \
    --activate true

cd ../..

# Function 2: Camera Stream Control
echo ""
echo "📹 Deploying camera-stream-control function..."
cd functions/camera-stream-control
appwrite functions create \
    --functionId "camera-stream-control" \
    --name "Camera Stream Control" \
    --runtime "node-19.0" \
    --execute "users" \
    --events "" \
    --schedule "" \
    --timeout 30 \
    --enabled true

appwrite functions createDeployment \
    --functionId "camera-stream-control" \
    --entrypoint "src/main.js" \
    --code . \
    --activate true

cd ../..

# Function 3: Door Control
echo ""
echo "🚪 Deploying door-control function..."
cd functions/door-control
appwrite functions create \
    --functionId "door-control" \
    --name "Door Control" \
    --runtime "node-19.0" \
    --execute "users" \
    --events "" \
    --schedule "" \
    --timeout 30 \
    --enabled true

appwrite functions createDeployment \
    --functionId "door-control" \
    --entrypoint "src/main.js" \
    --code . \
    --activate true

cd ../..

# Function 4: Tenant Access Status
echo ""
echo "👤 Deploying tenant-access-status function..."
cd functions/tenant-access-status
appwrite functions create \
    --functionId "tenant-access-status" \
    --name "Tenant Access Status" \
    --runtime "node-19.0" \
    --execute "users" \
    --events "" \
    --schedule "" \
    --timeout 30 \
    --enabled true

appwrite functions createDeployment \
    --functionId "tenant-access-status" \
    --entrypoint "src/main.js" \
    --code . \
    --activate true

cd ../..

echo ""
echo "✅ All functions deployed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Go to your Appwrite Console: https://cloud.appwrite.io"
echo "2. Navigate to Functions and verify all 4 functions are deployed"
echo "3. Test each function using the Appwrite Console"
echo "4. Configure environment variables if needed"
echo "5. Set up your database collections using setup-appwrite.js"
echo "6. Deploy your frontend to Netlify"
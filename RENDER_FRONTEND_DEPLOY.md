# EstateCore Frontend Deployment to Render

## Quick Setup Instructions

### Step 1: Create New Static Site on Render

1. Go to [render.com](https://render.com)
2. Click **"New +"** → **"Static Site"**
3. Connect your GitHub repository: `toivyb/estatecore_backend-new`

### Step 2: Configure Build Settings

**Basic Settings:**
```
Name: estatecore-frontend
Branch: master
Build Command: cd estatecore_frontend && npm ci && npm run build
Publish Directory: estatecore_frontend/dist
```

**Environment Variables:**
```
NODE_VERSION = 18
VITE_API_BASE_URL = https://estatecore-backend-sujs.onrender.com
NODE_ENV = production
```

### Step 3: Advanced Settings (Optional)

**Custom Headers:**
```
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
```

**Redirects for SPA:**
```
/*    /index.html   200
```

## Alternative: Using render.yaml

If you prefer infrastructure-as-code, use the `render-frontend.yaml` file:

1. Rename `render-frontend.yaml` to `render.yaml` (temporarily)
2. Deploy using Render's YAML configuration
3. Rename back after deployment

## Backend Connection

Your frontend will automatically connect to your existing backend at:
`https://estatecore-backend-sujs.onrender.com`

## Expected URLs

After deployment:
- **Frontend**: `https://estatecore-frontend.onrender.com`
- **Backend**: `https://estatecore-backend-sujs.onrender.com` (existing)

## Build Process

The build script will:
1. Install Node.js dependencies
2. Set production environment variables
3. Build React/Vite application
4. Output to `estatecore_frontend/dist/`

## Troubleshooting

**Common Issues:**
- Build fails: Check Node.js version is 18
- API errors: Verify backend URL in environment variables
- Routing issues: Ensure SPA redirects are configured

**Debug Commands:**
```bash
# Test build locally
cd estatecore_frontend
npm install
npm run build

# Test production build
npm run preview
```

## Files Created for Render Deployment

- `render-frontend.yaml` - Render service configuration
- `build-frontend.sh` - Custom build script
- `.env.production` - Production environment variables
- `RENDER_FRONTEND_DEPLOY.md` - This deployment guide

Your EstateCore frontend will be accessible globally via Render! 🚀
# How to Push Backend to GitHub

Due to git permission issues in WSL, please run these commands manually in your terminal:

## Step 1: Clean up and initialize Git

```bash
cd /mnt/c/Users/toivy/estatecore_project/estatecore_backend

# Remove any corrupted git files
rm -rf .git

# Initialize new git repository
git init
git branch -M main
```

## Step 2: Configure Git (replace with your info)

```bash
git config user.name "Your Name"
git config user.email "your.email@gmail.com"
```

## Step 3: Add files and make first commit

```bash
# Add all files (the .gitignore will exclude unnecessary files)
git add .

# Make first commit
git commit -m "Initial backend deployment setup

- Production-ready Flask app with Gunicorn
- PostgreSQL database configuration  
- CORS setup for frontend communication
- Health check endpoint for monitoring
- Complete SaaS billing system
- Per-apartment pricing model
- Owner access controls
- Professional dashboard and client management
- All deployment files for Render.com"
```

## Step 4: Connect to GitHub repository

```bash
git remote add origin https://github.com/toivyb/estatecore_backend-new.git
```

## Step 5: Push to GitHub

```bash
git push -u origin main
```

## What's Included

✅ **Core Application**
- `app.py` - Main application entry point
- `app/` - Flask application structure
- `config.py` - Production configuration
- `requirements.txt` - All dependencies

✅ **Deployment Configuration**  
- `render.yaml` - Render deployment config
- `DEPLOYMENT.md` - Complete deployment guide
- `.env.example` - Environment template
- Health check endpoint

✅ **SaaS Features**
- Per-apartment billing ($15/unit/month)
- Client management system
- Subscription tracking
- Owner access controls

✅ **Database Models**
- SaaS subscription models
- Property and unit management
- Tenant and user models
- Financial tracking

✅ **API Routes**
- `/api/health` - Health check
- `/api/saas/*` - SaaS billing
- `/api/owner/*` - Owner access
- All existing functionality

After pushing, you can deploy directly on Render.com using the repository!

## Troubleshooting

If you get permission errors:
```bash
sudo chown -R $(whoami) /mnt/c/Users/toivy/estatecore_project/estatecore_backend/.git
```

If files are missing:
```bash
git add . --force
```
# EstateCore Deployment Guide

## Render Deployment

EstateCore is ready for deployment to Render with the following configuration:

### Files Created for Deployment

1. **app.py** - Production-ready Flask application
2. **render.yaml** - Render service configuration  
3. **Procfile** - Process configuration for web service
4. **requirements.txt** - Python dependencies
5. **database_setup.py** - Automatic database initialization
6. **database_connection.py** - Database access layer

### Deployment Steps

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Ready for Render deployment"
   git push origin main
   ```

2. **Deploy to Render**:
   - Go to [render.com](https://render.com)
   - Create new Web Service
   - Connect your GitHub repository
   - Choose: **estatecore_project**
   - Runtime: **Python 3**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn --bind 0.0.0.0:$PORT app:app`

3. **Environment Variables** (automatically set by render.yaml):
   - `PORT`: 10000 (set by Render)
   - `RENDER`: true (identifies production environment)
   - `PYTHON_VERSION`: 3.10.0

### API Endpoints (Production)

Once deployed, your API will be available at: `https://your-app-name.onrender.com`

**Core Endpoints**:
- `GET /` - API status and info
- `GET /health` - Health check for monitoring
- `GET /api/dashboard` - Dashboard metrics
- `GET /api/companies` - Company management
- `GET /api/properties` - Property data
- `GET /api/users` - User management
- `GET /api/tenants` - Tenant information
- `POST /api/auth/login` - Authentication

### Database

- **SQLite** database is automatically created on first startup
- Sample data is seeded with 4 companies, 9 users, 7 properties
- Data persists across deployments on Render

### Security Features

- CORS enabled for cross-origin requests
- Password hashing with SHA-256
- Role-based access control
- Foreign key constraints for data integrity

### Frontend Configuration

Update your frontend API configuration to use the Render URL:

```javascript
// In your React app's api.js or config
const API_BASE_URL = 'https://your-app-name.onrender.com';
```

### Monitoring

- Health check endpoint: `/health`
- Automatic database initialization
- Error logging and handling
- Production-optimized CORS settings

### Costs

- Render Starter Plan: **Free** (with limitations)
- Scales automatically based on usage
- Database included (SQLite)

Your EstateCore API will be accessible globally once deployed! 🚀
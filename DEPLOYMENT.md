# EstateCore Deployment Guide

## AWS Amplify Deployment

### Prerequisites
1. AWS Account with Amplify access
2. GitHub repository containing this code

### Frontend Deployment (Amplify)

1. **Connect Repository**
   - Go to AWS Amplify Console
   - Choose "Host web app"
   - Connect your GitHub repository
   - Select the main branch

2. **Build Configuration**
   - Amplify will auto-detect the build settings from `amplify.yml`
   - Or manually configure:
     - Build command: `npm run build`
     - Build output directory: `estatecore_frontend/dist`

3. **Environment Variables**
   Set these in Amplify Console > App Settings > Environment Variables:
   ```
   VITE_API_BASE=https://your-backend-url.com
   VITE_API_BASE_URL=https://your-backend-url.com
   ```

### Backend Deployment Options

#### Option 1: AWS App Runner
1. Go to AWS App Runner Console
2. Create service from source code
3. Connect to your repository
4. Configure:
   - Source directory: `estatecore_backend`
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn --bind 0.0.0.0:8000 wsgi:app`

#### Option 2: Heroku
1. Install Heroku CLI
2. Create Heroku app: `heroku create your-app-name`
3. Set environment variables:
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set DATABASE_URL=your-database-url
   ```
4. Deploy: `git subtree push --prefix estatecore_backend heroku main`

#### Option 3: Railway
1. Connect GitHub repository to Railway
2. Select `estatecore_backend` as root directory
3. Railway will auto-detect Python and deploy

### Database Setup

For production, set up a PostgreSQL database:
```bash
# Environment variables needed:
DATABASE_URL=postgresql://user:password@host:port/dbname
SECRET_KEY=your-secret-key
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### Final Steps

1. Update frontend environment variables with actual backend URL
2. Update CORS settings in backend to allow your Amplify domain
3. Test the deployed application
4. Set up SSL certificates (usually automatic with Amplify/Heroku)

## Local Development

```bash
# Backend
cd estatecore_backend
pip install -r requirements.txt
python wsgi.py

# Frontend (separate terminal)
cd estatecore_frontend
npm install
npm run dev
```

## Features Included
- ✅ User authentication and authorization
- ✅ Role-based dashboard system
- ✅ Complete rent management CRUD operations
- ✅ Payment tracking and status management
- ✅ Responsive UI with Tailwind CSS
- ✅ REST API with Flask backend
- ✅ Modern React frontend with routing

The application is production-ready with proper error handling, authentication, and a clean UI.
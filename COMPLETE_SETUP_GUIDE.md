# 🏢 EstateCore Complete Setup Guide

## 🎯 Overview
This guide will help you deploy your complete EstateCore property management system with Appwrite backend and Netlify frontend.

## 📋 Prerequisites
- Appwrite account: https://cloud.appwrite.io
- Netlify account: https://netlify.com
- GitHub repository with your code
- Node.js 20+ (for local development)
- Appwrite CLI: `npm install -g appwrite-cli`

---

## 🚀 Phase 1: Appwrite Backend Setup

### Step 1: Database Collections
Run the automated setup script:

```bash
# Install Appwrite CLI
npm install -g appwrite-cli

# Login to Appwrite
appwrite login

# Run the database setup script
node setup-appwrite.js
```

**Manual Alternative:** Use the detailed specifications in `APPWRITE_DATABASE_SETUP.md`

### Step 2: Deploy Functions
Deploy the 4 required Appwrite Functions:

```bash
# Make script executable (Linux/Mac)
chmod +x deploy-functions.sh

# Deploy all functions
./deploy-functions.sh
```

**Manual Alternative:** 
1. Go to Appwrite Console > Functions
2. Create each function using the code in the `functions/` directory
3. Set runtime to Node.js 19.0
4. Set execute permissions to "users"

### Step 3: Authentication Configuration
In Appwrite Console:
1. Go to **Auth > Settings**
2. Enable **Email/Password** authentication
3. Set password requirements (minimum 8 characters)
4. Configure session duration (default: 1 year)

### Step 4: Set Permissions
For each collection, set these permissions:
- **Read**: `users`, `role:admin`
- **Create**: `users`, `role:admin`  
- **Update**: `users`, `role:admin`
- **Delete**: `role:admin`

---

## 🌐 Phase 2: Frontend Deployment

### Step 1: Connect to Netlify
1. Go to https://netlify.com
2. Login with GitHub
3. Click **"New site from Git"**
4. Select your EstateCore repository
5. Choose branch: `main` (or your default branch)

### Step 2: Configure Build Settings
Netlify will automatically detect settings from `netlify.toml`:
- **Build command**: `npm run build`
- **Publish directory**: `dist`
- **Node version**: 20.x

### Step 3: Set Environment Variables
In Netlify Dashboard > Site settings > Environment variables, add:

```
VITE_APPWRITE_PROJECT_ID=68b6e4240013f757c47b
VITE_APPWRITE_PROJECT_NAME=Estate_core Backend
VITE_APPWRITE_ENDPOINT=https://nyc.cloud.appwrite.io/v1
VITE_API_URL=https://nyc.cloud.appwrite.io/v1
```

### Step 4: Deploy
1. Click **"Deploy site"**
2. Wait for build to complete (~2-5 minutes)
3. Note your Netlify URL (e.g., `https://amazing-app-123456.netlify.app`)

---

## 🔗 Phase 3: Integration Configuration

### Step 1: Configure Appwrite Domains
1. Go to **Appwrite Console > Settings > Domains**
2. Add your Netlify URL to **Allowed Domains**
3. Add any custom domains you plan to use

### Step 2: Test Authentication
1. Visit your deployed application
2. Try to register a new account
3. Check if login works
4. Verify session persistence

### Step 3: Create Sample Data
Create test data to verify functionality:
1. Add a property
2. Add a tenant
3. Create a work order
4. Test VMS functions (if applicable)

---

## 🧪 Phase 4: Testing & Verification

### Core Features to Test:
- [ ] User registration/login
- [ ] Properties CRUD operations
- [ ] Tenants management
- [ ] Lease management
- [ ] Work orders/maintenance requests
- [ ] Payment tracking
- [ ] Dashboard metrics
- [ ] VMS camera controls
- [ ] Access control system
- [ ] Audit logging

### Performance Checks:
- [ ] Page load times
- [ ] API response times
- [ ] Mobile responsiveness
- [ ] Cross-browser compatibility

---

## 🔧 Troubleshooting

### Common Issues:

**1. CORS Errors**
- Ensure your Netlify domain is added to Appwrite allowed domains
- Check browser console for specific CORS messages

**2. Authentication Failures**
- Verify Appwrite auth settings are enabled
- Check environment variables are set correctly
- Ensure Appwrite project ID matches

**3. Build Failures**
- Node.js version compatibility (Netlify uses 20+)
- Missing environment variables
- Check Netlify build logs for specific errors

**4. Function Errors**
- Review Appwrite Function logs
- Verify function permissions and API keys
- Check function execution settings

**5. Database Connection Issues**
- Verify collection names match exactly
- Check collection permissions
- Ensure database ID is correct

### Debug Tools:
- Netlify build logs
- Appwrite Function logs
- Browser developer console
- Network tab for API calls

---

## 📈 Phase 5: Production Optimization

### Security:
- [ ] Review collection permissions
- [ ] Set up API rate limiting
- [ ] Configure proper CORS policies
- [ ] Enable HTTPS (automatic on Netlify)

### Performance:
- [ ] Enable Netlify CDN
- [ ] Optimize images and assets
- [ ] Set up proper caching headers
- [ ] Monitor Appwrite usage quotas

### Monitoring:
- [ ] Set up error tracking
- [ ] Monitor API response times
- [ ] Track user engagement
- [ ] Set up uptime monitoring

---

## 🎉 Deployment Complete!

Your EstateCore application is now fully deployed and ready for production use!

### Your Deployed URLs:
- **Frontend**: Your Netlify URL
- **Backend**: https://nyc.cloud.appwrite.io/v1
- **Appwrite Console**: https://cloud.appwrite.io

### Next Steps:
1. **Custom Domain**: Set up your own domain in Netlify
2. **User Training**: Train your team on the new system
3. **Data Migration**: Import existing property/tenant data
4. **Monitoring**: Set up alerts and monitoring
5. **Backup**: Configure regular data backups

### Support Resources:
- **Appwrite Docs**: https://appwrite.io/docs
- **Netlify Docs**: https://docs.netlify.com
- **Project Files**: Check the generated documentation files in your repo

---

## 📞 Need Help?

If you encounter issues:
1. Check the troubleshooting section above
2. Review Appwrite/Netlify documentation
3. Check build logs and error messages
4. Verify all environment variables and settings

**Happy Property Managing! 🏠✨**
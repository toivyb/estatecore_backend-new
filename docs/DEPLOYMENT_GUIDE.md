# EstateCore Deployment Guide

## Overview
This guide covers deploying EstateCore to various environments including development, staging, and production.

## Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Redis (optional, for caching)
- Nginx (for production)

## Environment Setup

### 1. Clone and Configure
```bash
git clone <repository-url>
cd estatecore_project
cp .env.example .env
```

### 2. Configure Environment Variables
Edit `.env` with your settings:
```bash
# Required
SECRET_KEY=your-super-secure-secret-key-min-32-characters
JWT_SECRET_KEY=your-jwt-secret-key-min-32-characters  
DATABASE_URL=postgresql://username:password@host:port/database

# Optional
FLASK_ENV=production
CORS_ORIGINS=https://yourdomain.com
OPENALPR_API_KEY=your-api-key
```

### 3. Validate Configuration
```bash
python scripts/config_validator.py
```

## Development Deployment

### Backend Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Optional: Install AI features
pip install -r requirements-ai.txt

# Initialize database
python scripts/reset_db.py
python scripts/seed.py

# Run development server
python main.py
```

### Frontend Setup
```bash
cd estatecore_frontend
npm install
npm run dev
```

Access the application:
- **Backend**: http://localhost:5000
- **Frontend**: http://localhost:5173

## Production Deployment

### Option 1: Docker Deployment

#### 1. Build Images
```bash
# Backend
docker build -t estatecore-backend -f estatecore_backend/Dockerfile .

# Frontend  
docker build -t estatecore-frontend -f estatecore_frontend/Dockerfile .
```

#### 2. Docker Compose
```bash
docker-compose up -d
```

#### 3. Initialize Database
```bash
docker exec -it estatecore-backend python scripts/reset_db.py
docker exec -it estatecore-backend python scripts/seed.py
```

### Option 2: Traditional Server Deployment

#### 1. Server Setup (Ubuntu 20.04+)
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3 python3-pip nodejs npm postgresql postgresql-contrib nginx -y

# Install PM2 for process management
sudo npm install -g pm2
```

#### 2. Database Setup
```bash
# Create PostgreSQL user and database
sudo -u postgres psql
CREATE USER estatecore WITH PASSWORD 'secure_password';
CREATE DATABASE estatecore_prod OWNER estatecore;
GRANT ALL PRIVILEGES ON DATABASE estatecore_prod TO estatecore;
\q
```

#### 3. Application Deployment
```bash
# Clone application
git clone <repository-url> /var/www/estatecore
cd /var/www/estatecore

# Set permissions
sudo chown -R www-data:www-data /var/www/estatecore

# Backend setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend setup
cd estatecore_frontend
npm ci --production
npm run build

# Initialize database
cd /var/www/estatecore
python scripts/reset_db.py
python scripts/create_super_admin.py admin@yourdomain.com
```

#### 4. Process Management with PM2
```bash
# Backend process
pm2 start main.py --name "estatecore-backend" --interpreter python3

# Frontend process (if serving with Node.js)
pm2 start estatecore_frontend/server.js --name "estatecore-frontend"

# Save PM2 configuration
pm2 save
pm2 startup
```

#### 5. Nginx Configuration
```bash
sudo cp deployment/nginx.conf /etc/nginx/sites-available/estatecore
sudo ln -s /etc/nginx/sites-available/estatecore /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Option 3: Cloud Platform Deployment

#### Heroku
```bash
# Install Heroku CLI
# Create Heroku app
heroku create estatecore-app

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DATABASE_URL=your-database-url

# Deploy
git push heroku main

# Initialize database
heroku run python scripts/reset_db.py
heroku run python scripts/seed.py
```

#### AWS/Azure/GCP
1. **Create VM instances**
2. **Set up load balancer**  
3. **Configure managed database**
4. **Set up object storage for static files**
5. **Follow traditional server deployment steps**

## SSL/HTTPS Setup

### Let's Encrypt (Free)
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
sudo certbot renew --dry-run
```

### Custom Certificate
```bash
# Copy certificate files
sudo cp your-cert.crt /etc/ssl/certs/
sudo cp your-private.key /etc/ssl/private/

# Update Nginx configuration
sudo nano /etc/nginx/sites-available/estatecore
# Add SSL configuration block
```

## Database Migrations

### Development
```bash
# Create migration
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade
```

### Production
```bash
# Backup database first
pg_dump estatecore_prod > backup.sql

# Apply migrations
flask db upgrade

# Verify application works
# If issues, restore from backup:
# psql estatecore_prod < backup.sql
```

## Monitoring and Logging

### Application Monitoring
```bash
# Install monitoring tools
pip install sentry-sdk[flask]

# Add to your application
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FlaskIntegration()]
)
```

### System Monitoring
```bash
# Install monitoring stack
sudo apt install prometheus grafana

# Configure monitoring dashboards
# Import EstateCore dashboard: deployment/grafana-dashboard.json
```

### Log Management
```bash
# Configure log rotation
sudo cp deployment/estatecore-logrotate /etc/logrotate.d/

# Centralized logging (optional)
# Configure ELK stack or similar
```

## Backup Strategy

### Database Backups
```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump estatecore_prod > /backups/db_backup_$DATE.sql
find /backups -name "db_backup_*.sql" -mtime +7 -delete
```

### File Backups
```bash
# Backup user uploads and static files
rsync -av /var/www/estatecore/uploads/ /backups/uploads/
rsync -av /var/www/estatecore/static/ /backups/static/
```

## Security Checklist

### Server Security
- [ ] Firewall configured (only ports 22, 80, 443 open)
- [ ] SSH key-based authentication
- [ ] Regular security updates
- [ ] Non-root user for application
- [ ] File permissions properly set

### Application Security  
- [ ] Strong SECRET_KEY (32+ characters)
- [ ] HTTPS enabled
- [ ] Database credentials secure
- [ ] No hardcoded secrets in code
- [ ] CORS properly configured
- [ ] Rate limiting enabled

### Database Security
- [ ] Database user has minimal required permissions
- [ ] Database not accessible from internet
- [ ] Regular security patches applied
- [ ] Encrypted connections enabled

## Performance Optimization

### Backend Optimization
```python
# Enable caching
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'redis'})

# Database connection pooling
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 20,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}
```

### Frontend Optimization
```bash
# Build optimization
npm run build -- --mode production

# Enable compression
# Add to Nginx config:
# gzip on;
# gzip_types text/css application/javascript image/svg+xml;
```

### Database Optimization
```sql
-- Add indexes for common queries
CREATE INDEX idx_lpr_events_timestamp ON lpr_events(timestamp);
CREATE INDEX idx_users_email ON users(email);
```

## Troubleshooting

### Common Issues

#### "ModuleNotFoundError: No module named 'dotenv'"
```bash
pip install python-dotenv
```

#### "SECRET_KEY environment variable must be set"
```bash
# Check .env file exists and has SECRET_KEY
cat .env | grep SECRET_KEY
```

#### Database connection errors
```bash
# Verify database is running
sudo systemctl status postgresql

# Test connection
psql -h localhost -U estatecore -d estatecore_prod
```

#### Permission denied errors
```bash
# Fix file permissions
sudo chown -R www-data:www-data /var/www/estatecore
sudo chmod -R 755 /var/www/estatecore
```

### Log Locations
- **Application logs**: `/var/log/estatecore/`
- **Nginx logs**: `/var/log/nginx/`
- **PostgreSQL logs**: `/var/log/postgresql/`
- **System logs**: `/var/log/syslog`

### Performance Issues
```bash
# Check system resources
htop
df -h
iostat

# Monitor application performance  
pm2 monit

# Database performance
SELECT * FROM pg_stat_activity;
```

## Health Checks

### Application Health
```bash
curl http://localhost:5000/api/health
```

### Database Health
```bash
psql -d estatecore_prod -c "SELECT version();"
```

### System Health
```bash
# Check disk space
df -h

# Check memory usage
free -h

# Check CPU usage
top
```

## Rollback Procedures

### Application Rollback
```bash
# Rollback to previous version
pm2 stop estatecore-backend
git checkout previous-release-tag
pm2 start estatecore-backend
```

### Database Rollback
```bash
# Restore from backup
pg_restore -d estatecore_prod backup.sql
```

## Maintenance Windows

### Scheduled Maintenance
1. **Notify users** 24-48 hours in advance
2. **Create database backup**
3. **Deploy during low-traffic hours**
4. **Monitor application after deployment**
5. **Have rollback plan ready**

### Emergency Maintenance
1. **Create immediate backup**
2. **Deploy critical fixes**
3. **Monitor system closely**
4. **Document issues and resolutions**

## Support and Resources

### Documentation
- [Installation Guide](README.md)
- [API Documentation](API_DOCUMENTATION.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)

### Community
- **GitHub Issues**: Report bugs and feature requests
- **Discord**: Community support and discussions
- **Email**: support@estatecore.com
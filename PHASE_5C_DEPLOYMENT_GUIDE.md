# EstateCore Phase 5C AI Intelligence - Deployment Guide

## Overview
EstateCore Phase 5C introduces advanced AI-powered intelligence features that revolutionize property management through machine learning, predictive analytics, and automated optimization.

## Phase 5C Features Completed

### 🤖 AI Intelligence Systems
- **Smart Energy Management**: ML-powered energy consumption forecasting and optimization
- **AI Management Dashboard**: Central hub for monitoring all AI systems
- **Automated Compliance Monitoring**: AI-driven compliance tracking and violation detection
- **Predictive Tenant Screening**: ML-based tenant risk assessment and scoring

### 🚀 Beta Testing Program
- **Beta Testing Dashboard**: Comprehensive testing management and feedback collection
- **Participant Management**: Track beta testers and their progress
- **Feature Testing Status**: Monitor testing coverage and bug reports
- **Feedback Collection**: Gather and analyze user feedback

## System Requirements

### Backend Requirements
- Python 3.8+
- Flask 2.3+
- SQLAlchemy 2.0+
- PostgreSQL 13+
- Redis 6+ (for caching)
- 4GB RAM minimum, 8GB recommended
- 2 CPU cores minimum, 4+ recommended

### Frontend Requirements
- Node.js 18+
- React 18+
- Tailwind CSS 3+
- Vite 5+

### AI/ML Dependencies
- scikit-learn (optional - fallback to simplified engine if not available)
- numpy (optional)
- pandas (optional)

## Deployment Steps

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd estatecore_project

# Set up Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install optional ML dependencies (recommended)
pip install scikit-learn numpy pandas
```

### 2. Database Configuration

```bash
# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost/estatecore_db"
export SECRET_KEY="your-secret-key-here"
export FLASK_ENV="production"

# Initialize database
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd estatecore_frontend

# Install dependencies
npm install

# Build for production
npm run build
```

### 4. AI Services Configuration

#### Smart Energy Management
The Smart Energy Management system uses either:
- **Full ML Engine**: Requires scikit-learn, numpy, pandas
- **Simplified Engine**: Uses built-in statistical methods (automatic fallback)

```python
# Configuration is handled automatically in app.py
# Service initializes on startup with appropriate engine
```

#### AI Management Dashboard
Monitors all AI systems and provides:
- Real-time system status
- Performance metrics
- Alert management
- Resource usage monitoring

### 5. Production Deployment

#### Using Render (Recommended)

1. **Connect Repository**: Link your GitHub repository to Render
2. **Environment Variables**:
   ```
   DATABASE_URL=postgresql://...
   SECRET_KEY=your-secret-key
   FLASK_ENV=production
   PYTHON_VERSION=3.10.8
   ```
3. **Build Command**: `pip install -r requirements.txt && cd estatecore_frontend && npm install && npm run build`
4. **Start Command**: `gunicorn app:app`

#### Using Docker

```dockerfile
# Dockerfile example
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
WORKDIR /app/estatecore_frontend
RUN npm install && npm run build

WORKDIR /app
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
```

## Feature Configuration

### Smart Energy Management API Endpoints
```
POST   /api/energy/readings          # Add energy reading
GET    /api/energy/forecast/{id}/{type} # Get consumption forecast
GET    /api/energy/recommendations/{id} # Get optimization recommendations
GET    /api/energy/analytics/{id}    # Get energy analytics
GET    /api/energy/alerts           # Get energy alerts
GET    /api/energy/dashboard/{id}    # Get dashboard data
POST   /api/energy/simulate/{id}     # Simulate test data
GET    /api/energy/types            # Get energy types
GET    /api/energy/health           # Health check
```

### AI Management Dashboard Features
- **System Monitoring**: Real-time status of all AI services
- **Performance Metrics**: CPU, memory, storage usage
- **Alert Management**: Centralized alert handling
- **Quick Actions**: System control and configuration

### Beta Testing Dashboard Features
- **Participant Management**: Track beta testers
- **Test Results**: Monitor feature testing progress
- **Feedback Collection**: Gather user feedback
- **Progress Tracking**: Overall beta program metrics

## Testing the Deployment

### 1. Backend Health Check
```bash
curl http://localhost:5000/api/energy/health
```

Expected response:
```json
{
  "success": true,
  "status": "healthy",
  "models_trained": true,
  "data_points": 810,
  "service_version": "1.0.0"
}
```

### 2. Frontend Access
Navigate to the application and verify:
- ✅ AI Management Dashboard loads
- ✅ Smart Energy Management interface works
- ✅ Beta Testing Dashboard displays data
- ✅ All navigation links function

### 3. API Integration Test
```bash
python test_energy_management.py
```

Expected output:
```
Testing Smart Energy Management System
========================================
1. Testing health check endpoint...
   Status: 200
   Service Status: healthy
   Models Trained: True
   Data Points: 810

[SUCCESS] Energy Management System Test Complete!
```

## Monitoring and Maintenance

### System Monitoring
- **AI Management Dashboard**: Monitor all AI services from `/ai-management-dashboard`
- **Performance Dashboard**: Track system performance from `/performance`
- **Beta Testing Dashboard**: Monitor testing progress from `/beta-testing`

### Log Monitoring
```bash
# Application logs
tail -f logs/app.log

# Energy management logs  
tail -f logs/energy_management.log

# Error logs
tail -f logs/error.log
```

### Health Checks
Set up automated health checks for:
- `/api/energy/health` - Energy management service
- `/api/properties` - Core property API
- `/api/users` - User management API

## Security Considerations

### API Security
- All API endpoints require authentication
- Rate limiting implemented on critical endpoints
- Input validation on all user inputs
- SQL injection protection via SQLAlchemy

### Data Protection
- Energy data encrypted at rest
- AI model data protected
- User data anonymized in analytics
- GDPR compliance for EU users

## Troubleshooting

### Common Issues

#### 1. ML Dependencies Missing
**Error**: `ImportError: No module named 'sklearn'`
**Solution**: System automatically falls back to simplified engine. Install ML dependencies for full features:
```bash
pip install scikit-learn numpy pandas
```

#### 2. Energy Service Not Starting
**Error**: `Energy Management service: NOT FOUND`
**Solution**: Check imports and ensure service initialization in `app.py`:
```python
# Verify this exists in app.py
from services.energy_management_service import get_energy_management_service
energy_service = get_energy_management_service()
app.energy_service = energy_service
```

#### 3. Frontend Build Errors
**Error**: Component import failures
**Solution**: Ensure all components are properly exported:
```bash
cd estatecore_frontend
npm run build
```

### Performance Optimization

#### Database Optimization
```sql
-- Index for energy readings
CREATE INDEX idx_energy_readings_property_timestamp ON energy_readings(property_id, timestamp);

-- Index for user queries
CREATE INDEX idx_users_email ON users(email);
```

#### Caching Strategy
- Redis for API response caching
- Frontend component memoization
- Database query result caching

## Version Information
- **Phase**: 5C AI Intelligence
- **Version**: 5.0.0-beta.1
- **Release Date**: January 2024
- **Compatibility**: Backward compatible with Phase 5B

## Support and Documentation

### Additional Resources
- API Documentation: `/api/docs`
- System Status: `/system-status`
- Admin Tools: `/admin-tools` (Super Admin only)

### Getting Help
- GitHub Issues: Report bugs and feature requests
- Documentation: Full API and feature documentation
- Support Email: Contact for deployment assistance

## Next Steps

After successful Phase 5C deployment:
1. **Monitor System Performance**: Use built-in dashboards
2. **Collect Beta Feedback**: Through beta testing dashboard
3. **Plan Phase 6**: Advanced AI features and integrations
4. **Scale Infrastructure**: Based on usage metrics

---

**🚀 EstateCore Phase 5C AI Intelligence is now ready for production deployment!**

The system provides advanced AI-powered property management capabilities with comprehensive monitoring, testing, and optimization features. All core AI systems are operational and ready to revolutionize property management operations.
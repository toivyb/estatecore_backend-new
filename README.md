# EstateCore - Complete Property Management Platform 🏠

[![Version](https://img.shields.io/badge/version-5.0-blue.svg)](https://github.com/toivyb/estatecore_backend-new)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-Production%20Ready-brightgreen.svg)](https://github.com/toivyb/estatecore_backend-new)

A comprehensive, AI-powered property management platform designed for modern real estate operations. Features advanced automation, intelligent analytics, and seamless user experience.

## ✨ Key Features

### 🏠 Property Management
- **Multi-property dashboard** with real-time metrics
- **Advanced tenant management** and screening
- **Unit tracking** with occupancy analytics
- **Document management** with secure file storage
- **Maintenance scheduling** and work order tracking

### 💰 Financial Management
- **Automated rent collection** workflows
- **Lease management** with AI-powered expiration monitoring
- **Financial reporting** and analytics
- **Revenue tracking** and forecasting
- **Payment processing** integration

### 🤖 AI & Automation
- **License Plate Recognition (LPR)** for access control
- **AI lease expiration** monitoring and alerts
- **Automated maintenance** forecasting
- **Smart tenant screening** with scoring
- **Revenue leakage** detection

### 🛡️ Security & Access
- **Role-based permissions** with granular controls
- **Multi-camera LPR integration** with real-time monitoring
- **Security event tracking** and alerting
- **Access log management** with audit trails
- **Advanced user authentication**

### 📊 Analytics & Reporting
- **Performance monitoring** dashboard
- **KPI tracking** and business intelligence
- **Bulk operations** for mass updates
- **Advanced reporting** with export capabilities
- **Real-time data** visualization

## 🎯 System Status

- ✅ **100% Feature Complete** - All planned features implemented
- ✅ **Production Ready** - Fully tested and optimized
- ✅ **Error-Free Operation** - Comprehensive error handling
- ✅ **Modern Tech Stack** - React + Flask + AI integration

## Project Structure

```
estatecore_project/
├── estatecore_backend/      # Python Flask backend application
├── estatecore_frontend/     # React frontend application
├── ai_modules/              # AI/ML modules for predictions
├── scripts/                 # Utility scripts for setup and maintenance
├── docs/                    # Project documentation
├── deployment/              # Deployment configuration files
├── tests/                   # Test files
├── archive/                 # Archived legacy code
├── utils/                   # Shared utility modules
├── migrations/              # Database migration files
├── instance/                # Flask instance configuration
└── requirements.txt         # Python dependencies

Optional:
├── requirements-ai.txt      # AI/ML dependencies (install separately)
```

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+

### Environment Setup

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit .env with your configuration:**
   - Set `SECRET_KEY` (minimum 16 characters)
   - Set `DATABASE_URL` (PostgreSQL connection string)
   - Configure other optional settings

3. **Validate configuration:**
   ```bash
   python scripts/config_validator.py
   ```

### Backend Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install AI features (optional):**
   ```bash
   pip install -r requirements-ai.txt
   ```

3. **Initialize database:**
   ```bash
   python scripts/reset_db.py
   python scripts/seed.py
   ```

4. **Run backend:**
   ```bash
   python main.py
   ```

### Frontend Setup

1. **Navigate to frontend:**
   ```bash
   cd estatecore_frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

## Features

- **Property Management**: Comprehensive property and unit management
- **Tenant Management**: Tenant profiles, lease tracking, communication
- **Rent Collection**: Automated rent processing and payment tracking
- **Maintenance**: Work order management and scheduling
- **AI Features**: Lease scoring, maintenance forecasting, revenue analysis
- **Access Control**: Digital access management and visitor passes
- **Reporting**: Financial reports, analytics, and insights

## Documentation

See the `docs/` directory for detailed documentation:
- [Installation Guide](docs/README-APPLY.txt)
- [Issue Resolution Plan](docs/ISSUE_RESOLUTION_PLAN.txt)
- [Found Issues Report](docs/FOUND_ISSUES.txt)

## Security

- All sensitive configuration is managed through environment variables
- No hardcoded credentials in source code
- Environment validation prevents startup with invalid configuration
- Comprehensive security measures for production deployment

## Development

### Project Organization
- `estatecore_backend/`: Main Flask application
- `ai_modules/`: Standalone AI/ML modules
- `scripts/`: Administrative and maintenance scripts
- `utils/`: Shared utilities across components

### Legacy Code
Legacy code has been moved to `archive/legacy/` to maintain project history while keeping the main codebase clean.

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]
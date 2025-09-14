# 🏢 EstateCore - Property Management System

A comprehensive property management solution with video management system (VMS) and access control, built with React frontend and Appwrite backend.

---

## 🚀 Quick Start - New Appwrite Deployment

### For Immediate Production Deployment:
```bash
# 1. Setup Appwrite backend
npm run setup-appwrite

# 2. Deploy Functions  
npm run deploy-functions

# 3. Deploy to Netlify (follow the guide)
npm run deploy-netlify
```

### Manual Setup:
Follow the detailed guide in `COMPLETE_SETUP_GUIDE.md`

---

## 📁 Modern Architecture (Recommended)

### Frontend (Netlify)
- **Framework**: React 18 with Vite
- **Backend**: Appwrite (Cloud)
- **Authentication**: Appwrite Sessions
- **Database**: Appwrite Collections
- **Functions**: Appwrite Functions

### Legacy Flask Backend
The original Flask backend has been replaced with Appwrite for better scalability and maintenance.

---

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
# EstateCore Coding Standards

## Overview
This document defines the coding standards and naming conventions used in the EstateCore project.

## Directory Structure Standards

### Directory Naming
- **Snake_case** for main project directories: `estatecore_backend`, `estatecore_frontend`
- **Lowercase with hyphens** for configuration directories: `node_modules`, `build-tools`
- **CamelCase** for component directories when appropriate: `UI/Components`

### File Organization
```
estatecore_project/
├── estatecore_backend/      # Python backend
├── estatecore_frontend/     # React frontend  
├── ai_modules/              # AI/ML modules
├── scripts/                 # Utility scripts
├── docs/                    # Documentation
├── deployment/              # Deployment configs
├── tests/                   # Test files
└── utils/                   # Shared utilities
```

## Python Naming Conventions

### Files and Modules
- **snake_case**: `user_model.py`, `auth_utils.py`, `lease_scoring.py`
- **Descriptive names**: Clearly indicate the module's purpose

### Classes
- **PascalCase**: `User`, `LPREvent`, `PropertyManager`
- **Descriptive**: `AccessAttempt`, `MaintenanceRequest`

### Functions and Variables
- **snake_case**: `get_user_by_id()`, `current_user`, `lease_score`
- **Verb-noun pattern** for functions: `create_user()`, `validate_credentials()`

### Constants
- **UPPER_SNAKE_CASE**: `SECRET_KEY`, `DATABASE_URL`, `MAX_RETRIES`

### Example Python Code
```python
# Good
class UserManager:
    def __init__(self, database_url):
        self.database_url = database_url
    
    def get_user_by_email(self, email_address):
        return self._query_user_table(email_address)
    
    def _query_user_table(self, email):
        # Private method implementation
        pass

# Constants
MAX_LOGIN_ATTEMPTS = 3
DEFAULT_SESSION_TIMEOUT = 3600
```

## JavaScript/React Naming Conventions

### Files and Components
- **PascalCase** for components: `UserProfile.jsx`, `LoginForm.jsx`
- **camelCase** for utilities: `apiUtils.js`, `authHelpers.js`
- **kebab-case** for assets and configs: `app-config.json`, `user-avatar.png`

### React Components
- **PascalCase**: `Dashboard`, `PropertyList`, `MaintenanceForm`
- **Descriptive names**: Clearly indicate component purpose

### Functions and Variables
- **camelCase**: `getUserData()`, `currentUser`, `isAuthenticated`
- **Boolean prefixes**: `isLoading`, `hasError`, `canEdit`

### Example React Code
```jsx
// Good
const UserProfile = ({ userId }) => {
  const [userData, setUserData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  
  const fetchUserData = async (id) => {
    setIsLoading(true);
    // Implementation
  };
  
  return (
    <div className="user-profile">
      {/* Component content */}
    </div>
  );
};
```

## Database Naming Conventions

### Table Names
- **snake_case**: `users`, `lpr_events`, `maintenance_requests`
- **Plural nouns**: Tables represent collections

### Column Names
- **snake_case**: `user_id`, `created_at`, `email_address`
- **Descriptive**: `first_name` not `fname`

### Example Database Schema
```sql
CREATE TABLE lpr_events (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    plate VARCHAR(20) NOT NULL,
    camera VARCHAR(50),
    confidence FLOAT,
    image_url VARCHAR(500),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## Configuration and Environment

### Environment Variables
- **UPPER_SNAKE_CASE**: `SECRET_KEY`, `DATABASE_URL`, `JWT_SECRET_KEY`
- **Prefixed by component**: `FLASK_ENV`, `REACT_APP_API_URL`

### Configuration Files
- **kebab-case**: `docker-compose.yml`, `tailwind.config.js`
- **Descriptive**: Clear purpose from filename

## API Naming Conventions

### Endpoints
- **RESTful patterns**: `/api/users`, `/api/properties/{id}`
- **Plural nouns**: `/api/lpr-events`, `/api/maintenance-requests`
- **Hyphenated**: Multi-word resources use hyphens

### Example API Design
```
GET    /api/users              # List users
POST   /api/users              # Create user
GET    /api/users/{id}         # Get specific user
PUT    /api/users/{id}         # Update user
DELETE /api/users/{id}         # Delete user

GET    /api/lpr-events         # List LPR events
POST   /api/lpr-events         # Create LPR event
```

## Documentation Standards

### File Naming
- **UPPER_SNAKE_CASE** for important docs: `README.md`, `CODING_STANDARDS.md`
- **Descriptive prefixes**: `API_DOCUMENTATION.md`, `DEPLOYMENT_GUIDE.md`

### Comment Standards
```python
# Python
def calculate_lease_score(tenant_data, property_data):
    """
    Calculate lease scoring based on tenant and property data.
    
    Args:
        tenant_data (dict): Tenant information including credit score, income
        property_data (dict): Property details including rent, location
    
    Returns:
        float: Lease score between 0.0 and 1.0
    """
    pass
```

```jsx
// JavaScript/React
/**
 * UserProfile component displays user information and settings
 * @param {Object} props - Component props
 * @param {string} props.userId - Unique user identifier  
 * @param {Function} props.onUpdate - Callback when user data changes
 */
const UserProfile = ({ userId, onUpdate }) => {
    // Component implementation
};
```

## Testing Standards

### Test File Naming
- **Python**: `test_user_model.py`, `test_auth_utils.py`
- **JavaScript**: `UserProfile.test.jsx`, `apiUtils.test.js`

### Test Function Naming
- **Descriptive**: `test_user_creation_with_valid_data()`
- **Behavior-focused**: `should_return_error_when_email_invalid()`

## Git Standards

### Branch Naming
- **feature/feature-name**: `feature/user-authentication`
- **bugfix/issue-description**: `bugfix/login-validation-error`
- **hotfix/critical-fix**: `hotfix/security-patch`

### Commit Messages
```
feat: add user authentication system
fix: resolve login validation error
docs: update API documentation
refactor: improve database query performance
```

## Enforcement

### Automated Tools
- **Python**: Use `black` for formatting, `flake8` for linting
- **JavaScript**: Use `eslint` and `prettier` for code quality
- **Pre-commit hooks**: Enforce standards before commits

### Code Review Checklist
- [ ] Naming follows established conventions
- [ ] Functions and classes have clear, descriptive names
- [ ] Documentation is complete and accurate
- [ ] No inconsistent naming patterns
- [ ] Environment variables properly named and documented

## Migration Strategy

For existing code that doesn't follow these standards:
1. **Gradual refactoring**: Update during regular maintenance
2. **New code compliance**: All new code must follow standards
3. **Breaking changes**: Document and communicate before renaming public APIs
4. **Batch updates**: Group related naming changes together

## Examples of Good vs Bad Naming

### Good ✅
```python
class PropertyManager:
    def get_available_units(self, property_id):
        return self._query_available_units(property_id)

user_authentication_token = generate_jwt_token(user_id)
is_admin_user = check_user_permissions(user)
```

### Bad ❌
```python
class PropMgr:
    def getAvailUnits(self, propId):
        return self.queryAvailUnits(propId)

userAuthTkn = genTkn(uid)
adminUser = checkPerms(user)
```

This document should be followed by all contributors to maintain code quality and consistency across the EstateCore project.
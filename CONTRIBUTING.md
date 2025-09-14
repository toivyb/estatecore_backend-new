# Contributing to EstateCore

Thank you for your interest in contributing to EstateCore! This document provides guidelines and information for contributors.

## Code of Conduct

### Our Commitment
We are committed to providing a welcoming and inclusive experience for all contributors, regardless of background or experience level.

### Expected Behavior
- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other contributors

### Unacceptable Behavior
- Harassment, discrimination, or inappropriate conduct
- Trolling, insulting, or derogatory comments
- Public or private harassment
- Publishing others' private information without permission

## Getting Started

### Development Setup
1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/estatecore.git
   cd estatecore_project
   ```
3. **Set up development environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   pip install -r requirements.txt
   cd estatecore_frontend && npm install
   ```
4. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

### Project Structure
```
estatecore_project/
├── estatecore_backend/      # Python Flask backend
├── estatecore_frontend/     # React frontend
├── ai_modules/              # AI/ML modules
├── docs/                    # Documentation
├── scripts/                 # Utility scripts
├── tests/                   # Test files
└── deployment/              # Deployment configurations
```

## How to Contribute

### Reporting Bugs
1. **Check existing issues** to avoid duplicates
2. **Use the bug report template**
3. **Include detailed information**:
   - Operating system and version
   - Python/Node.js versions
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages and stack traces

### Suggesting Features
1. **Check existing feature requests**
2. **Use the feature request template**  
3. **Provide detailed description**:
   - Use case and motivation
   - Detailed description of the feature
   - Possible implementation approach
   - Any alternative solutions considered

### Contributing Code

#### Before You Start
- **Discuss major changes** in an issue first
- **Check the project roadmap** to align with project direction
- **Look for "good first issue"** labels for beginner-friendly tasks

#### Development Workflow
1. **Create a feature branch** from `main`:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Follow the [coding standards](docs/CODING_STANDARDS.md)
   - Write tests for new functionality
   - Update documentation as needed

3. **Test your changes**:
   ```bash
   # Backend tests
   python -m pytest tests/
   
   # Frontend tests  
   cd estatecore_frontend && npm test
   
   # Integration tests
   python scripts/verify_structure.py
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add user authentication system"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request** on GitHub

#### Pull Request Guidelines
- **Use descriptive titles** and descriptions
- **Link related issues** using keywords (fixes #123)
- **Include screenshots** for UI changes
- **Add tests** for new functionality
- **Update documentation** if needed
- **Ensure CI passes** before requesting review

#### Commit Message Format
Use conventional commit format:
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(auth): add JWT token authentication
fix(api): resolve user creation validation error
docs(api): update endpoint documentation
refactor(database): improve query performance
```

## Code Standards

### Python (Backend)
- **Follow PEP 8** style guidelines
- **Use type hints** where appropriate
- **Write docstrings** for functions and classes
- **Use meaningful variable names**
- **Keep functions small and focused**

Example:
```python
def calculate_lease_score(tenant_data: dict, property_data: dict) -> float:
    """
    Calculate lease scoring based on tenant and property data.
    
    Args:
        tenant_data: Tenant information including credit score, income
        property_data: Property details including rent, location
    
    Returns:
        Lease score between 0.0 and 1.0
    """
    # Implementation here
    return score
```

### JavaScript/React (Frontend)
- **Use ESLint** for code quality
- **Follow React best practices**
- **Use functional components** with hooks
- **Write meaningful component names**
- **Keep components small and focused**

Example:
```jsx
/**
 * UserProfile component displays user information and settings
 */
const UserProfile = ({ userId, onUpdate }) => {
  const [userData, setUserData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  
  const handleUpdate = useCallback((newData) => {
    // Update logic here
    onUpdate(newData);
  }, [onUpdate]);
  
  return (
    <div className="user-profile">
      {/* Component content */}
    </div>
  );
};
```

### Testing Standards
- **Write tests for new features**
- **Maintain high test coverage**
- **Use descriptive test names**
- **Follow AAA pattern**: Arrange, Act, Assert

```python
def test_user_creation_with_valid_data():
    """Test that user creation succeeds with valid data."""
    # Arrange
    user_data = {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "secure_password"
    }
    
    # Act
    result = create_user(user_data)
    
    # Assert
    assert result.success is True
    assert result.user.email == "test@example.com"
```

## Documentation

### Types of Documentation
- **API Documentation**: Document all endpoints, parameters, responses
- **User Guides**: Step-by-step instructions for users
- **Developer Guides**: Technical documentation for contributors
- **Code Comments**: Explain complex logic and decisions

### Documentation Standards
- **Use clear, simple language**
- **Include code examples**
- **Keep documentation up-to-date**
- **Use proper markdown formatting**
- **Include screenshots for UI features**

## Testing

### Test Types
- **Unit Tests**: Test individual functions/components
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete user workflows
- **Performance Tests**: Test system performance under load

### Running Tests
```bash
# Backend unit tests
python -m pytest tests/ -v

# Backend integration tests
python -m pytest tests/integration/ -v

# Frontend tests
cd estatecore_frontend
npm test

# E2E tests
npm run test:e2e

# Coverage reports
python -m pytest --cov=estatecore_backend tests/
npm run test:coverage
```

### Writing Tests
- **Test both success and failure cases**
- **Use fixtures for common test data**
- **Mock external dependencies**
- **Keep tests independent and repeatable**

## Review Process

### Code Review Checklist
- [ ] Code follows project standards
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No hardcoded secrets or credentials
- [ ] Performance considerations addressed
- [ ] Security best practices followed
- [ ] Breaking changes are documented

### Review Timeline
- **Small PRs**: 1-2 business days
- **Medium PRs**: 3-5 business days  
- **Large PRs**: 1-2 weeks (consider breaking into smaller PRs)

### Addressing Review Comments
- **Respond to all comments**
- **Make requested changes promptly**
- **Ask for clarification if needed**
- **Mark conversations as resolved when addressed**

## Release Process

### Versioning
We use [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Schedule
- **Major releases**: Quarterly
- **Minor releases**: Monthly
- **Patch releases**: As needed

### Contributing to Releases
- **Feature freeze** 1 week before release
- **Bug fixes only** during freeze period
- **All tests must pass** before release
- **Documentation must be updated**

## Getting Help

### Community Support
- **GitHub Discussions**: Ask questions and share ideas
- **Discord Server**: Real-time chat with contributors
- **Stack Overflow**: Tag questions with `estatecore`

### Maintainer Contact
- **Email**: developers@estatecore.com
- **GitHub**: @estatecore-maintainers

### Documentation Resources
- [Project README](README.md)
- [API Documentation](docs/API_DOCUMENTATION.md)
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)
- [Coding Standards](docs/CODING_STANDARDS.md)

## Recognition

### Contributors
All contributors are recognized in:
- **README.md**: Contributors section
- **Release notes**: Major contribution acknowledgments
- **Annual report**: Top contributors highlighted

### Maintainers
Outstanding contributors may be invited to become maintainers with:
- **Commit access** to the repository
- **Review responsibilities**
- **Release management** participation

## License

By contributing to EstateCore, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to EstateCore! Your efforts help make property management more efficient and accessible for everyone.
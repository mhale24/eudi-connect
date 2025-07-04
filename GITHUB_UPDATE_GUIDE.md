# GitHub Repository Update Guide

This guide contains all the changes needed to update your GitHub repository with the fixes that resolve the Docker container startup issues.

## Summary of Changes Made

### 1. Critical Docker Configuration Fix
- **File**: `docker-compose.yml`
- **Change**: Remove the `CORS_ORIGINS=http://localhost:3000` environment variable from the api service
- **Reason**: This was causing Pydantic parsing errors preventing container startup

### 2. Updated Dependencies
- **File**: `packages/api/pyproject.toml`
- **Added Dependencies**:
  - `redis = "^5.0.1"`
  - `aioredis = "^2.0.1"`
  - `email-validator = "^2.1.0"`
  - `jsonschema = "^4.20.0"`
  - `jinja2 = "^3.1.2"`
  - `numpy = "^1.25.2"`
  - `scikit-learn = "^1.3.2"`
  - `joblib = "^1.3.2"`
  - `scipy = "^1.11.4"`
  - `prometheus-client = "^0.19.0"`

### 3. Code Fixes Applied
All the following files have been fixed locally and need to be pushed:

#### Core Configuration
- `packages/api/eudi_connect/core/config.py` - Added DEBUG field, fixed CORS_ORIGINS handling
- `packages/api/eudi_connect/core/errors.py` - Added missing exception classes

#### Exception Handling
- `packages/api/eudi_connect/exceptions/base.py` - **NEW FILE** - Base exception classes

#### API Endpoints
- `packages/api/eudi_connect/api/v1/endpoints/billing.py` - Fixed AsyncSession and imports
- `packages/api/eudi_connect/api/v1/endpoints/credentials.py` - Fixed FastAPI dependency injection
- `packages/api/eudi_connect/api/v1/endpoints/wallet.py` - Fixed Python parameter ordering

#### Models and Services
- `packages/api/eudi_connect/models/revocation.py` - Fixed SQLAlchemy reserved attribute conflict
- `packages/api/eudi_connect/services/didkit.py` - Fixed imports and added missing zlib import
- `packages/api/eudi_connect/services/notification.py` - Fixed import paths

#### Additional Files
- `packages/api/requirements.txt` - **NEW FILE** - Complete dependency list as backup
- `packages/api/test_direct_run.py` - **NEW FILE** - Test script for debugging

## Git Commands to Update Repository

### Step 1: Stage All Changes
```bash
cd "My Projects/Vibe Coding Projects/EU SAAS app/eudi-connect"
git add .
```

### Step 2: Commit Changes
```bash
git commit -m "Fix Docker container startup issues and add missing dependencies

- Remove problematic CORS_ORIGINS environment variable from docker-compose.yml
- Add missing dependencies to pyproject.toml (redis, email-validator, scientific packages)
- Fix FastAPI dependency injection issues across multiple endpoints
- Add missing exception classes and base exception handling
- Fix SQLAlchemy model conflicts and import issues
- Add comprehensive requirements.txt as backup dependency management
- Add test script for direct debugging outside Docker

All containers now start successfully and API responds correctly."
```

### Step 3: Push to GitHub
```bash
git push origin main
```

## Verification Steps

After pushing to GitHub, anyone cloning the repository should be able to:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/mhale24/eudi-connect.git
   cd eudi-connect
   ```

2. **Start the containers**:
   ```bash
   docker-compose up --build
   ```

3. **Verify API is running**:
   - Visit: http://localhost:8000/health
   - Visit: http://localhost:8000/docs (API documentation)

## Key Improvements

### Before Updates:
- ❌ Container failed to start due to CORS_ORIGINS parsing errors
- ❌ Missing critical dependencies causing ModuleNotFoundError
- ❌ FastAPI dependency injection issues
- ❌ SQLAlchemy model conflicts
- ❌ Import errors across multiple files

### After Updates:
- ✅ Container starts successfully
- ✅ All dependencies properly installed
- ✅ FastAPI endpoints work correctly
- ✅ Proper exception handling
- ✅ Clean imports and no conflicts
- ✅ API responds to health checks and serves documentation

## Files That Will Be Updated on GitHub

### Modified Files:
- `docker-compose.yml`
- `packages/api/pyproject.toml`
- `packages/api/eudi_connect/core/config.py`
- `packages/api/eudi_connect/core/errors.py`
- `packages/api/eudi_connect/api/v1/endpoints/billing.py`
- `packages/api/eudi_connect/api/v1/endpoints/credentials.py`
- `packages/api/eudi_connect/api/v1/endpoints/wallet.py`
- `packages/api/eudi_connect/models/revocation.py`
- `packages/api/eudi_connect/services/didkit.py`
- `packages/api/eudi_connect/services/notification.py`

### New Files:
- `packages/api/eudi_connect/exceptions/base.py`
- `packages/api/requirements.txt`
- `packages/api/test_direct_run.py`
- `GITHUB_UPDATE_GUIDE.md` (this file)

This comprehensive update resolves all the Docker containerization issues and ensures the FastAPI application runs correctly in both development and production environments.
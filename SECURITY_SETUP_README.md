# JuniorGPT Security Setup Guide

## 🔒 Flask Secret Key Security

JuniorGPT now includes comprehensive Flask secret key management following security best practices from the tutorials provided.

## 🚀 Quick Setup

### 1. Automatic Security Setup (Recommended)
```bash
# Run the complete security setup
python setup_security.py
```

This will:
- Generate a cryptographically secure 64-character secret key
- Create/update your `.env` file
- Verify all security settings
- Create a security checklist

### 2. Manual Secret Key Generation
```bash
# Generate just a secret key
python generate_secret_key.py
```

Choose from three secure generation methods:
- **Hexadecimal** (recommended): 64-character hex string
- **URL-Safe Base64**: 43-character URL-safe string  
- **UUID-based**: 32-character UUID hex string

## 🔧 Implementation Details

### Secret Key Generation Methods

Following the tutorials, we implement three secure methods:

#### 1. Using `secrets.token_hex()` (Recommended)
```python
import secrets
secret_key = secrets.token_hex(32)  # 64 characters
```

#### 2. Using `secrets.token_urlsafe()`
```python
import secrets
secret_key = secrets.token_urlsafe(32)  # ~43 characters
```

#### 3. Using `uuid.uuid4().hex`
```python
import uuid
secret_key = uuid.uuid4().hex  # 32 characters
```

### Configuration Security

#### Development Mode
- Auto-generates secure fallback key using `secrets.token_hex(32)`
- Warns if using example keys
- Validates key length (minimum 32 characters)

#### Production Mode
- **Requires explicit FLASK_SECRET_KEY** environment variable
- Fails startup if production key not set
- Validates key strength and length

### Environment Variable Management

```python
# config.py - Secure configuration loading
SECRET_KEY: str = os.environ.get('FLASK_SECRET_KEY', _generate_fallback_secret_key())

def _generate_fallback_secret_key() -> str:
    if os.environ.get('FLASK_ENV') == 'production':
        return 'PRODUCTION-KEY-REQUIRED-SET-FLASK_SECRET_KEY'
    else:
        return secrets.token_hex(32)  # Secure development fallback
```

## 📋 Security Features

### ✅ What's Implemented

1. **Cryptographically Secure Key Generation**
   - Uses `secrets` module for cryptographic randomness
   - 32+ byte keys (64+ characters hex)
   - No predictable patterns

2. **Environment-Based Configuration**
   - Keys stored in `.env` file only
   - Never hardcoded in source code
   - Different behavior for dev/prod environments

3. **Automatic Validation**
   - Startup validation of key presence and strength
   - Length requirements (32+ characters)
   - Production environment checks

4. **Security Best Practices**
   - CSRF protection enabled by default
   - XSS protection implemented
   - Input sanitization
   - Secure session management

### 🛡️ Security Layers

```
┌─────────────────────────────────────┐
│           Application Layer         │
│  • CSRF Protection                  │
│  • XSS Protection                   │
│  • Input Validation                 │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│          Session Layer              │
│  • Secure Secret Key               │
│  • Cryptographic Signatures        │
│  • Session Cookie Security          │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│        Configuration Layer          │
│  • Environment Variables           │
│  • Key Rotation Support            │
│  • Environment-Specific Settings   │
└─────────────────────────────────────┘
```

## 📖 Usage Examples

### Basic Setup
```bash
# 1. Clone repository
git clone <repo-url>
cd juniorgpt

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up security (generates keys, creates .env)
python setup_security.py

# 4. Add your API keys to .env
nano .env  # Add OPENAI_API_KEY and ANTHROPIC_API_KEY

# 5. Run application
python app_plugin.py
```

### Production Deployment
```bash
# 1. Set production environment
export FLASK_ENV=production

# 2. Generate production secret key
python generate_secret_key.py

# 3. Set environment variables
export FLASK_SECRET_KEY="your_secure_production_key_here"
export OPENAI_API_KEY="your_openai_key"
export ANTHROPIC_API_KEY="your_anthropic_key"

# 4. Run with production settings
python app_plugin.py
```

### Manual Key Management
```python
# Generate new key programmatically
import secrets

# Method 1: Hexadecimal (recommended)
key = secrets.token_hex(32)
print(f"FLASK_SECRET_KEY={key}")

# Method 2: URL-safe base64
key = secrets.token_urlsafe(32)
print(f"FLASK_SECRET_KEY={key}")

# Method 3: UUID-based
import uuid
key = uuid.uuid4().hex
print(f"FLASK_SECRET_KEY={key}")
```

## 🔍 Security Validation

### Automated Checks
```bash
# Run security validation
python setup_security.py

# Check configuration
python -c "from config import get_config; c=get_config(); print('Key length:', len(c.SECRET_KEY))"
```

### Manual Verification
```python
# Verify secret key in Python
import os
from dotenv import load_dotenv
load_dotenv()

key = os.environ.get('FLASK_SECRET_KEY')
print(f"Key present: {bool(key)}")
print(f"Key length: {len(key) if key else 0}")
print(f"Is secure: {len(key) >= 32 if key else False}")
```

## ⚠️ Security Warnings

### Development
- ✅ Auto-generated keys are secure for development
- ⚠️ Don't use development keys in production
- ⚠️ Don't commit `.env` files to version control

### Production
- 🚨 **Always set explicit FLASK_SECRET_KEY**
- 🚨 **Use HTTPS/TLS encryption**
- 🚨 **Regularly rotate secret keys**
- 🚨 **Monitor for security vulnerabilities**

## 📋 Security Checklist

A comprehensive security checklist is automatically generated at `SECURITY_CHECKLIST.md` covering:

- Development security requirements
- Production security requirements  
- API key security practices
- Database security measures
- Infrastructure security guidelines

## 🔄 Key Rotation

### How to Rotate Secret Keys

1. **Generate new key**:
   ```bash
   python generate_secret_key.py
   ```

2. **Update environment**:
   ```bash
   # Update .env file or environment variables
   FLASK_SECRET_KEY=new_secure_key_here
   ```

3. **Restart application**:
   ```bash
   # Sessions will be invalidated (users need to log in again)
   python app_plugin.py
   ```

### Automated Rotation (Future Enhancement)
```python
# Example rotation script
def rotate_secret_key():
    new_key = secrets.token_hex(32)
    # Update .env file
    # Restart application
    # Notify administrators
```

## 🛠️ Troubleshooting

### Common Issues

**1. "FLASK_SECRET_KEY not set" error**
```bash
# Generate and set key
python generate_secret_key.py
# Or set manually in .env
```

**2. "Secret key too short" warning**
```bash
# Generate 32+ character key
python -c "import secrets; print(secrets.token_hex(32))"
```

**3. Sessions not working**
```bash
# Check key is properly loaded
python -c "from config import get_config; print(len(get_config().SECRET_KEY))"
```

**4. Production startup fails**
```bash
# Set production secret key
export FLASK_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
```

## 📚 References

- [Flask Secret Key Security](https://flask.palletsprojects.com/en/2.0.x/config/#SECRET_KEY)
- [Python secrets module](https://docs.python.org/3/library/secrets.html)
- [Cryptographically secure random numbers](https://docs.python.org/3/library/secrets.html#recipes-and-best-practices)
- [Flask Security Best Practices](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-v-user-logins)

## 🎯 Summary

The JuniorGPT security implementation provides:

✅ **Cryptographically secure key generation** using `secrets` module  
✅ **Environment-based configuration** with validation  
✅ **Development vs Production** security modes  
✅ **Automated security setup** with one-command installation  
✅ **Comprehensive security checklist** and monitoring  
✅ **Best practices implementation** following Flask security guidelines  

Your Flask application is now secured with industry-standard secret key management! 🔒
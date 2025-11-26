# Python Version Upgrade - TODO

## Current Status

**Current Version**: Python 3.9  
**Target Version**: Python 3.11+ or 3.12  
**Priority**: Medium (when convenient)

## Why Upgrade?

### Benefits of Python 3.11+

1. **Performance**: 10-60% faster than Python 3.9
2. **Better Error Messages**: More helpful tracebacks
3. **Type Hints**: Improved type hint syntax
4. **Security**: Latest security patches
5. **Modern Features**: 
   - Better async/await support
   - Improved pattern matching
   - Exception groups
   - TOML support in stdlib

### For This Project

- ✅ **Native scrypt support** - Can use default Werkzeug password hashing
- ✅ **Better performance** - Faster request handling
- ✅ **Future-proof** - Python 3.9 EOL is October 2025
- ✅ **Better debugging** - Improved error messages

## Current Workaround

We're using `pbkdf2:sha256` for password hashing instead of the default `scrypt` because Python 3.9's hashlib doesn't have scrypt support in your build.

**File**: `app/models/person.py`
```python
# Current workaround for Python 3.9
self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
```

**After upgrade**, we can use:
```python
# Default method (uses scrypt on Python 3.11+)
self.password_hash = generate_password_hash(password)
```

## When to Upgrade

Good times to upgrade:
- ✅ Before deploying to production
- ✅ When setting up a new development machine
- ✅ After completing MVP (Phase 4)
- ✅ When you have time for testing

**Not urgent** - Current setup works perfectly fine!

## Upgrade Steps

### 1. Install Python 3.11 or 3.12

**macOS (Homebrew)**:
```bash
brew install python@3.12
```

**macOS (Official Installer)**:
Download from https://www.python.org/downloads/

**Linux (Ubuntu/Debian)**:
```bash
sudo apt update
sudo apt install python3.12 python3.12-venv
```

### 2. Create New Virtual Environment

```bash
# Deactivate current venv
deactivate

# Backup old venv (optional)
mv venv venv_old

# Create new venv with Python 3.12
python3.12 -m venv venv

# Activate new venv
source venv/bin/activate

# Verify version
python --version  # Should show Python 3.12.x
```

### 3. Reinstall Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Test Everything

```bash
# Run tests
pytest

# Start app
flask run

# Test login
# Test database operations
# Test all features
```

### 5. Update Password Hashing (Optional)

After confirming everything works, you can simplify the password hashing:

**In `app/models/person.py`**:
```python
def set_password(self, password):
    """Set password hash for organizer login."""
    # Can now use default method (scrypt)
    self.password_hash = generate_password_hash(password)
```

### 6. Update Documentation

Update these files to reflect Python 3.11+ requirement:
- `README.md`
- `requirements.txt` (add Python version comment)
- `.python-version` (create this file with `3.12`)

## Compatibility Notes

### What Will Break?
- ❌ Nothing! Python 3.11+ is backward compatible with 3.9 code

### What to Test?
- ✅ Password hashing/login
- ✅ Database operations
- ✅ Email sending (Brevo)
- ✅ Background scheduler
- ✅ All routes and templates

## Requirements.txt Update

After upgrade, add Python version requirement:

```txt
# Python 3.11+ required
# Recommended: Python 3.12

Flask==3.0.0
# ... rest of requirements
```

## Production Deployment

When deploying to production, make sure:
- Server has Python 3.11+ installed
- Virtual environment uses correct Python version
- All dependencies install correctly
- Run full test suite before going live

## Rollback Plan

If something breaks:

```bash
# Deactivate new venv
deactivate

# Restore old venv
rm -rf venv
mv venv_old venv

# Activate old venv
source venv/bin/activate

# You're back to Python 3.9
```

## Timeline Suggestion

**Recommended Upgrade Points**:

1. **Now** (if you have 30 minutes):
   - Low risk, high benefit
   - Good time since you're just starting development

2. **After Phase 1** (Weeks 1-3):
   - After basic features are working
   - Before building complex features

3. **Before Production** (Week 10+):
   - Must upgrade before Python 3.9 EOL (Oct 2025)
   - Better performance for production

## Notes

- Current Python 3.9 setup works perfectly fine
- No urgent need to upgrade
- Upgrade when convenient
- Test thoroughly after upgrading
- Keep this file as a reference

---

**Status**: 📝 TODO - Upgrade when convenient  
**Priority**: Medium  
**Estimated Time**: 30 minutes  
**Risk**: Low (backward compatible)  
**Benefit**: High (performance, security, future-proof)

---

**Created**: 2024-11-24  
**Current Python**: 3.9  
**Target Python**: 3.11+ or 3.12


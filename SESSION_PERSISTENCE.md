# Session Persistence Across Server Restarts

## Problem Statement

By default, Flask sessions are stored in signed cookies on the client side. While the session data persists in the cookie, during development with auto-reload enabled, sessions can be lost due to various reasons:
- Session cookie expiration
- Browser clearing cookies
- Session not marked as permanent
- Development server restarts clearing in-memory state

This requires developers to re-authenticate after every code change, which is time-consuming.

## Solution: Flask-Session with Filesystem Storage

We've implemented **Flask-Session** to store session data server-side, making sessions persist across server restarts during development.

---

## How It Works

### Development Mode (Default)
- **Session Storage**: Filesystem (`flask_session/` directory)
- **Session Lifetime**: 7 days
- **Persistence**: ✅ Sessions survive server restarts
- **Security**: Sessions are signed with SECRET_KEY

### Production Mode
- **Session Storage**: Redis (recommended) or filesystem
- **Session Lifetime**: 7 days
- **Persistence**: ✅ Sessions survive server restarts and scale across multiple servers
- **Security**: HTTPS-only cookies, signed sessions

---

## Configuration

### Development (config.py)

```python
class DevelopmentConfig(Config):
    # Session storage
    SESSION_TYPE = "filesystem"
    SESSION_FILE_DIR = "flask_session/"
    SESSION_PERMANENT = True
    SESSION_COOKIE_SECURE = False  # Allow HTTP
```

### Production (config.py)

```python
class ProductionConfig(Config):
    # Session storage
    SESSION_TYPE = "redis"  # More scalable
    SESSION_REDIS = os.environ.get("REDIS_URL")
    SESSION_COOKIE_SECURE = True  # Require HTTPS
```

---

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `Flask-Session==0.5.0` - Server-side session management
- `cachelib==0.10.2` - Required by Flask-Session

### 2. Verify Installation

```bash
pip list | grep Flask-Session
```

Should show: `Flask-Session 0.5.0`

---

## Usage

### Login with Persistent Session

When you log in, the session is automatically marked as permanent:

```python
# In app/routes/organizer.py
session.permanent = True  # Session persists for 7 days
session["person_id"] = person.id
```

### Session Lifetime

Sessions last for **7 days** by default:

```python
# In config.py
PERMANENT_SESSION_LIFETIME = timedelta(days=7)
```

### Manual Logout

Sessions are cleared on logout:

```python
session.clear()  # Removes all session data
```

---

## File Structure

```
holiday_party_planner/
├── flask_session/          # Session storage (gitignored)
│   ├── 2029240f6d1128be89ddc32729463129
│   ├── 3f7a8b2c9d4e5f6a7b8c9d0e1f2a3b4c
│   └── ...
├── config.py               # Session configuration
├── app/
│   └── __init__.py        # Flask-Session initialization
└── .gitignore             # Excludes flask_session/
```

---

## Security Considerations

### Development vs Production

| Feature | Development | Production |
|---------|-------------|------------|
| Storage | Filesystem | Redis |
| HTTPS Required | ❌ No | ✅ Yes |
| Session Signing | ✅ Yes | ✅ Yes |
| Cookie Security | Relaxed | Strict |
| Session Lifetime | 7 days | 7 days |

### Development Security

**Safe for Development**:
- ✅ Sessions stored locally on your machine
- ✅ Sessions are signed (can't be tampered with)
- ✅ `flask_session/` is gitignored (not committed)
- ✅ Only accessible on localhost

**Not Safe for Production**:
- ❌ Filesystem storage doesn't scale
- ❌ HTTP cookies can be intercepted
- ❌ No HTTPS requirement

### Production Security

**Required for Production**:
- ✅ Use Redis for session storage
- ✅ Enable HTTPS-only cookies (`SESSION_COOKIE_SECURE = True`)
- ✅ Set strong `SECRET_KEY` from environment variable
- ✅ Use secure Redis connection (TLS)
- ✅ Set `SESSION_COOKIE_HTTPONLY = True` (prevents XSS)
- ✅ Set `SESSION_COOKIE_SAMESITE = "Lax"` (prevents CSRF)

---

## Environment-Specific Behavior

### Automatic Configuration

The app automatically uses the correct session storage based on `FLASK_ENV`:

```bash
# Development (default)
export FLASK_ENV=development
flask run
# → Uses filesystem sessions

# Production
export FLASK_ENV=production
flask run
# → Uses Redis sessions (requires REDIS_URL)
```

### Override Session Type

You can override the session type with an environment variable:

```bash
# Force Redis in development (for testing)
export SESSION_TYPE=redis
export REDIS_URL=redis://localhost:6379
flask run
```

---

## Troubleshooting

### Sessions Still Not Persisting

**Check 1**: Verify Flask-Session is installed
```bash
pip list | grep Flask-Session
```

**Check 2**: Verify session directory exists
```bash
ls -la flask_session/
```

**Check 3**: Check Flask logs for session initialization
```bash
flask run
# Look for: "Created session directory: flask_session/"
```

**Check 4**: Verify session is marked as permanent
```python
# In login route
session.permanent = True  # Must be set!
```

### Session Directory Not Created

```bash
# Manually create it
mkdir flask_session
```

### Sessions Cleared on Browser Close

This is normal browser behavior. The session data is still on the server, but the browser clears the session cookie. To prevent this:

```python
# In config.py (already set)
SESSION_PERMANENT = True
```

### Redis Connection Error (Production)

```bash
# Check Redis is running
redis-cli ping
# Should return: PONG

# Check REDIS_URL is set
echo $REDIS_URL
# Should return: redis://localhost:6379 (or your Redis URL)
```

---

## Testing Session Persistence

### Test 1: Login and Restart Server

1. **Log in**: http://localhost:5000/organizer/login
2. **Verify logged in**: See dashboard
3. **Restart Flask**: Press Ctrl+C, then `flask run`
4. **Refresh browser**: http://localhost:5000/organizer/
5. **✅ Expected**: Still logged in, see dashboard

### Test 2: Check Session Files

```bash
# After logging in
ls -la flask_session/
# Should see session files

# View session file (they're pickled, so not human-readable)
file flask_session/*
# Should show: data
```

### Test 3: Manual Session Cleanup

```bash
# Clear all sessions
rm -rf flask_session/*

# Restart Flask
flask run

# Try to access dashboard
# ✅ Expected: Redirected to login (session cleared)
```

---

## Production Deployment

### Using Redis (Recommended)

**1. Install Redis**:
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis
```

**2. Set Environment Variables**:
```bash
export FLASK_ENV=production
export SESSION_TYPE=redis
export REDIS_URL=redis://localhost:6379
```

**3. Update config.py** (already done):
```python
class ProductionConfig(Config):
    SESSION_TYPE = os.environ.get("SESSION_TYPE", "redis")
    SESSION_REDIS = os.environ.get("REDIS_URL")
```

**4. Deploy**:
```bash
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app('production')"
```

### Using Filesystem (Not Recommended for Production)

If you must use filesystem in production:

```bash
export SESSION_TYPE=filesystem
export SESSION_FILE_DIR=/var/lib/holiday_party/sessions
```

**Limitations**:
- ❌ Doesn't scale across multiple servers
- ❌ Slower than Redis
- ❌ Requires shared filesystem for load balancing

---

## Maintenance

### Clear Old Sessions

Sessions are automatically cleaned up after expiration, but you can manually clear them:

```bash
# Development
rm -rf flask_session/*

# Production (Redis)
redis-cli FLUSHDB  # ⚠️ Clears ALL Redis data!
```

### Monitor Session Storage

```bash
# Development: Check disk usage
du -sh flask_session/

# Production: Check Redis memory
redis-cli INFO memory
```

---

## Summary

✅ **What's Implemented**:
- Server-side session storage with Flask-Session
- Filesystem storage for development
- Redis support for production
- 7-day session lifetime
- Automatic session persistence
- Security best practices

✅ **Benefits**:
- No more re-authentication after server restarts
- Faster development workflow
- Production-ready session management
- Scalable with Redis

✅ **Security**:
- Sessions are signed and secure
- Development uses filesystem (safe for local dev)
- Production uses Redis with HTTPS
- Session data never exposed to client

---

**Status**: ✅ Implemented and Ready to Use!  
**Next**: Install dependencies and restart Flask to test!


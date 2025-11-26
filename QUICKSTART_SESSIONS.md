# Quick Start: Persistent Sessions

## TL;DR - Get Started in 2 Minutes

```bash
# 1. Install dependencies
pip install Flask-Session==0.5.0 cachelib==0.10.2

# 2. Restart Flask
flask run

# 3. Log in and test!
# Visit: http://localhost:5000/organizer/login
# Login with: john.smith@example.com / password123
# Restart Flask (Ctrl+C, then flask run)
# Refresh browser - you should still be logged in! 🎉
```

---

## What Changed?

### ✅ Sessions Now Persist Across Server Restarts

**Before**:
- 😞 Logged out after every server restart
- 😞 Had to re-authenticate constantly
- 😞 Slow development workflow

**After**:
- 🎉 Stay logged in across restarts
- 🎉 Sessions last 7 days
- 🎉 Fast development workflow

---

## How It Works

### Session Storage

**Development** (automatic):
- Sessions stored in `flask_session/` directory
- Survives server restarts
- Automatically cleaned up after 7 days

**Production** (when deployed):
- Sessions stored in Redis
- Scales across multiple servers
- More secure with HTTPS

---

## Installation

### Option 1: Automatic Setup (Recommended)

```bash
./setup_persistent_sessions.sh
```

### Option 2: Manual Setup

```bash
# Install packages
pip install Flask-Session==0.5.0 cachelib==0.10.2

# Create session directory
mkdir -p flask_session

# Restart Flask
flask run
```

---

## Testing

### Test Session Persistence

1. **Log in**:
   ```
   http://localhost:5000/organizer/login
   Email: john.smith@example.com
   Password: password123
   ```

2. **Verify logged in**:
   - You should see the organizer dashboard
   - Your name should appear in the UI

3. **Restart Flask**:
   ```bash
   # Press Ctrl+C to stop
   flask run
   ```

4. **Refresh browser**:
   - Visit: http://localhost:5000/organizer/
   - ✅ **You should still be logged in!**

5. **Check session files**:
   ```bash
   ls -la flask_session/
   # You should see session files
   ```

---

## Configuration

### Session Lifetime

Sessions last **7 days** by default. To change:

```python
# In config.py
PERMANENT_SESSION_LIFETIME = timedelta(days=30)  # 30 days
```

### Clear Sessions

```bash
# Clear all sessions (logs everyone out)
rm -rf flask_session/*
```

### Disable Persistent Sessions

To go back to default Flask sessions:

```python
# In config.py - DevelopmentConfig
SESSION_TYPE = None  # Use default cookie-based sessions
```

---

## Files Modified

| File | Change |
|------|--------|
| `config.py` | Added Flask-Session configuration |
| `app/__init__.py` | Initialize Flask-Session |
| `app/routes/organizer.py` | Set `session.permanent = True` on login |
| `requirements.txt` | Added Flask-Session and cachelib |
| `.gitignore` | Added `flask_session/` |

---

## Security Notes

### Development (Current Setup)

✅ **Safe for local development**:
- Sessions stored on your local machine
- Not accessible over network
- Automatically gitignored

❌ **Not for production**:
- Filesystem storage doesn't scale
- No HTTPS requirement

### Production (When Deploying)

The app automatically switches to Redis in production:

```bash
# Set environment variables
export FLASK_ENV=production
export REDIS_URL=redis://localhost:6379

# Sessions now use Redis (scalable & secure)
```

---

## Troubleshooting

### Still Getting Logged Out?

**Check 1**: Verify Flask-Session is installed
```bash
pip list | grep Flask-Session
# Should show: Flask-Session 0.5.0
```

**Check 2**: Verify session directory exists
```bash
ls -la flask_session/
# Should show session files after login
```

**Check 3**: Check Flask startup logs
```bash
flask run
# Look for: "Created session directory: flask_session/"
```

**Check 4**: Clear browser cookies and try again
```
Browser → Settings → Clear Cookies → Try logging in again
```

### Session Directory Not Created

```bash
# Create it manually
mkdir -p flask_session

# Restart Flask
flask run
```

### Import Error

```bash
# If you see: ModuleNotFoundError: No module named 'flask_session'
pip install Flask-Session==0.5.0 cachelib==0.10.2
```

---

## FAQ

### Q: Will this work in production?

**A**: Yes! The app automatically uses Redis in production for better scalability.

### Q: How long do sessions last?

**A**: 7 days by default. Configurable in `config.py`.

### Q: Is this secure?

**A**: Yes! Sessions are signed with your SECRET_KEY and can't be tampered with.

### Q: Can I disable this feature?

**A**: Yes! Set `SESSION_TYPE = None` in config.py to use default Flask sessions.

### Q: Will this affect my existing sessions?

**A**: No. Existing sessions will continue to work. New sessions will be stored server-side.

### Q: Do I need Redis for development?

**A**: No! Development uses filesystem storage. Redis is only needed for production.

---

## Benefits

✅ **Development**:
- No more constant re-authentication
- Faster development workflow
- Sessions survive server restarts
- Easy to set up (2 commands)

✅ **Production**:
- Scalable with Redis
- Works across multiple servers
- Secure with HTTPS
- Industry-standard solution

✅ **Security**:
- Sessions are signed
- Can't be tampered with
- Automatic expiration
- HTTPS-only in production

---

## Next Steps

1. ✅ Install dependencies: `pip install Flask-Session cachelib`
2. ✅ Restart Flask: `flask run`
3. ✅ Test login persistence
4. 📚 Read full docs: `SESSION_PERSISTENCE.md`

---

**Status**: ✅ Ready to Use!  
**Time to Setup**: 2 minutes  
**Benefit**: Huge time savings during development!

---

**Questions?** See `SESSION_PERSISTENCE.md` for detailed documentation.


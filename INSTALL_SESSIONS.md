# Install Persistent Sessions - Step by Step

## 🎯 Goal

Enable sessions to persist across Flask server restarts during development.

---

## ⚡ Quick Install (2 Commands)

```bash
# 1. Install packages
pip install Flask-Session==0.5.0 cachelib==0.10.2

# 2. Restart Flask
flask run
```

**That's it!** Sessions now persist across restarts. 🎉

---

## 📋 Detailed Steps

### Step 1: Activate Virtual Environment

```bash
# Make sure you're in the project directory
cd /path/to/holiday_party_planner

# Activate virtual environment
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install Flask-Session==0.5.0 cachelib==0.10.2
```

**What this installs**:
- `Flask-Session` - Server-side session management
- `cachelib` - Required dependency for Flask-Session

### Step 3: Verify Installation

```bash
pip list | grep Flask-Session
```

**Expected output**:
```
Flask-Session    0.5.0
```

### Step 4: Restart Flask

```bash
# Stop Flask if running (Ctrl+C)
# Then start it again
flask run
```

**Look for this in the logs**:
```
Created session directory: flask_session/
```

### Step 5: Test Session Persistence

1. **Log in**:
   - Go to: http://localhost:5000/organizer/login
   - Email: `john.smith@example.com`
   - Password: `password123`

2. **Verify logged in**:
   - You should see the organizer dashboard

3. **Restart Flask**:
   ```bash
   # Press Ctrl+C to stop
   flask run
   ```

4. **Refresh browser**:
   - Go to: http://localhost:5000/organizer/
   - ✅ **You should still be logged in!**

5. **Check session files**:
   ```bash
   ls -la flask_session/
   ```
   
   **Expected output**:
   ```
   total 8
   drwxr-xr-x  3 user  staff   96 Nov 24 10:30 .
   drwxr-xr-x 25 user  staff  800 Nov 24 10:30 ..
   -rw-r--r--  1 user  staff  234 Nov 24 10:30 2029240f6d1128be89ddc32729463129
   ```

---

## ✅ Verification Checklist

- [ ] Virtual environment activated
- [ ] Flask-Session installed (`pip list | grep Flask-Session`)
- [ ] Flask restarted
- [ ] Logged in successfully
- [ ] Restarted Flask again
- [ ] Still logged in after restart ✅
- [ ] Session files exist in `flask_session/`

---

## 🔧 Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'flask_session'"

**Solution**:
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Install Flask-Session
pip install Flask-Session==0.5.0 cachelib==0.10.2
```

### Problem: Still getting logged out after restart

**Check 1**: Verify Flask-Session is installed
```bash
pip list | grep Flask-Session
```

**Check 2**: Verify session directory exists
```bash
ls -la flask_session/
```

**Check 3**: Check Flask logs
```bash
flask run
# Look for: "Created session directory: flask_session/"
```

**Check 4**: Clear browser cookies and try again
- Browser → Settings → Clear Cookies
- Log in again
- Test restart

### Problem: Session directory not created

**Solution**:
```bash
# Create it manually
mkdir -p flask_session

# Restart Flask
flask run
```

### Problem: Permission denied on flask_session/

**Solution**:
```bash
# Fix permissions
chmod 755 flask_session

# Restart Flask
flask run
```

---

## 🎓 What Changed?

### Before Installation

```
User logs in → Session in cookie → Server restarts → Session lost → User logged out ❌
```

### After Installation

```
User logs in → Session in flask_session/ → Server restarts → Session still there → User still logged in ✅
```

---

## 📁 What Gets Created?

```
holiday_party_planner/
├── flask_session/              # ← New directory (gitignored)
│   ├── 2029240f6d1128be89ddc32729463129
│   ├── 3f7a8b2c9d4e5f6a7b8c9d0e1f2a3b4c
│   └── ...
└── (existing files)
```

**Note**: `flask_session/` is automatically added to `.gitignore` so it won't be committed.

---

## 🔒 Security

### Is This Safe?

✅ **Yes, for development**:
- Sessions stored locally on your machine
- Not accessible over network
- Automatically gitignored
- Signed with SECRET_KEY

✅ **Yes, for production**:
- Automatically switches to Redis
- HTTPS-only cookies
- Industry-standard solution

---

## 📊 Session Lifetime

**Default**: 7 days

**To change**:
```python
# In config.py
PERMANENT_SESSION_LIFETIME = timedelta(days=30)  # 30 days
```

---

## 🧹 Maintenance

### Clear All Sessions (Log Everyone Out)

```bash
rm -rf flask_session/*
```

### View Session Count

```bash
ls -1 flask_session/ | wc -l
```

### View Session Storage Size

```bash
du -sh flask_session/
```

---

## 🚀 Production Deployment

When deploying to production, the app automatically uses Redis:

```bash
# Set environment variables
export FLASK_ENV=production
export REDIS_URL=redis://localhost:6379

# Sessions now use Redis (scalable & secure)
```

**No code changes needed!** The configuration automatically switches based on environment.

---

## 📚 More Information

- **Quick Start**: `QUICKSTART_SESSIONS.md`
- **Full Documentation**: `SESSION_PERSISTENCE.md`
- **Implementation Details**: `SESSION_IMPLEMENTATION_SUMMARY.md`

---

## ✅ Success!

If you can:
1. ✅ Log in
2. ✅ Restart Flask
3. ✅ Still be logged in

**Then it's working!** 🎉

---

## 🎁 Benefits

✅ **No more constant re-authentication**  
✅ **Faster development workflow**  
✅ **Sessions last 7 days**  
✅ **Production-ready**  
✅ **Easy to set up (2 commands)**  

---

**Questions?** Check the troubleshooting section above or see the full documentation.


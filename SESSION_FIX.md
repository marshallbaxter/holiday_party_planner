# Session Fix - request.session vs session

## The Problem

Getting 500 error when trying to log in:
```
AttributeError: 'Request' object has no attribute 'session'
```

## The Cause

In Flask, sessions are accessed via the `session` object imported from Flask, **not** `request.session`.

**Wrong** ❌:
```python
from flask import request
person_id = request.session.get("person_id")
```

**Correct** ✅:
```python
from flask import session
person_id = session.get("person_id")
```

## What Was Fixed

### 1. app/routes/organizer.py
- ✅ Added `session` to imports
- ✅ Changed `request.session.get()` to `session.get()`
- ✅ Changed `request.session["person_id"]` to `session["person_id"]`
- ✅ Changed `request.session.clear()` to `session.clear()`

### 2. app/utils/decorators.py
- ✅ Added `session` to imports
- ✅ Changed all `request.session` references to `session`
- ✅ Fixed in `login_required` decorator
- ✅ Fixed in `event_admin_required` decorator

## Files Modified

1. **app/routes/organizer.py**
   - Line 2: Added `session` to imports
   - Line 15: `session.get("person_id")`
   - Line 124: `session["person_id"] = person.id`
   - Line 141: `session.clear()`

2. **app/utils/decorators.py**
   - Line 3: Added `session` to imports
   - Line 12: `session.get("person_id")`
   - Line 20: `session.clear()`
   - Line 47: `session.get("person_id")`

## Try Again Now

1. **Restart Flask** (if it's still running):
   ```bash
   # Press Ctrl+C to stop
   flask run
   ```

2. **Go to login page**:
   ```
   http://localhost:5000/organizer/login
   ```

3. **Log in with**:
   - Email: `john.smith@example.com`
   - Password: `password123`

4. **You should see the dashboard!** 🎉

## Flask Session vs Request

| Object | Purpose | Usage |
|--------|---------|-------|
| `request` | Current HTTP request | `request.form`, `request.args`, `request.method` |
| `session` | User session data | `session["key"]`, `session.get("key")` |
| `g` | Request-scoped data | `g.current_user`, `g.db` |

## How Flask Sessions Work

```python
from flask import session

# Set session data
session["user_id"] = 123
session["username"] = "john"

# Get session data
user_id = session.get("user_id")  # Returns None if not set
username = session["username"]     # Raises KeyError if not set

# Check if key exists
if "user_id" in session:
    print("User is logged in")

# Clear session
session.clear()

# Remove specific key
session.pop("user_id", None)
```

## Session Configuration

Sessions are configured in `config.py`:

```python
# Secret key for signing session cookies
SECRET_KEY = "your-secret-key"

# Session lifetime
PERMANENT_SESSION_LIFETIME = timedelta(days=7)
```

## Security Notes

- ✅ Sessions are **signed** with SECRET_KEY
- ✅ Sessions are **stored in cookies** (client-side)
- ✅ Sessions are **tamper-proof** (can't be modified by client)
- ⚠️ Sessions are **not encrypted** (don't store sensitive data)
- ⚠️ Use strong SECRET_KEY in production

## Common Session Patterns

### Login
```python
from flask import session

@app.route("/login", methods=["POST"])
def login():
    # Verify credentials
    if user.check_password(password):
        session["user_id"] = user.id
        return redirect("/dashboard")
```

### Logout
```python
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
```

### Check if logged in
```python
from flask import session

def is_logged_in():
    return "user_id" in session
```

### Decorator for protected routes
```python
from functools import wraps
from flask import session, redirect

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function
```

## Troubleshooting

### Session not persisting
- Check SECRET_KEY is set
- Check cookies are enabled in browser
- Check not in incognito/private mode

### Session cleared on every request
- Make sure SECRET_KEY doesn't change
- Check PERMANENT_SESSION_LIFETIME setting

### "KeyError" when accessing session
- Use `session.get("key")` instead of `session["key"]`
- Or check if key exists first: `if "key" in session:`

---

**Status**: ✅ Fixed!  
**Next**: Try logging in again - it should work now!


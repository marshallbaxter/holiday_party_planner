# Development User Switcher Feature

## Overview

A development-only user switching feature has been added to the Holiday Party Planner application. This feature allows developers to quickly switch between different user accounts without logging out and back in, making it much easier to test different user roles and permissions during development.

## Features

✅ **Development-Only**: Only enabled when `FLASK_ENV=development` (automatically disabled in production)
✅ **Easy Access**: Dropdown menu in the navigation header
✅ **Visual Indicator**: Yellow badge shows current user and dev mode status
✅ **Preserves Context**: Stays on the current page after switching users
✅ **Secure**: Only allows switching to users with login credentials (password_hash)
✅ **User-Friendly**: Shows user's full name and email in the dropdown

## How It Works

### 1. Visual Indicator
When logged in during development, you'll see a yellow badge in the navigation bar showing the current user's first name with a user icon and dropdown arrow.

### 2. Dropdown Menu
Click the badge to open a dropdown menu showing all available users (those with passwords). The current user is highlighted with a checkmark.

### 3. Switch Users
Click any user in the dropdown to instantly switch to that user's session. You'll stay on the same page you were on (if possible).

### 4. Confirmation
A success message confirms the switch: "Switched to [User Name]"

## Technical Implementation

### Files Modified

1. **app/routes/organizer.py**
   - Added `dev_switch_user()` route at `/organizer/dev/switch-user/<person_id>`
   - POST-only endpoint for security
   - Validates DEBUG mode, user existence, and password presence
   - Preserves current page via `next` parameter

2. **app/__init__.py**
   - Updated `inject_config()` context processor
   - Injects `is_dev_mode`, `current_person`, and `available_users` into all templates
   - Only queries users with passwords (organizers)

3. **app/templates/base.html**
   - Added Alpine.js for dropdown interactivity
   - Added user switcher UI component in navigation
   - Yellow badge design for clear dev mode indication
   - Responsive dropdown with user list

### Security Features

- **Development Only**: Checks `ENV != "production"` before allowing switches
- **Password Required**: Only users with `password_hash` can be switched to
- **CSRF Protection**: All switch requests include CSRF token
- **Session Management**: Properly sets `session.permanent = True`

## Usage

### Prerequisites
1. Application must be running in development mode
   - Make sure your `.env` file has `FLASK_ENV=development`
   - The feature automatically enables when not in production
2. Database must be seeded with test users (run `flask seed-db`)
3. You must be logged in as an organizer

### Available Test Users
After running `flask seed-db`, you'll have these test accounts:
- john.smith@example.com (password: password123)
- jane.smith@example.com (password: password123)
- bob.johnson@example.com (password: password123)
- alice.johnson@example.com (password: password123)
- mary.williams@example.com (password: password123)

### Steps to Use
1. Log in to the application at `/organizer/login`
2. Look for the yellow badge in the top-right navigation
3. Click the badge to open the user switcher dropdown
4. Click any user to switch to their account
5. The page will reload with the new user's session

## Production Safety

The feature is **completely disabled** in production:
- UI component is hidden when `ENV=production`
- Backend route returns error if accessed in production
- No performance impact when disabled
- No security risk in production environments

## Testing Different Scenarios

### Test Event Admin Permissions
1. Switch to John Smith (event creator)
2. Create an event
3. Switch to Jane Smith
4. Try to access John's event (should be denied)

### Test Guest Management
1. Switch to different organizers
2. Test creating/editing households
3. Verify each user sees only their events

### Test RSVP Workflows
1. Switch between different household members
2. Test RSVP submission from different perspectives
3. Verify organizers can manage RSVPs

## Troubleshooting

### User Switcher Not Visible
- **Verify `FLASK_ENV=development` in your `.env` file**
- Restart Flask application (`flask run`)
- Ensure you're logged in
- Check that test users have passwords (`flask seed-db`)

### "User switching is only available in development mode"
- Set `FLASK_ENV=development` in `.env` file
- Make sure `FLASK_ENV` is NOT set to `production`
- Restart Flask application
- Verify `app.config['ENV']` is not `"production"`

### Dropdown Not Working
- Check browser console for JavaScript errors
- Verify Alpine.js is loading (check network tab)
- Clear browser cache and reload

## Future Enhancements

Possible improvements for future versions:
- Remember last used user per session
- Quick switch keyboard shortcuts
- User role badges in dropdown
- Filter users by role (admin, guest, etc.)
- Recent users list for faster switching


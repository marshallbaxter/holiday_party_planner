# 🧪 Testing Authentication Features

Quick guide to test the new magic link and password reset features.

---

## Prerequisites

1. **Brevo API Key Configured**
   ```bash
   # In your .env file
   BREVO_API_KEY=your-actual-api-key
   BREVO_SENDER_EMAIL=your-verified-email@domain.com
   BREVO_SENDER_NAME=Holiday Party Planner
   ```

2. **Database Migration Applied**
   ```bash
   flask db upgrade
   ```

3. **Flask App Running**
   ```bash
   flask run
   ```

---

## Test 1: Magic Link Login ✨

### Steps:

1. **Navigate to Login Page**
   - Go to: `http://localhost:5000/organizer/login`

2. **Request Magic Link**
   - Scroll to "Or login without a password" section
   - Enter a valid test email: `john.smith@example.com`
   - Click "Send Magic Link"
   - Should see: "A login link has been sent to john.smith@example.com"

3. **Check Email**
   - Open the email inbox for the test account
   - Look for email with subject: "Your login link for Family Holiday Party Planner"
   - Email should have a blue "Log In Now" button

4. **Click Magic Link**
   - Click the "Log In Now" button in the email
   - Should be redirected to: `http://localhost:5000/organizer/verify-magic-link/<token>`
   - Should see: "Welcome back, John!" message
   - Should be logged in and see the dashboard

5. **Try Reusing Link** (Security Test)
   - Click the same magic link again
   - Should see: "Invalid or expired login link"
   - Should NOT be logged in

### Expected Results:
- ✅ Email received within seconds
- ✅ Magic link works on first click
- ✅ User logged in successfully
- ✅ Link fails on second use
- ✅ Session persists across page refreshes

---

## Test 2: Password Reset 🔑

### Steps:

1. **Navigate to Login Page**
   - Go to: `http://localhost:5000/organizer/login`

2. **Click "Forgot password?"**
   - Click the "Forgot password?" link
   - Should be redirected to: `http://localhost:5000/organizer/forgot-password`

3. **Request Password Reset**
   - Enter email: `john.smith@example.com`
   - Click "Send Reset Link"
   - Should see: "If an account exists with that email, you will receive a password reset link shortly."

4. **Check Email**
   - Open the email inbox
   - Look for email with subject: "Reset your password for Family Holiday Party Planner"
   - Email should have a red "Reset Password" button

5. **Click Reset Link**
   - Click the "Reset Password" button
   - Should be redirected to: `http://localhost:5000/organizer/reset-password/<token>`
   - Should see a form with two password fields

6. **Set New Password**
   - Enter new password: `newpassword123` (min 8 characters)
   - Confirm password: `newpassword123`
   - Click "Reset Password"
   - Should see: "Your password has been reset successfully"
   - Should be redirected to login page

7. **Log In with New Password**
   - Enter email: `john.smith@example.com`
   - Enter password: `newpassword123`
   - Click "Log In"
   - Should be logged in successfully

8. **Try Reusing Reset Link** (Security Test)
   - Click the same reset link again
   - Should see: "Invalid or expired password reset link"

### Expected Results:
- ✅ Email received within seconds
- ✅ Reset link works on first use
- ✅ Password validation works (min 8 chars)
- ✅ Password mismatch detected
- ✅ New password works for login
- ✅ Link fails on second use

---

## Test 3: Rate Limiting 🛡️

### Steps:

1. **Request Multiple Magic Links**
   - Go to login page
   - Request magic link 6 times in a row for the same email
   - On the 6th request, should see: "Too many login attempts. Please try again later"

2. **Request Multiple Password Resets**
   - Go to forgot password page
   - Request reset 6 times in a row for the same email
   - Still shows success message (security feature)
   - But no email sent after 5th request

### Expected Results:
- ✅ First 5 requests succeed
- ✅ 6th request blocked
- ✅ Error message shown for magic links
- ✅ Success message still shown for password resets (security)

---

## Test 4: Security Tests 🔒

### Test Invalid Email (Password Reset)

1. Go to forgot password page
2. Enter non-existent email: `doesnotexist@example.com`
3. Click "Send Reset Link"
4. Should see success message (security: don't reveal if email exists)
5. No email should be sent

### Test Expired Token

1. Request a magic link or password reset
2. Wait for expiration (30 min for magic link, 60 min for password reset)
3. Try to use the link
4. Should see: "Invalid or expired link"

### Test Invalid Token

1. Manually edit the URL token to something random
2. Try to access: `http://localhost:5000/organizer/verify-magic-link/invalid-token`
3. Should see: "Invalid or expired login link"

---

## Test 5: Email Template Verification 📧

### Check Magic Link Email:
- ✅ Professional design
- ✅ Clear "Log In Now" button
- ✅ Security warning about expiration
- ✅ Fallback text link
- ✅ Correct recipient email shown
- ✅ "Didn't request this?" message

### Check Password Reset Email:
- ✅ Professional design
- ✅ Clear "Reset Password" button
- ✅ Security warning about expiration
- ✅ Fallback text link
- ✅ Correct recipient email shown
- ✅ "Didn't request this?" message

---

## Troubleshooting

### No Email Received

1. **Check Brevo Configuration**
   ```bash
   # Verify in .env
   BREVO_API_KEY=xkeysib-...
   BREVO_SENDER_EMAIL=verified-email@domain.com
   ```

2. **Check Logs**
   ```bash
   tail -f logs/app.log
   ```
   Look for Brevo API errors

3. **Check Spam Folder**
   - Emails might be in spam/junk folder

4. **Verify Sender Email**
   - Make sure sender email is verified in Brevo dashboard

### Token Not Working

1. **Check Token Expiration**
   - Magic links expire in 30 minutes
   - Password resets expire in 60 minutes

2. **Check Database**
   ```bash
   sqlite3 instance/holiday_party.db
   SELECT * FROM auth_tokens ORDER BY created_at DESC LIMIT 5;
   ```

3. **Check for Used Tokens**
   - Tokens can only be used once
   - `used_at` field should be NULL for unused tokens

### Rate Limiting Issues

1. **Clear Rate Limit**
   ```bash
   # Delete old tokens from database
   sqlite3 instance/holiday_party.db
   DELETE FROM auth_tokens WHERE person_id = 1;
   ```

2. **Adjust Rate Limit**
   ```bash
   # In .env
   AUTH_TOKEN_RATE_LIMIT=10  # Increase limit
   ```

---

## Success Criteria ✅

All tests should pass with:
- ✅ Emails delivered within 5 seconds
- ✅ Magic links work on first use
- ✅ Password resets work correctly
- ✅ Security features prevent abuse
- ✅ Rate limiting protects against spam
- ✅ Error messages are user-friendly
- ✅ Email templates look professional

---

## Next Steps

Once all tests pass:
1. ✅ Mark features as production-ready
2. ✅ Update user documentation
3. ✅ Deploy to staging environment
4. ✅ Perform final testing in staging
5. ✅ Deploy to production

---

**Happy Testing! 🎉**


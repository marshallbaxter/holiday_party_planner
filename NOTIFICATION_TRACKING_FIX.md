# Notification Tracking Fix

**Date**: 2025-11-26  
**Issue**: Notification `sent_at` field not being set when emails are sent  
**Status**: ✅ Fixed

---

## Problem

When investigating why emails weren't being received after clicking "Resend All", I discovered that the `Notification` model has a `sent_at` field that was not being populated when emails were sent. 

**Symptoms:**
- Notifications were created with `status="sent"`
- But `sent_at` field was NULL
- This made it difficult to track when emails were actually sent
- The `Notification` model has helper methods (`mark_sent()`, `mark_failed()`) that weren't being used

---

## Root Cause

In `app/services/notification_service.py`, the `send_email()` method was manually setting the notification status instead of using the model's built-in methods:

**Before (Incorrect):**
```python
notification = Notification(
    event_id=event.id,
    person_id=person.id,
    notification_type="email",
    channel="email",
    status="sent",  # ← Manually setting status
    provider_message_id=api_response.message_id,
)
db.session.add(notification)
db.session.commit()
```

This approach:
- ❌ Doesn't set `sent_at` timestamp
- ❌ Bypasses the model's validation logic
- ❌ Doesn't use the proper `mark_sent()` method

---

## Solution

Updated `NotificationService.send_email()` to use the `Notification` model's built-in methods:

**After (Correct):**
```python
notification = Notification(
    event_id=event.id,
    person_id=person.id,
    notification_type="email",
    channel="email",
)
notification.mark_sent(provider_message_id=api_response.message_id)  # ← Use helper method
db.session.add(notification)
db.session.commit()
```

The `mark_sent()` method (defined in `app/models/notification.py`):
```python
def mark_sent(self, provider_message_id=None):
    """Mark notification as sent."""
    self.status = "sent"
    self.sent_at = datetime.utcnow()  # ← Sets timestamp
    if provider_message_id:
        self.provider_message_id = provider_message_id
```

---

## Changes Made

### File: `app/services/notification_service.py`

**1. Success Case (lines 53-68):**
- Changed to use `notification.mark_sent()`
- Added logging: `current_app.logger.info(f"Email sent successfully to {to_email}: {subject}")`

**2. Brevo API Error Case (lines 70-86):**
- Changed to use `notification.mark_failed()`
- Improved error logging with recipient email

**3. General Exception Case (lines 87-101):**
- Added new exception handler for non-Brevo errors
- Uses `notification.mark_failed()`
- Logs unexpected errors

---

## Benefits

✅ **Proper Timestamp Tracking** - `sent_at` field now populated correctly  
✅ **Better Error Handling** - Catches all exceptions, not just Brevo API errors  
✅ **Improved Logging** - More detailed log messages for debugging  
✅ **Code Consistency** - Uses model methods instead of manual field setting  
✅ **Audit Trail** - Can now accurately track when emails were sent  

---

## Testing

To verify the fix works:

1. **Click "Resend All"** on the event dashboard
2. **Check the notifications table:**
   ```sql
   SELECT id, status, sent_at, error_message, created_at 
   FROM notifications 
   ORDER BY created_at DESC 
   LIMIT 5;
   ```
3. **Verify:**
   - `status` = "sent" (for successful sends)
   - `sent_at` is NOT NULL (should have timestamp)
   - `error_message` is NULL (for successful sends)

4. **Check server logs** for:
   - "Email sent successfully to [email]: [subject]"
   - Or error messages if something went wrong

---

## Impact

**Backward Compatibility:**
- ✅ Existing notifications in database are unaffected
- ✅ Old notifications with NULL `sent_at` will remain as-is
- ✅ New notifications will have proper timestamps

**Future Notifications:**
- All new email sends will have proper `sent_at` timestamps
- Better audit trail for compliance and debugging
- Can now accurately report on email delivery times

---

## Related Files

- `app/services/notification_service.py` - Email sending service (modified)
- `app/models/notification.py` - Notification model with helper methods (no changes)
- `app/services/invitation_service.py` - Uses NotificationService (no changes needed)

---

## Next Steps

1. **Test email sending** - Click "Resend All" and verify emails are received
2. **Check Brevo dashboard** - Verify emails appear in Brevo's transactional logs
3. **Monitor logs** - Watch for any error messages
4. **Verify timestamps** - Check that `sent_at` is now populated in database

---

## Summary

Fixed a bug where the `Notification.sent_at` field wasn't being set when emails were sent. The fix ensures proper timestamp tracking by using the model's built-in `mark_sent()` and `mark_failed()` methods instead of manually setting fields. This provides better audit trails and makes debugging email issues much easier.

**Status**: ✅ Fixed and ready for testing

**Server**: Running on http://127.0.0.1:5001

Please try clicking "Resend All" again to test the fix!


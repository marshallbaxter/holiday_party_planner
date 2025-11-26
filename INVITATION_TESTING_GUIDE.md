# Invitation System Testing Guide

## Quick Start

The invitation system is now fully implemented and ready for testing!

**Server**: http://127.0.0.1:5001  
**Login**: http://127.0.0.1:5001/organizer/login

---

## Prerequisites

1. **Brevo API Key Configured** (in `.env` file)
   ```
   BREVO_API_KEY=your-api-key-here
   BREVO_SENDER_EMAIL=your-verified-email@example.com
   BREVO_SENDER_NAME=Holiday Party Planner
   ```

2. **Database Migrated** ✅ (Already done)
   ```bash
   flask db upgrade
   ```

3. **Server Running** ✅ (Currently running on port 5001)
   ```bash
   flask run --port 5001
   ```

---

## Test Scenarios

### Scenario 1: Send Invitations to All Pending Households

**Steps:**
1. Login as organizer
2. Navigate to an event (or create a new one)
3. Click "Manage Guests"
4. Add 2-3 households with valid email addresses
5. Return to Event Dashboard
6. Observe "Send Invitations" card shows "X pending"
7. Click "Send to X Household(s)" button
8. Confirm in dialog
9. **Expected**: Success message showing "Successfully sent X invitation(s)!"
10. **Verify**: Check recipient email inboxes for invitation emails
11. **Verify**: Invitation status on Manage Guests page shows "✓ Sent [timestamp]"

---

### Scenario 2: Resend Individual Invitation

**Steps:**
1. From Manage Guests page
2. Find a household that has already been sent an invitation
3. Click "Resend" button next to that household
4. **Expected**: Success message "Invitation resent to [Household Name]!"
5. **Verify**: Send count increments (shows "sent (2x)" if sent twice)
6. **Verify**: Recipient receives another email

---

### Scenario 3: Household Without Email

**Steps:**
1. Add a household with NO email addresses (e.g., only children, no adults with email)
2. Try to send invitations
3. **Expected**: Warning message showing "X invitation(s) could not be sent"
4. **Verify**: Households with email receive invitations
5. **Verify**: Household without email shows "⚠️ No email addresses" on Manage Guests page
6. **Verify**: No "Send Now" button appears for households without email

---

### Scenario 4: Resend All Invitations

**Steps:**
1. After all invitations have been sent (pending = 0)
2. Go to Event Dashboard
3. Observe "Send Invitations" card shows "All X invitations sent!"
4. Click "Resend All" button
5. Confirm in dialog
6. **Expected**: All households receive invitation emails again
7. **Verify**: Send counts increment for all households

---

### Scenario 5: No Households Invited

**Steps:**
1. Create a new event
2. Don't add any households
3. Go to Event Dashboard
4. **Expected**: "Send Invitations" card shows "No households invited yet"
5. **Expected**: Link to "Add guests first →"
6. Click link
7. **Expected**: Taken to Manage Guests page

---

### Scenario 6: API Endpoint Testing

**Test Invitation Stats API:**
```bash
curl http://127.0.0.1:5001/api/event/[EVENT_UUID]/invitation-stats
```

**Expected Response:**
```json
{
  "total": 5,
  "sent": 3,
  "pending": 2,
  "no_email": 1,
  "can_send": 1
}
```

---

## Verification Checklist

### Database Verification

Check that invitation tracking fields are populated:

```bash
sqlite3 instance/holiday_party.db "SELECT id, household_id, sent_at, sent_count, last_sent_at FROM event_invitations;"
```

**Expected**: Rows with non-null `sent_at` and `sent_count > 0` for sent invitations

---

### Email Verification

1. **Check Brevo Dashboard**
   - Login to Brevo account
   - Go to "Transactional" → "Logs"
   - Verify emails were sent successfully

2. **Check Recipient Inbox**
   - Email subject: "You're invited to [Event Title]"
   - Email contains event details
   - "RSVP Now" button is present and clickable
   - Token link works correctly

3. **Check Notification Logs**
   ```bash
   sqlite3 instance/holiday_party.db "SELECT * FROM notifications WHERE notification_type='email' ORDER BY sent_at DESC LIMIT 10;"
   ```

---

### UI Verification

**Event Dashboard:**
- [ ] Invitation stats display correctly
- [ ] Button text changes based on state ("Send" vs "Resend All")
- [ ] Warning appears for households without email
- [ ] Confirmation dialog appears before sending
- [ ] Success/error messages display correctly

**Manage Guests Page:**
- [ ] Invitation status shows for each household
- [ ] "✓ Sent [timestamp]" appears for sent invitations
- [ ] "⏳ Pending" appears for unsent invitations
- [ ] Send count displays correctly (e.g., "sent (3x)")
- [ ] "Send Now" / "Resend" button appears only for households with email
- [ ] Button text changes based on send status

---

## Common Issues & Solutions

### Issue: Emails Not Sending

**Possible Causes:**
1. Brevo API key not configured or invalid
2. Sender email not verified in Brevo
3. Recipient email invalid

**Solution:**
- Check `.env` file for correct `BREVO_API_KEY`
- Verify sender email in Brevo dashboard
- Check Brevo logs for error messages
- Check `notifications` table for error messages

---

### Issue: "No email addresses" Warning

**Cause:** Household has no adult members with email addresses

**Solution:**
- Add email address to at least one adult in the household
- Or skip this household (they can be invited via other means)

---

### Issue: Invitation Status Not Updating

**Cause:** Database not committing changes

**Solution:**
- Check server logs for errors
- Verify `mark_as_sent()` is being called
- Check database directly to confirm fields are updating

---

## Performance Testing

### Test with Multiple Households

1. Create 10+ households with email addresses
2. Send invitations to all
3. **Expected**: All emails sent within reasonable time (< 30 seconds)
4. **Verify**: No timeout errors
5. **Verify**: All invitations marked as sent

---

## Security Testing

### Test Authorization

1. **Without Login:**
   - Try to access `/organizer/event/[UUID]/invitations/send` directly
   - **Expected**: Redirect to login page

2. **As Non-Admin:**
   - Login as a person who is NOT an admin of the event
   - Try to send invitations
   - **Expected**: "You don't have permission" error

3. **CSRF Protection:**
   - Try to submit form without CSRF token
   - **Expected**: 400 Bad Request error

---

## Success Criteria

✅ All test scenarios pass  
✅ Emails delivered successfully  
✅ Invitation status tracked correctly  
✅ UI displays accurate information  
✅ Error handling works gracefully  
✅ Authorization enforced properly  
✅ No console errors or warnings  

---

## Next Steps After Testing

1. **Production Deployment:**
   - Update `.env` with production Brevo credentials
   - Test with production email addresses
   - Monitor Brevo quota and usage

2. **User Training:**
   - Document invitation workflow for organizers
   - Create video tutorial if needed

3. **Monitoring:**
   - Set up alerts for failed email sends
   - Monitor Brevo API usage
   - Track invitation open rates (if Brevo webhooks implemented)

---

## Support

If you encounter any issues during testing:

1. Check server logs for error messages
2. Check Brevo dashboard for email delivery status
3. Verify database schema is up to date (`flask db current`)
4. Review `INVITATION_SYSTEM_IMPLEMENTED.md` for implementation details

---

Happy Testing! 🎉


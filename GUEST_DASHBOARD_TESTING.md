# Guest Dashboard Testing Guide

## Quick Start Testing

### Prerequisites
1. Flask app running: `flask run`
2. At least one household created
3. At least 2-3 published events created
4. Household invited to multiple events

---

## Test Scenario 1: Access Dashboard from Invitation Email

**Setup**:
1. Create a household with 2+ members
2. Create 2-3 published events
3. Invite the household to all events
4. Check invitation email (or copy link from organizer dashboard)

**Steps**:
1. Open invitation email
2. Look for "View All My Invitations" button (should be below "RSVP Now")
3. Click the button
4. Verify dashboard loads

**Expected Results**:
- ✅ Dashboard displays household name
- ✅ Shows all household members
- ✅ Lists all events household is invited to
- ✅ Each event shows current RSVP status
- ✅ "RSVP Now" button visible for events without responses
- ✅ Page is mobile-responsive

---

## Test Scenario 2: Navigate Between Dashboard and RSVP Form

**Steps**:
1. From dashboard, click "RSVP Now" on an event
2. Verify RSVP form loads
3. Look for "← My Invitations" link (top left)
4. Click the link
5. Verify dashboard loads
6. Verify you're back at the dashboard

**Expected Results**:
- ✅ Navigation works in both directions
- ✅ "← My Invitations" link prominent
- ✅ "View Event Details" link also available
- ✅ No errors during navigation

---

## Test Scenario 3: Submit RSVP and Return to Dashboard

**Steps**:
1. From dashboard, click "RSVP Now" on an event
2. Fill out RSVP form (select responses for all members)
3. Submit RSVP
4. Verify success message
5. Click "← My Invitations" link
6. Verify dashboard shows updated RSVP status

**Expected Results**:
- ✅ RSVP submission successful
- ✅ Dashboard shows updated status
- ✅ Status badges color-coded correctly:
  - Green = Attending
  - Red = Not Attending
  - Yellow = Maybe
  - Gray = No Response
- ✅ Summary counts accurate
- ✅ Button changes from "RSVP Now" to "Update RSVP"

---

## Test Scenario 4: Update Existing RSVP

**Steps**:
1. From dashboard, find event with existing RSVP
2. Click "Update RSVP" button
3. Change one or more responses
4. Submit
5. Return to dashboard
6. Verify updated status

**Expected Results**:
- ✅ Can update existing RSVP
- ✅ Dashboard reflects changes
- ✅ Confirmation email sent (check inbox)

---

## Test Scenario 5: Access Dashboard from Confirmation Email

**Steps**:
1. Submit an RSVP (if not already done)
2. Check email for RSVP confirmation
3. Look for "View My Invitations" button
4. Click the button
5. Verify dashboard loads

**Expected Results**:
- ✅ Confirmation email contains dashboard link
- ✅ Dashboard loads correctly
- ✅ Shows all invitations (not just the one RSVP'd to)

---

## Test Scenario 6: Multiple Events on Dashboard

**Setup**:
- Household invited to 3+ events
- Mix of RSVP statuses (some responded, some not)

**Steps**:
1. Access dashboard
2. Verify all events displayed
3. Check RSVP status for each event
4. Verify events sorted by date (upcoming first)

**Expected Results**:
- ✅ All invited events shown
- ✅ Only published events shown (drafts hidden)
- ✅ Events sorted chronologically
- ✅ Each event card shows:
  - Title, date, venue
  - RSVP deadline (if set)
  - Status for each household member
  - Summary counts
  - Action buttons

---

## Test Scenario 7: Household with No Invitations

**Setup**:
- Create a new household
- Don't invite to any events
- Get a token somehow (or use existing token and delete invitations)

**Steps**:
1. Access dashboard with token
2. Verify empty state displayed

**Expected Results**:
- ✅ Friendly empty state message
- ✅ Icon displayed
- ✅ Text: "No Invitations Yet"
- ✅ No errors

---

## Test Scenario 8: Mobile Responsiveness

**Steps**:
1. Open dashboard on mobile device or browser dev tools
2. Verify layout adapts
3. Test navigation
4. Test RSVP flow

**Expected Results**:
- ✅ Dashboard readable on mobile
- ✅ Event cards stack vertically
- ✅ Buttons easy to tap
- ✅ Text readable without zooming
- ✅ Navigation works smoothly

---

## Test Scenario 9: Bookmark and Return

**Steps**:
1. Access dashboard
2. Bookmark the page (Cmd/Ctrl + D)
3. Close browser
4. Open bookmark
5. Verify dashboard loads

**Expected Results**:
- ✅ Bookmark works
- ✅ Dashboard loads from bookmark
- ✅ Token still valid
- ✅ All data displayed correctly

---

## Test Scenario 10: Event Details Navigation

**Steps**:
1. From dashboard, click "View Event Details" link
2. Verify event detail page loads
3. Navigate back to dashboard (browser back button or link)

**Expected Results**:
- ✅ Event detail page loads
- ✅ Can navigate back to dashboard
- ✅ Dashboard state preserved

---

## Edge Cases to Test

### Edge Case 1: Token Expiration
```
1. Use an old/expired token
2. Try to access dashboard
Expected: Redirect with error message
```

### Edge Case 2: Invalid Token
```
1. Modify token in URL
2. Try to access dashboard
Expected: Redirect with error message
```

### Edge Case 3: Household with Only Children
```
1. Create household with only children (no adults)
2. Invite to event
3. Access dashboard
Expected: Shows children with "Child" badges
```

### Edge Case 4: Event with No Venue
```
1. Create event without venue address
2. Invite household
3. Access dashboard
Expected: Event displays without venue line
```

### Edge Case 5: Event with No RSVP Deadline
```
1. Create event without RSVP deadline
2. Invite household
3. Access dashboard
Expected: Event displays without deadline line
```

### Edge Case 6: Past Event
```
1. Create event with past date
2. Invite household
3. Access dashboard
Expected: Event still shows (or decide if should be hidden)
```

---

## Database Verification

### Check Dashboard Data
```python
# In Flask shell: flask shell
from app.models import EventInvitation, Household, RSVP

# Get household
household = Household.query.first()

# Get invitations
invitations = EventInvitation.query.filter_by(household_id=household.id).all()

# Check each invitation
for inv in invitations:
    print(f"Event: {inv.event.title}")
    print(f"  Status: {inv.event.status}")
    print(f"  Date: {inv.event.event_date}")
    
    # Get RSVPs
    rsvps = RSVP.query.filter_by(
        event_id=inv.event_id,
        household_id=household.id
    ).all()
    
    for rsvp in rsvps:
        print(f"  {rsvp.person.full_name}: {rsvp.status}")
```

---

## Common Issues & Troubleshooting

### Issue: Dashboard shows no events
**Possible Causes**:
- No invitations created
- All events are drafts (not published)
- Wrong household token

**Fix**: Verify invitations exist and events are published

### Issue: RSVP status not updating on dashboard
**Possible Causes**:
- Browser cache
- RSVP submission failed

**Fix**: Hard refresh (Cmd/Ctrl + Shift + R), check database

### Issue: "View All My Invitations" button not in email
**Possible Causes**:
- Old email template cached
- Email sent before implementation

**Fix**: Send new invitation, check template file

### Issue: Token expired error
**Possible Causes**:
- Token older than TOKEN_EXPIRATION_DAYS config

**Fix**: Generate new invitation, update config if needed

---

## Success Criteria

✅ **Dashboard accessible from invitation emails**  
✅ **Dashboard accessible from confirmation emails**  
✅ **Dashboard accessible from RSVP forms**  
✅ **Shows all household invitations**  
✅ **Shows current RSVP status accurately**  
✅ **Navigation works smoothly**  
✅ **Mobile responsive**  
✅ **Token authentication works**  
✅ **Empty state handles gracefully**  
✅ **Updates reflect immediately**

---

## Performance Testing

### Load Test
```bash
# Test dashboard with many invitations
# Create household with 10+ event invitations
# Access dashboard and verify performance
```

**Expected**:
- Page loads in < 2 seconds
- No database N+1 queries
- Smooth scrolling

---

## Next Steps After Testing

1. ✅ Fix any bugs discovered
2. ✅ Optimize database queries if needed
3. ✅ Add automated tests (optional)
4. ✅ Deploy to staging
5. ✅ User acceptance testing
6. ✅ Deploy to production


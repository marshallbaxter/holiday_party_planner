# Organizer Dashboard Testing Guide

## Quick Start Testing

### Prerequisites
1. Flask app running: `flask run`
2. At least 2 organizer accounts created
3. Each organizer has a household
4. Multiple events created by different organizers

---

## Test Scenario 1: Organizer with Both Hosting and Guest Roles

**Setup**:
1. Create Organizer A with household
2. Create Organizer B with household
3. Organizer A creates Event 1 (published)
4. Organizer B creates Event 2 (published)
5. Organizer B invites Organizer A's household to Event 2

**Steps**:
1. Log in as Organizer A
2. Navigate to dashboard (`/organizer/`)
3. Verify "Events I'm Hosting" section shows Event 1
4. Verify "Events I'm Invited To" section shows Event 2
5. Verify Event 2 shows RSVP status for household members
6. Click "RSVP Now" on Event 2
7. Fill out RSVP and submit
8. Return to dashboard
9. Verify RSVP status updated

**Expected Results**:
- ✅ Two sections displayed
- ✅ Event 1 in hosting section
- ✅ Event 2 in invited section
- ✅ RSVP status visible
- ✅ Can RSVP from dashboard
- ✅ Status updates after RSVP

---

## Test Scenario 2: Organizer Hosting Only (No Invitations)

**Setup**:
1. Create Organizer C with household
2. Organizer C creates 2 events
3. Don't invite Organizer C to any other events

**Steps**:
1. Log in as Organizer C
2. View dashboard
3. Verify "Events I'm Hosting" shows 2 events
4. Verify "Events I'm Invited To" shows empty state

**Expected Results**:
- ✅ Hosting section shows events
- ✅ Invited section shows "You haven't been invited to any events as a guest"
- ✅ No errors
- ✅ Can still manage hosted events

---

## Test Scenario 3: Organizer Invited Only (Not Hosting)

**Setup**:
1. Create Organizer D with household
2. Organizer D doesn't create any events
3. Another organizer invites Organizer D's household to 2 events

**Steps**:
1. Log in as Organizer D
2. View dashboard
3. Verify "Events I'm Hosting" shows empty state
4. Verify "Events I'm Invited To" shows 2 events

**Expected Results**:
- ✅ Hosting section shows "You haven't created any events yet"
- ✅ Invited section shows 2 events
- ✅ Can RSVP to invited events
- ✅ Can view event details

---

## Test Scenario 4: Organizer Without Household

**Setup**:
1. Create Organizer E without household
2. Organizer E creates 1 event

**Steps**:
1. Log in as Organizer E
2. View dashboard
3. Verify "Events I'm Hosting" section displays
4. Verify "Events I'm Invited To" section NOT displayed

**Expected Results**:
- ✅ Hosting section works normally
- ✅ Invited section not shown (no household)
- ✅ No errors or crashes
- ✅ Can still manage events

---

## Test Scenario 5: Draft Events Not Shown

**Setup**:
1. Create Organizer F with household
2. Another organizer creates draft event
3. Invites Organizer F's household to draft event

**Steps**:
1. Log in as Organizer F
2. View dashboard
3. Verify draft event NOT shown in "Events I'm Invited To"

**Expected Results**:
- ✅ Only published events shown
- ✅ Draft events hidden
- ✅ No errors

---

## Test Scenario 6: Organizer Hosting and Invited to Same Event

**Setup**:
1. Create Organizer G with household
2. Organizer G creates Event X
3. Another admin invites Organizer G's household to Event X

**Steps**:
1. Log in as Organizer G
2. View dashboard
3. Verify Event X only appears in "Events I'm Hosting"
4. Verify Event X NOT duplicated in "Events I'm Invited To"

**Expected Results**:
- ✅ Event appears once (in hosting section)
- ✅ No duplication
- ✅ Deduplication logic works

---

## Test Scenario 7: Multiple Household Members

**Setup**:
1. Create household with 3 members (2 adults, 1 child)
2. One adult is Organizer H
3. Invite household to event
4. Submit mixed RSVPs (1 attending, 1 not attending, 1 maybe)

**Steps**:
1. Log in as Organizer H
2. View dashboard
3. Verify all 3 household members shown with status
4. Verify color-coded badges correct
5. Verify summary counts accurate

**Expected Results**:
- ✅ All household members displayed
- ✅ Individual status badges shown
- ✅ Colors correct (green/red/yellow/gray)
- ✅ Summary: "1 attending, 1 not attending, 1 maybe, 0 no response"

---

## Test Scenario 8: Update RSVP from Dashboard

**Setup**:
1. Organizer already RSVP'd to event
2. Status shows "Attending"

**Steps**:
1. Log in as organizer
2. View dashboard
3. Verify button says "Update RSVP" (not "RSVP Now")
4. Click "Update RSVP"
5. Change status to "Not Attending"
6. Submit
7. Return to dashboard
8. Verify status updated

**Expected Results**:
- ✅ Button text changes based on status
- ✅ Can update existing RSVP
- ✅ Dashboard reflects changes
- ✅ Confirmation email sent

---

## Test Scenario 9: View Event Details

**Setup**:
1. Organizer invited to event

**Steps**:
1. From dashboard, click "View Details" button
2. Verify public event detail page loads
3. Navigate back to dashboard (browser back)
4. Verify dashboard still works

**Expected Results**:
- ✅ Event detail page loads
- ✅ Shows public event information
- ✅ Can navigate back
- ✅ No session issues

---

## Test Scenario 10: Mobile Responsiveness

**Steps**:
1. Open dashboard on mobile device or browser dev tools
2. Verify both sections display
3. Verify event cards stack vertically
4. Verify buttons accessible
5. Test RSVP flow on mobile

**Expected Results**:
- ✅ Layout adapts to mobile
- ✅ Text readable
- ✅ Buttons easy to tap
- ✅ No horizontal scrolling
- ✅ All functionality works

---

## Edge Cases

### Edge Case 1: Organizer with 10+ Invited Events
```
1. Invite organizer to many events
2. View dashboard
Expected: All events display, scrollable
```

### Edge Case 2: Event with No Venue
```
1. Create event without venue address
2. Invite organizer
Expected: Event displays without venue line
```

### Edge Case 3: Past Event
```
1. Create event with past date
2. Invite organizer
Expected: Event still shows (or decide if should be hidden)
```

### Edge Case 4: Event with Long Title
```
1. Create event with very long title
2. Invite organizer
Expected: Title wraps or truncates gracefully
```

---

## Database Verification

### Check Dashboard Data
```python
# In Flask shell: flask shell
from app.models import Person, EventAdmin, EventInvitation, RSVP

# Get organizer
organizer = Person.query.filter_by(email='organizer@example.com').first()

# Check hosting events
admin_records = EventAdmin.query.filter_by(
    person_id=organizer.id, removed_at=None
).all()
print(f"Hosting {len(admin_records)} events")

# Check household
household = organizer.primary_household
print(f"Household: {household.name if household else 'None'}")

# Check invitations
if household:
    invitations = EventInvitation.query.filter_by(
        household_id=household.id
    ).all()
    print(f"Invited to {len(invitations)} events")
    
    for inv in invitations:
        print(f"  - {inv.event.title} ({inv.event.status})")
        rsvps = RSVP.query.filter_by(
            event_id=inv.event_id,
            household_id=household.id
        ).all()
        for rsvp in rsvps:
            print(f"    {rsvp.person.full_name}: {rsvp.status}")
```

---

## Common Issues & Troubleshooting

### Issue: "Events I'm Invited To" not showing
**Possible Causes**:
- Organizer has no household
- No invitations exist
- All invited events are drafts

**Fix**: Verify household exists, check invitations, publish events

### Issue: Duplicate events showing
**Possible Causes**:
- Deduplication logic not working
- Organizer is both host and guest

**Fix**: Check `hosting_event_ids` filtering logic

### Issue: RSVP status not displaying
**Possible Causes**:
- RSVPs not created
- Query error

**Fix**: Check RSVP records in database, verify invitation exists

### Issue: Button says "RSVP Now" but already responded
**Possible Causes**:
- Summary calculation incorrect
- RSVP status not "no_response"

**Fix**: Check summary logic, verify RSVP statuses

---

## Performance Testing

### Load Test
```bash
# Create organizer with many invitations
# 1. Create 20 events
# 2. Invite organizer to all 20
# 3. Load dashboard
# 4. Measure page load time
```

**Expected**:
- Page loads in < 2 seconds
- No N+1 query issues
- Smooth scrolling

---

## Success Criteria

✅ **Both sections display correctly**  
✅ **Hosting events show in top section**  
✅ **Invited events show in bottom section**  
✅ **RSVP status accurate**  
✅ **Color-coded badges correct**  
✅ **Action buttons work**  
✅ **No duplicates**  
✅ **Draft events hidden**  
✅ **Mobile responsive**  
✅ **No errors or crashes**

---

## Next Steps After Testing

1. ✅ Fix any bugs discovered
2. ✅ Optimize queries if needed
3. ✅ Add pagination if many events
4. ✅ Consider adding filters/sorting
5. ✅ Deploy to staging
6. ✅ User acceptance testing
7. ✅ Deploy to production


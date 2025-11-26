# RSVP Testing Guide

## Quick Start Testing

### Prerequisites
1. Flask app running: `flask run`
2. Database initialized: `flask db upgrade`
3. At least one event created with status "published"
4. At least one household invited to the event

### Test Scenario 1: Basic RSVP Submission

**Setup**:
```bash
# Start the Flask development server
flask run
```

**Steps**:
1. Navigate to organizer dashboard
2. Create a test event (or use existing)
3. Invite a household to the event
4. Copy the RSVP link from the invitation (or check email)
5. Open RSVP link in browser: `/event/{uuid}/rsvp?token={token}`
6. Verify form displays:
   - Event details (title, date, venue)
   - All household members
   - Radio buttons for each person
   - Notes textarea for each person
7. Select RSVP status for each household member
8. Add optional notes
9. Click "Submit RSVP"
10. Verify success message appears
11. Verify form shows updated status
12. Check email for confirmation (if Brevo configured)

**Expected Results**:
- ✅ Form displays correctly
- ✅ Success message: "Thank you! Your RSVP has been recorded for X person(s)..."
- ✅ Form shows updated RSVP status
- ✅ Confirmation email sent (if email configured)
- ✅ Database updated (check via organizer dashboard)

---

### Test Scenario 2: Update Existing RSVP

**Steps**:
1. Complete Test Scenario 1 first
2. Return to RSVP form (same link)
3. Verify current status is pre-selected
4. Change one or more responses
5. Update notes
6. Click "Submit RSVP"
7. Verify success message
8. Verify updated status displayed

**Expected Results**:
- ✅ Previous responses pre-selected
- ✅ Can change responses
- ✅ Success message on update
- ✅ New confirmation email sent

---

### Test Scenario 3: Multi-Person Household

**Setup**:
- Create household with 2+ members (adults and children)
- Invite household to event

**Steps**:
1. Open RSVP link
2. Verify all household members listed
3. Verify children have "Child" badge
4. Select different responses for different members:
   - Adult 1: Attending
   - Adult 2: Not Attending
   - Child 1: Attending
5. Add notes for specific members
6. Submit RSVP
7. Verify all responses recorded

**Expected Results**:
- ✅ All household members shown
- ✅ Children identified with badge
- ✅ Can set different responses per person
- ✅ All responses saved correctly

---

### Test Scenario 4: Security Testing

**Test 4.1: Invalid Token**
```
URL: /event/{uuid}/rsvp?token=invalid_token
Expected: Redirect or error message
```

**Test 4.2: Missing Token**
```
URL: /event/{uuid}/rsvp
Expected: Redirect or error message
```

**Test 4.3: CSRF Protection**
```
1. Open RSVP form
2. Remove csrf_token from form (browser dev tools)
3. Submit form
Expected: CSRF validation error
```

**Test 4.4: Person ID Tampering**
```
1. Open RSVP form
2. Modify person_id in form field name (browser dev tools)
3. Submit form
Expected: "Invalid person ID" error message
```

---

### Test Scenario 5: Edge Cases

**Test 5.1: No Response Selected**
```
1. Open RSVP form
2. Don't select any radio buttons
3. Submit form
Expected: Warning message about no responses
```

**Test 5.2: Empty Notes**
```
1. Open RSVP form
2. Select responses but leave notes empty
3. Submit form
Expected: Success (notes are optional)
```

**Test 5.3: Long Notes**
```
1. Open RSVP form
2. Enter very long text in notes field (500+ characters)
3. Submit form
Expected: Success (notes field is TEXT type, no length limit)
```

**Test 5.4: Special Characters in Notes**
```
1. Enter notes with special characters: <script>, ', ", &
2. Submit form
3. Verify notes saved correctly without XSS issues
Expected: Characters escaped/sanitized
```

---

### Test Scenario 6: Mobile Responsiveness

**Steps**:
1. Open RSVP form on mobile device or browser dev tools mobile view
2. Verify layout adapts to small screen
3. Verify radio buttons are easy to tap
4. Verify form is scrollable
5. Submit form on mobile

**Expected Results**:
- ✅ Form displays correctly on mobile
- ✅ All elements accessible
- ✅ Submit button visible and functional

---

## Database Verification

### Check RSVP Records
```python
# In Flask shell: flask shell
from app.models import RSVP, Event, Household

# Get event
event = Event.query.first()

# Get RSVPs for event
rsvps = RSVP.query.filter_by(event_id=event.id).all()

# Check RSVP details
for rsvp in rsvps:
    print(f"{rsvp.person.full_name}: {rsvp.status} - {rsvp.notes}")
    print(f"  Responded at: {rsvp.responded_at}")
    print(f"  Updated by host: {rsvp.updated_by_host}")
```

### Check Notification Logs
```python
from app.models import Notification

# Get notifications for event
notifications = Notification.query.filter_by(event_id=event.id).all()

for notif in notifications:
    print(f"{notif.notification_type} to {notif.person.email}: {notif.status}")
```

---

## Common Issues & Troubleshooting

### Issue: "RSVP submission not yet implemented"
**Cause**: Old code still in place  
**Fix**: Verify `app/routes/public.py` has been updated with new implementation

### Issue: Template not found error
**Cause**: `rsvp_form.html` not created  
**Fix**: Verify file exists at `app/templates/public/rsvp_form.html`

### Issue: CSRF token error
**Cause**: CSRF protection not configured  
**Fix**: Verify `csrf.init_app(app)` in `app/__init__.py`

### Issue: No confirmation email received
**Cause**: Brevo API not configured or email address missing  
**Fix**: 
- Check `BREVO_API_KEY` in config
- Verify person has email address
- Check notification logs in database

### Issue: "Invalid person ID" error
**Cause**: Person doesn't belong to household  
**Fix**: Verify household membership in database

---

## Performance Testing

### Load Test Scenario
```bash
# Using Apache Bench (ab)
ab -n 100 -c 10 -p rsvp_data.txt -T "application/x-www-form-urlencoded" \
   "http://localhost:5000/event/{uuid}/rsvp/submit?token={token}"
```

**Expected**:
- All requests succeed
- No database deadlocks
- Emails queued properly

---

## Automated Testing

### Run Existing Tests
```bash
pytest tests/test_models.py -v
```

### Create Integration Test (Future)
```python
# tests/test_rsvp_routes.py
def test_rsvp_submission(client, sample_event, sample_household):
    # Get invitation token
    invitation = sample_event.invitations.first()
    token = invitation.invitation_token
    
    # Submit RSVP
    response = client.post(
        f'/event/{sample_event.uuid}/rsvp/submit?token={token}',
        data={
            'csrf_token': 'test_token',
            'rsvp_1': 'attending',
            'notes_1': 'Looking forward to it!'
        }
    )
    
    assert response.status_code == 302  # Redirect
    # Add more assertions...
```

---

## Success Criteria

✅ **All test scenarios pass**  
✅ **No errors in Flask logs**  
✅ **Database records updated correctly**  
✅ **Confirmation emails sent**  
✅ **Form is user-friendly and intuitive**  
✅ **Mobile responsive**  
✅ **Security validations work**  
✅ **Error handling graceful**

---

## Next Steps After Testing

1. Fix any bugs discovered
2. Add automated integration tests
3. Implement RSVP deadline validation (future)
4. Implement RSVP reminder emails (future)
5. Deploy to production


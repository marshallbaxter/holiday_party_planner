# RSVP Implementation - Code Reference

## Quick Reference for Key Code Sections

### 1. Form Template Structure

**File**: `app/templates/public/rsvp_form.html`

**Key Sections**:

```html
<!-- Event Details Display -->
<h1>RSVP for {{ event.title }}</h1>
<span>{{ event.event_date|datetime('%A, %B %d, %Y at %I:%M %p') }}</span>

<!-- Form with CSRF Token -->
<form method="POST" action="{{ url_for('public.submit_rsvp', event_uuid=event.uuid, token=request.args.get('token')) }}">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    
    <!-- Loop through household members -->
    {% for rsvp in rsvps %}
        <!-- Radio buttons for each person -->
        <input type="radio" name="rsvp_{{ rsvp.person_id }}" value="attending">
        <input type="radio" name="rsvp_{{ rsvp.person_id }}" value="not_attending">
        <input type="radio" name="rsvp_{{ rsvp.person_id }}" value="maybe">
        <input type="radio" name="rsvp_{{ rsvp.person_id }}" value="no_response">
        
        <!-- Optional notes -->
        <textarea name="notes_{{ rsvp.person_id }}"></textarea>
    {% endfor %}
    
    <button type="submit">Submit RSVP</button>
</form>
```

---

### 2. Route Implementation

**File**: `app/routes/public.py`

**Import Statement**:
```python
from app.services.rsvp_service import RSVPService
```

**Submit Route Logic**:
```python
@bp.route("/event/<uuid:event_uuid>/rsvp/submit", methods=["POST"])
@valid_rsvp_token_required
def submit_rsvp(event_uuid):
    event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
    household = request.household  # Set by decorator
    
    try:
        # Parse form data
        rsvp_data = {}
        valid_person_ids = {member.id for member in household.active_members}
        
        for key, value in request.form.items():
            if key.startswith("rsvp_"):
                person_id = int(key.split("_")[1])
                
                # Security check
                if person_id not in valid_person_ids:
                    flash("Invalid person ID in form submission.", "error")
                    return redirect(...)
                
                # Validate status
                status = value.strip()
                if status not in ["attending", "not_attending", "maybe", "no_response"]:
                    flash(f"Invalid RSVP status: {status}", "error")
                    return redirect(...)
                
                # Get notes
                notes = request.form.get(f"notes_{person_id}", "").strip() or None
                
                # Build data dictionary
                rsvp_data[person_id] = {"status": status, "notes": notes}
        
        # Update RSVPs
        updated_rsvps = RSVPService.update_household_rsvps(event, household, rsvp_data)
        
        if updated_rsvps:
            flash(f"Thank you! Your RSVP has been recorded for {len(updated_rsvps)} person(s).", "success")
    
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while submitting your RSVP.", "error")
    
    return redirect(url_for("public.rsvp_form", event_uuid=event_uuid, token=request.args.get("token")))
```

---

### 3. Service Layer (Already Exists)

**File**: `app/services/rsvp_service.py`

**Method Used**:
```python
@staticmethod
def update_household_rsvps(event, household, rsvp_data):
    """Update RSVPs for all members of a household.
    
    Args:
        event: Event object
        household: Household object
        rsvp_data: Dictionary mapping person_id to status and notes
                  Example: {1: {'status': 'attending', 'notes': 'Excited!'}}
    
    Returns:
        List of updated RSVP objects
    """
    updated_rsvps = []
    
    for person_id, data in rsvp_data.items():
        rsvp = RSVP.query.filter_by(
            event_id=event.id, person_id=person_id, household_id=household.id
        ).first()
        
        if rsvp:
            status = data.get("status", "no_response")
            notes = data.get("notes")
            rsvp.update_status(status, notes)
            updated_rsvps.append(rsvp)
    
    db.session.commit()
    
    # Send confirmation email
    if updated_rsvps:
        NotificationService.send_household_rsvp_confirmation(event, household, updated_rsvps)
    
    return updated_rsvps
```

---

### 4. Form Data Structure

**Form Field Naming Convention**:
```
rsvp_{person_id}     -> RSVP status (radio button value)
notes_{person_id}    -> Optional notes (textarea value)
csrf_token           -> CSRF protection token
```

**Example Form Data**:
```python
{
    'csrf_token': 'IjY4ZTk5...',
    'rsvp_1': 'attending',
    'notes_1': 'Looking forward to it!',
    'rsvp_2': 'not_attending',
    'notes_2': 'Sorry, can\'t make it',
    'rsvp_3': 'attending',
    'notes_3': ''
}
```

**Parsed into rsvp_data**:
```python
{
    1: {'status': 'attending', 'notes': 'Looking forward to it!'},
    2: {'status': 'not_attending', 'notes': 'Sorry, can\'t make it'},
    3: {'status': 'attending', 'notes': None}
}
```

---

### 5. Database Schema

**RSVP Model** (`app/models/rsvp.py`):
```python
class RSVP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"))
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"))
    household_id = db.Column(db.Integer, db.ForeignKey("households.id"))
    status = db.Column(db.String(20), default="no_response")
    responded_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_by_person_id = db.Column(db.Integer, db.ForeignKey("persons.id"))
    updated_by_host = db.Column(db.Boolean, default=False)
```

**Valid Status Values**:
- `attending`
- `not_attending`
- `maybe`
- `no_response`

---

### 6. URL Routes

**RSVP Form (GET)**:
```
/event/<uuid>/rsvp?token=<token>
```

**RSVP Submit (POST)**:
```
/event/<uuid>/rsvp/submit?token=<token>
```

**Example**:
```
GET  /event/a1b2c3d4-e5f6-7890-abcd-ef1234567890/rsvp?token=eyJhbGc...
POST /event/a1b2c3d4-e5f6-7890-abcd-ef1234567890/rsvp/submit?token=eyJhbGc...
```

---

### 7. Flash Messages

**Success**:
```python
flash(f"Thank you! Your RSVP has been recorded for {len(updated_rsvps)} person(s). A confirmation email has been sent.", "success")
```

**Error**:
```python
flash("An error occurred while submitting your RSVP. Please try again or contact the organizer.", "error")
```

**Warning**:
```python
flash("No RSVP responses were submitted. Please select a response for at least one person.", "warning")
```

---

### 8. Email Confirmation

**Template**: `app/templates/emails/household_rsvp_confirmation.html`

**Sent Automatically** by `RSVPService.update_household_rsvps()` via:
```python
NotificationService.send_household_rsvp_confirmation(event, household, updated_rsvps)
```

**Email Content**:
- Household name
- List of all household members with their responses
- Event details (date, venue)
- Link to update RSVP

---

### 9. Security Validations

**Token Validation** (Decorator):
```python
@valid_rsvp_token_required
```

**Person ID Validation**:
```python
valid_person_ids = {member.id for member in household.active_members}
if person_id not in valid_person_ids:
    flash("Invalid person ID in form submission.", "error")
    return redirect(...)
```

**Status Validation**:
```python
valid_statuses = ["attending", "not_attending", "maybe", "no_response"]
if status not in valid_statuses:
    flash(f"Invalid RSVP status: {status}", "error")
    return redirect(...)
```

**CSRF Protection**:
```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

---

## Testing Snippets

### Flask Shell Testing
```python
flask shell

# Get event and household
from app.models import Event, Household, RSVP
event = Event.query.first()
household = Household.query.first()

# Check RSVPs
rsvps = RSVP.query.filter_by(event_id=event.id, household_id=household.id).all()
for rsvp in rsvps:
    print(f"{rsvp.person.full_name}: {rsvp.status}")
```

### cURL Testing
```bash
curl -X POST "http://localhost:5000/event/{uuid}/rsvp/submit?token={token}" \
  -d "csrf_token={token}&rsvp_1=attending&notes_1=Excited!"
```

---

## File Locations

```
app/
├── routes/
│   └── public.py                    # RSVP routes (MODIFIED)
├── templates/
│   └── public/
│       └── rsvp_form.html          # RSVP form (NEW)
├── services/
│   └── rsvp_service.py             # Service layer (EXISTING)
└── models/
    └── rsvp.py                      # RSVP model (EXISTING)
```

---

## Dependencies

- Flask
- Flask-WTF (CSRF protection)
- SQLAlchemy (Database ORM)
- Jinja2 (Template engine)
- Tailwind CSS (Styling)


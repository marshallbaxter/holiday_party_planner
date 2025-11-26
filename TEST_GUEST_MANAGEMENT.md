# Testing Guest Management - Quick Guide

## 🚀 Quick Start

```bash
# Restart Flask
flask run
```

Then visit: http://localhost:5000/organizer/login

---

## 📋 Test Scenario: Create Your First Household

### **Step 1: Log In**

- Email: `john.smith@example.com`
- Password: `password123`

### **Step 2: Access Guest Management**

1. From dashboard, click **"👥 Manage Guests"**
2. You should see the guest directory (empty at first)

### **Step 3: Create a Household**

1. Click **"+ New Household"**
2. Enter:
   - Name: `The Johnson Family`
   - Address: `456 Oak Street\nSpringfield, IL 62701`
3. Click **"Create Household"**
4. ✅ You should see the household detail page

### **Step 4: Add First Person (Adult)**

1. Click **"+ Add Person"**
2. Enter:
   - First Name: `Bob`
   - Last Name: `Johnson`
   - Email: `bob@example.com`
   - Phone: `(555) 123-4567`
   - Role: `Adult`
   - ✅ Check **"Primary Contact for Household"**
3. Click **"Add Person"**
4. ✅ You should see Bob added to the household

### **Step 5: Add Second Person (Spouse)**

1. Click **"+ Add Person"** again
2. Enter:
   - First Name: `Alice`
   - Last Name: `Johnson`
   - Email: `alice@example.com`
   - Role: `Adult`
   - ⬜ Leave "Primary Contact" unchecked
3. Click **"Add Person"**
4. ✅ You should see both Bob and Alice

### **Step 6: Add Children**

1. Click **"+ Add Person"**
2. Enter:
   - First Name: `Emma`
   - Last Name: `Johnson`
   - Role: `Child`
3. Click **"Add Person"**

Repeat for another child:
   - First Name: `Liam`
   - Last Name: `Johnson`
   - Role: `Child`

4. ✅ You should see 4 family members total

### **Step 7: View Guest Directory**

1. Click **"← Back to Guests"**
2. ✅ You should see:
   - Total Households: 1
   - Total People: 4
   - Adults / Children: 2 / 2
   - The Johnson Family listed with all members

---

## 🧪 Additional Tests

### **Test Editing**

1. **Edit Household**:
   - Click on "The Johnson Family"
   - Click "Edit Household"
   - Change name to "Johnson Household"
   - Save
   - ✅ Name should update

2. **Edit Person**:
   - Click "Edit" next to Bob
   - Change email to `bob.johnson@example.com`
   - Save
   - ✅ Email should update

### **Test Primary Contact**

1. Click "Edit" next to Alice
2. Check "Primary Contact for Household"
3. Save
4. ✅ Both Bob and Alice should show as primary contacts

### **Test Removing Person**

1. Click "Remove" next to Liam
2. Confirm the dialog
3. ✅ Liam should be removed from the list
4. ✅ Statistics should update (3 people now)

### **Test Creating Multiple Households**

Create a second household:
1. Go back to guest directory
2. Click "+ New Household"
3. Create "The Williams Family"
4. Add Mary Williams (adult, primary contact)
5. ✅ Guest directory should show 2 households

---

## ✅ Expected Results

### **Guest Directory Should Show**:

```
┌─────────────────────────────────────────┐
│  Total Households: 2                    │
│  Total People: 4                        │
│  Adults / Children: 3 / 1               │
└─────────────────────────────────────────┘

The Johnson Family
📍 456 Oak Street, Springfield, IL 62701
👥 3 member(s)
📧 Bob Johnson (bob.johnson@example.com)
[Bob Johnson] [Alice Johnson] [Emma Johnson (child)]

The Williams Family
👥 1 member(s)
📧 Mary Williams
[Mary Williams]
```

---

## 🐛 Common Issues

### **Issue: "No module named 'app.routes.guests'"**

**Solution**: Make sure you registered the blueprint in `app/__init__.py`:
```python
from app.routes import organizer, public, api, guests
app.register_blueprint(guests.bp)
```

### **Issue: "Template not found"**

**Solution**: Make sure templates are in `app/templates/guests/`:
- `index.html`
- `household_detail.html`
- `household_form.html`
- `person_form.html`

### **Issue: Form validation errors**

**Solution**: Check that all required fields are filled:
- Household: name (required)
- Person: first_name, last_name, role (required)

---

## 📊 Test Data to Create

For comprehensive testing, create:

### **Household 1: The Smith Family**
- John Smith (adult, primary contact, email)
- Jane Smith (adult, email)
- Tommy Smith (child)

### **Household 2: The Johnson Family**
- Bob Johnson (adult, primary contact, email)
- Alice Johnson (adult, email)
- Emma Johnson (child)
- Liam Johnson (child)

### **Household 3: The Williams Family**
- Mary Williams (adult, primary contact, email)

### **Household 4: The Brown Family**
- David Brown (adult, primary contact, email)
- Sarah Brown (adult, email)
- Olivia Brown (child)

**Expected Totals**:
- Households: 4
- People: 11
- Adults: 7
- Children: 4

---

## 🎯 Next: Test Event Integration

Once you have households created, you can test inviting them to events (Phase 2):

1. Go to an event dashboard
2. Click "Manage Guests"
3. Select households to invite
4. Send invitations

**Note**: Phase 2 (event-specific guest assignment) is not yet implemented. This will be the next step!

---

## ✅ Success Criteria

You've successfully tested guest management if:

- ✅ Can create households
- ✅ Can add people to households
- ✅ Can edit households and people
- ✅ Can mark primary contacts
- ✅ Can remove people (soft delete)
- ✅ Can archive households
- ✅ Statistics update correctly
- ✅ Navigation works smoothly
- ✅ Forms validate properly
- ✅ Success/error messages display

---

**Ready to test!** Start with creating "The Johnson Family" and work through the steps above. 🚀


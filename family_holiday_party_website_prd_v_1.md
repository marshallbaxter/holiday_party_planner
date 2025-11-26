# Family Holiday Party Website — Product Requirements Document (PRD)

_Last updated: 2025-11-09 (Revised per feature scope decisions)_

## 1) Purpose & Vision
Create a lightweight, privacy-respecting web app to plan and run family holiday events. Core goals: send invitations, collect/manage RSVPs, coordinate potluck items, and automate yearly events so recurring hosts can easily reuse guest lists and templates.

## 2) Scope (MVP vs. Nice-to-Have)
**MVP**
- Event creation (each event is standalone; no seasonal grouping)
- Invitations via email/SMS
- RSVP management (household-aware)
- Potluck item catalog + sign-ups with dietary tags and notes
- Guest directory (import/export)
- Unlisted event links (no index) + organizer login 
- Guest list copy from prior events (with deduping)
- Automatic creation of recurring annual events with draft mode for organizer edits before publishing
- Basic reminders & notifications

**Future/Nice-to-Have**
- Gift exchange/Secret Santa
- Photo gallery (post-event)
- Budget tracking / shared expenses
- PIN/password protection, and eventually full login model
- Host-configurable visibility of RSVP/food info

## 3) Roles & Relationships
- **Organizer**: creates events, manages invites, edits event details, and can hand off or share admin rights.
- **Co-Organizer/Admin**: full access to assist with event management.
- **Household Member (Adult)**: can RSVP and edit household information for themselves and any dependents.
- **Household Member (Child)**: represented without required contact details; visible under adult guardians.
- **Guest**: receives invites and participates in potluck sign-ups.

### Relationship Model
- Each person can belong to multiple households (to handle family splits, marriages, etc.).
- Households can have multiple adults who share edit access.
- Event ownership follows the previous year’s organizer by default but can be handed off or shared.

## 4) Functional Requirements

### 4.1 Event Management
- Create standalone events with title, date/time, venue (address/map), and schedule sections.
- Display multiple upcoming events (no grouping by season).
- Default creation of new annual instances for recurring events; organizers can edit before invites go live.
- Option to hand off organizer role or add co-organizers (people or households).

### 4.2 Guest & Household Management
- Guests grouped by household; households can include multiple members.
- Members can have roles: Adult or Child.
- Guests can add new household members; organizers are notified when this happens.
- Contact details (email/phone) optional, especially for children.
- Confirmation emails sent whenever a person’s information is changed.

### 4.3 Invitations & Messaging (Email/SMS)
- Invitations via email and SMS.
- Basic transactional message templates for reminders, confirmations, and updates.
- Organizer can send custom messages and announcements.
- Message wall feature for guests to post updates or share info with everyone.
- SMS replies automatically update RSVPs for the attached guest; future expansion may include household-aware parsing.

### 4.4 RSVP Management
- Household-aware RSVP system allowing adults to RSVP for themselves and children.
- Statuses: Attending / Not Attending / Maybe / No Response.
- Confirmation emails for RSVP updates.
- RSVP updates possible via SMS or web.

### 4.5 Potluck & Food Management
- Item catalog with categories (Mains, Sides, Desserts, Drinks, Other).
- Detailed dietary tags (vegetarian, vegan, gluten-free, nut-free, dairy-free, etc.) and freeform notes.
- Guests see the full list of claimed dishes.
- Guests can specify whether the food is brought by them personally or by their household.
- Automatic reminder messages for missing dishes and approaching deadlines.

### 4.6 Copying and Year-to-Year Automation
- Organizers can copy guest lists from one or more prior events.
- System dedupes guests and households automatically.
- Annual recurring events auto-generate draft versions before invitations go out.
- Organizers can edit and confirm before making the event public.
- Default ownership and admin roles copied from prior event; can be handed off manually.

### 4.7 Notifications & Reminders
- Automatic reminders for RSVP deadlines, potluck submissions, and upcoming event notices.
- Notifications via email/SMS with opt-out support.

## 5) Privacy & Access Control
- Events accessed via unlisted links; no indexing.
- PIN/password protection planned for future versions.
- Full login model planned for long-term.
- Guests see all dishes and RSVPs at the household level; contact info is private.
- Host-configurable visibility of RSVP and potluck details to be added later.
- PII minimized; adults manage household children’s info.

## 6) Relationship & Household Management Logic
### Overview
Relationships are modeled to reflect real-world family dynamics and maintain flexibility over time. The design supports merging, splitting, and reassigning household memberships while preserving event histories.

### Core Concepts
- **Person**: The core entity representing an individual (adult or child).
- **Household**: A grouping of people that share an address, invite, or RSVP record.
- **Memberships**: A person can belong to one or more households. Each membership record stores role (adult/child), join date, and leave date (if applicable).
- **Ownership & Admin Rights**:
  - Admin privileges can be assigned to individuals or entire households.
  - Admin rights cascade to adult members of an admin household.
  - Events maintain a history of admin changes.

### Household Changes
- **Splitting a Household**: Members can be moved into a new household; prior event associations remain intact for historical accuracy.
- **Merging Households**: If two households merge (e.g., marriage), historical data is preserved, and the new household inherits memberships.
- **Child Transitions**: When a child becomes an adult or forms a new household, their membership updates automatically without data loss.
- **Notifications**: Organizers are notified when a household is split, merged, or otherwise modified.

### Privacy & Data Integrity
- Event histories retain original household and RSVP data.
- Changes to household composition after an event do not alter past event data.
- Each membership action (join, leave, change role) is logged.

## 7) Data Flow Overview (New)
### Purpose
This section outlines how information moves through the system — from event creation to invitations, responses, reminders, and potluck coordination — describing the major actors and data exchanges.

### Primary Actors
- **Organizer/Admins**: Create and manage events, send messages, and monitor responses.
- **Guests/Households**: Receive invitations, RSVP, and manage potluck participation.
- **System Services**: Handle message delivery (email/SMS), reminders, and synchronization between modules.

### Core Data Flows
1. **Event Creation → Invitation Queue**
   - Organizer creates event and sets parameters.
   - System compiles guest list (manual add, copy, import).
   - Invitations are queued for email/SMS delivery.

2. **Invitation Delivery → Guest Interaction**
   - Each guest receives a unique RSVP link or SMS code.
   - Links include household context (allowing household members to view/update shared RSVP and items).
   - Email and SMS logs record delivery and bounce status.

3. **Guest Response (RSVP)**
   - Guest submits RSVP via web or SMS.
   - System updates RSVP record, recalculates counts (attending, not attending, etc.), and sends confirmation email.
   - Organizer receives live updates on dashboard.

4. **Potluck Item Management**
   - Guests browse or claim items from event’s potluck catalog.
   - System validates availability and updates claim status.
   - Optional notifications sent when item categories are under-filled or nearing deadline.

5. **Reminders & Notifications**
   - Automated jobs run based on event timelines:
     - RSVP reminder (e.g., 7 days before deadline)
     - Potluck reminder (e.g., 3 days before event)
     - Event-day schedule notice (e.g., “Dinner starts at 5PM”)
   - Each reminder passes through notification service → delivery provider (email/SMS) → logs responses.

6. **Message Wall & Custom Updates**
   - Organizers or guests post updates to the event’s message wall.
   - Posts are visible to all invitees via the event page.
   - Optional email digest summarizing recent posts.

7. **Post-Event Archiving**
   - After event date passes, event transitions to Archived state.
   - Guests can view the archived page (read-only).
   - Organizer can trigger copy for next year or export guest list.

### Integrations
- **Email/SMS Providers:** Transactional messaging APIs (e.g., Brevo, Twilio, etc.).
- **Data Persistence:** RSVP, potluck, and message data stored with relational integrity.
- **Job Scheduler:** Background tasks for reminder cadence and event automation.
- **Audit Logging:** All outbound communications and RSVP changes logged for traceability.

### Data Flow Notes
- Personal data shared only where required for contact and event participation.
- All communication includes event and household context to minimize confusion.
- Future versions may add APIs for integrations (calendar sync, address lookup, etc.).

## 8) Non-Functional Requirements
- **Performance:** P95 page load < 2.5s.
- **Availability:** 99.9% during holiday windows.
- **Security/Privacy:** TLS, minimal PII, encrypted storage.
- **Compliance:** CAN-SPAM/TCPA consent for messaging.

## 9) Future Considerations
- Advanced SMS parsing for multi-person RSVP confirmation.
- Volunteer task tracking.
- Gift exchange module.
- Relationship graph visualization.
- Host-controlled RSVP/potluck visibility options.
- Full login model with user accounts.
- Analytics dashboard (deferred until needed).


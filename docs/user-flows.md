# CleanClaw User Flows -- Complete UX Specification

**Author:** @ux-design-expert (Sati)
**Date:** 2026-03-23
**Status:** Final
**PRD Ref:** `docs/prd/cleanclaw-prd-v3.md`
**Wireframe Ref:** `docs/ux/cleanclaw-wireframes-v3.md`
**Schema Ref:** `docs/architecture/cleanclaw-schema-v3.md`

---

## Table of Contents

1. [Owner Flows](#1-owner-flows)
2. [Cleaner Flows](#2-cleaner-flows)
3. [Homeowner Flows](#3-homeowner-flows)
4. [Cross-Role Interactions](#4-cross-role-interactions)
5. [Error States & Edge Cases](#5-error-states--edge-cases)

---

## Conventions

**Status colors used throughout:**
- Blue = Scheduled
- Green = In Progress
- Gray = Completed
- Red = Cancelled
- Orange = Rescheduled

**Persona references:**
- Maria Gutierrez = Schedule Owner (primary), 4 teams, 120 recurring clients
- Sarah Mitchell = Homeowner, biweekly cleaning
- Ana Ramirez = Cleaner on Team Beta

**Route notation:** `#/role/screen` maps to hash routes in the PWA.

---

## 1. Owner Flows

### Flow 1.1: First-Time Setup (Onboarding)

**Trigger:** Owner completes self-registration at `#/register`.
**Goal:** Go from zero to a functional schedule in under 15 minutes.
**Route:** `#/owner/onboarding` (wizard, 7 steps)

```
Sign Up --> Business Info --> Add Services --> Define Areas -->
Create First Team --> Invite Cleaners --> Review --> Dashboard
```

#### Step 1: Sign Up

**What they see:** Registration screen with Google OAuth button (prominent) and email/password form (secondary). Tagline: "Your cleaning business, finally organized."

**What they input:**
- Option A: Click "Sign up with Google" (recommended, fastest)
- Option B: Full name, email, password (min 8 chars, 1 uppercase, 1 number), confirm password

**Validation:**
- Email must be unique (real-time check on blur: "An account with this email already exists. Sign in instead?")
- Password strength meter below field with live checkmarks
- Confirm password must match (inline error on mismatch)

**What happens next:** Account created in `users` table. JWT issued. Role set to `owner` in `cleaning_user_roles`. Redirect to `#/owner/onboarding/business`.

**Error states:**
- Google OAuth fails: "Google sign-in failed. Try again or use email."
- Email already exists: Link to sign-in page
- Weak password: Inline helper highlights unmet requirements

---

#### Step 2: Business Info

**What they see:** Card titled "Tell us about your business" with form fields. Progress bar shows 1/7.

**What they input:**
| Field | Type | Required | Validation | Example |
|-------|------|----------|------------|---------|
| Business Name | Text | Yes | 2-100 chars | "Sparkle Clean Denver" |
| Phone | Tel | Yes | US phone format | (303) 555-0000 |
| Email | Email | Yes | Valid email | james@sparkleclean.com |
| Address | Address autocomplete | Yes | Google Places validated | 123 Main St, Denver, CO |
| Timezone | Dropdown | Yes | Auto-detected from address | America/Denver |
| Logo | File upload | No | JPG/PNG, max 2MB | sparkle-logo.png |

**Validation:**
- Phone: Format as user types, accept (XXX) XXX-XXXX or XXX-XXX-XXXX
- Address: Google Places autocomplete. Must select from suggestions (no freeform).
- Timezone: Pre-selected based on address. Editable dropdown.

**What happens next:** Business record created in `businesses` table. Slug auto-generated from name (e.g., `sparkle-clean-denver`). Owner linked via `business_members`. Redirect to Step 3.

**UI details:**
- "Skip for now" link at bottom (logo only)
- Back button to previous step
- "Next" button disabled until required fields valid

---

#### Step 3: Add Services

**What they see:** Card titled "What services do you offer?" with a pre-populated list of common cleaning services and an "Add Custom" option.

**What they input:**

Pre-populated suggestions (toggle on/off):
| Service | Default Duration | Default Price | Pre-selected |
|---------|-----------------|---------------|-------------|
| Standard Clean | 2.0 hrs | $120 | Yes |
| Deep Clean | 3.5 hrs | $220 | Yes |
| Move In/Out | 4.0 hrs | $350 | No |
| Post-Construction | 5.0 hrs | $500 | No |

For each selected service:
- Name: Editable text (pre-filled)
- Duration: Number input (hours, 0.5 increments)
- Base Price: Currency input ($)

**Validation:**
- At least 1 service must be active
- Duration: 0.5 - 12.0 hours
- Price: $1 - $9,999

**What happens next:** Services created in `cleaning_services` table linked to `business_id`. Redirect to Step 4.

**UI details:**
- Toggle switches for pre-populated services
- "Add Custom Service" button opens inline row
- Drag handle to reorder services

---

#### Step 4: Define Areas

**What they see:** Card titled "Where do you operate?" with a map and area input.

**What they input:**
| Field | Type | Required | Example |
|-------|------|----------|---------|
| Service Area Name | Text | Yes (at least 1) | "Denver Metro" |
| ZIP Codes or City | Multi-input | Yes | 80202, 80203, 80204 |

**Validation:**
- At least 1 area with at least 1 ZIP code
- ZIP codes validated against US postal database

**What happens next:** Areas created in `cleaning_areas` table. Used for team assignment scoring (proximity). Redirect to Step 5.

**UI details:**
- Map visualization showing coverage area as pins/polygons
- "Add Another Area" button for multi-area businesses
- Bulk ZIP code paste supported (comma-separated)
- Skip option: "I'll set this up later" (creates default area from business address ZIP)

---

#### Step 5: Create First Team

**What they see:** Card titled "Create your first cleaning team" with team creation form.

**What they input:**
| Field | Type | Required | Example |
|-------|------|----------|---------|
| Team Name | Text | Yes | "Team Alpha" |
| Color | Color picker | Yes (pre-selected) | #3B82F6 (blue) |
| Max Jobs/Day | Number | No (default: 6) | 5 |
| Service Areas | Multi-select | No | "Denver Metro" |

**Validation:**
- Team name: 2-50 chars, unique within business
- Max jobs: 1-15
- Color: Must be valid hex. Default palette offered (8 colors).

**What happens next:** Team created in `cleaning_teams`. No members yet (next step). Redirect to Step 6.

**UI details:**
- Color picker shows 8 default palette colors + custom hex input
- Preview card shows how the team will look in the schedule
- "I work alone" option: Creates a default team with owner as sole member, skips invite step

---

#### Step 6: Invite Cleaners

**What they see:** Card titled "Invite your team members" with email invitation form.

**What they input:**
| Field | Type | Required | Example |
|-------|------|----------|---------|
| Email | Email | Yes (at least for team lead) | ana@email.com |
| Name | Text | Yes | Ana Ramirez |
| Role | Dropdown | Yes | Member / Team Lead |
| Team | Dropdown (pre-filled) | Yes | Team Alpha |

**Validation:**
- Email must be valid format
- Cannot invite yourself
- Plan limits enforced: Basic = 3 cleaners max, Pro = 15, Business = 50
- Duplicate email check (within business)

**What happens next:**
1. Invitation record created in `cleaning_team_members` with `status = invited`
2. Email sent with invitation link: `#/register/invite/:token`
3. Token valid for 7 days
4. Redirect to Step 7

**UI details:**
- "Add Another" button for multiple invites
- "Skip for now" link (can invite later from Teams page)
- Counter showing "X / Y invites used" based on plan
- Bulk invite: paste CSV of name,email pairs

---

#### Step 7: Review & Launch

**What they see:** Summary card showing everything configured:

```
Business: Sparkle Clean Denver
  Phone: (303) 555-0000
  Timezone: America/Denver

Services (3):
  Standard Clean - 2h - $120
  Deep Clean - 3.5h - $220
  Move In/Out - 4h - $350

Areas (1): Denver Metro (80202, 80203, 80204)

Teams (1): Team Alpha (#3B82F6)
  Max 5 jobs/day

Invitations Sent (2):
  Ana Ramirez (ana@email.com) - Member
  Carlos Lima (carlos@email.com) - Team Lead
```

**What they input:** Review only. Edit links next to each section to go back.

**What happens next:**
- Click "Launch My Dashboard" button
- Onboarding marked complete in user profile
- Redirect to `#/owner/dashboard`
- Dashboard shows welcome state with onboarding checklist:
  - [x] Business info
  - [x] Services configured
  - [x] First team created
  - [ ] Add your first client
  - [ ] Generate your first schedule
  - [ ] Send your first invoice

---

### Flow 1.2: Daily Schedule Management

**Trigger:** Owner opens app in the morning (6:00 AM typical).
**Goal:** Ensure all teams know their jobs, handle changes throughout the day.
**Route:** `#/owner/dashboard` --> `#/owner/schedule`

```
Open App --> Dashboard (KPIs) --> Schedule View --> Generate Tomorrow -->
Review Jobs --> Assign Teams --> Confirm --> Cleaners Notified
```

#### Step 1: Open App / Dashboard Review

**What they see:** `#/owner/dashboard` with 4 KPI cards, team progress bars, overdue payments, and activity feed.

**KPI cards (real-time via SSE):**
| Card | Value | Tap Action |
|------|-------|------------|
| Revenue This Week | $4,280 (+12% vs last week) | Go to `#/owner/invoices` |
| Bookings Today | 18 (4 completed) | Go to `#/owner/schedule` (today) |
| Teams Active | 4/5 (1 off) | Go to `#/owner/teams` |
| Unassigned Jobs | 3 (red pulse if > 0) | Go to `#/owner/schedule` with unassigned filter |

**Team progress bars:**
```
Team Alpha   [=====>        ] 3/5 jobs  | In Progress (at Wilson's)
Team Beta    [===========>  ] 4/5 jobs  | At Mitchell's
Team Charlie [=>            ] 1/4 jobs  | En Route
Team Delta   [              ] 0/4 jobs  | Not Started
```

**What they input:** No input. This is an overview screen. Tap any element to drill down.

**What happens next:** Owner reviews KPIs. If unassigned jobs exist (red badge), taps to go to Schedule Builder.

---

#### Step 2: Open Schedule Builder

**What they see:** `#/owner/schedule` showing today's date. Desktop: team columns side by side with job cards. Mobile: one team at a time via dropdown.

**Layout (desktop):**
- Top: Date navigation (`< Prev Day | Today | Next Day >`) + view toggle (Day/Week/Month)
- Generate bar: `[Generate Today's Schedule]` `[AI Optimize]` (Pro+) `[Save Template]`
- Summary bar: `18 jobs | 5 teams active | 32 total hours | 3 unassigned [!]`
- Main: 5 team columns with job cards positioned by time (1 hour = 60px height)
- Bottom: Unassigned jobs queue (yellow/orange background)

**What they input:**
- Navigate to tomorrow's date using `[Next Day >]`
- Click `[Generate Tomorrow's Schedule]`

**Validation:**
- System checks `cleaning_client_schedules` for all recurring patterns matching tomorrow's day-of-week
- Matches found are converted to `cleaning_bookings` entries
- Each booking assigned to preferred team using scoring algorithm (area proximity, team history, workload balance)
- Conflicts detected: time overlaps flagged with orange border

**What happens next:** Schedule populated with job cards in team columns. Unassigned queue shows jobs that could not be auto-assigned (no preferred team, all teams full, new client).

---

#### Step 3: Review Generated Jobs

**What they see:** Job cards in team columns. Each card shows:
```
+------------------+
| 8:00 AM          |
| Henderson        |
| Deep Clean       |
| 2.5 hrs          |
| [Scheduled]      |
+------------------+
```

**What they input:** Click any job card to open side panel (400px right panel) with full details:
- Client name, address, service type, duration
- Team assigned, time slot
- Client notes (alarm codes, pet info, access instructions)
- Job actions: Reassign Team, Reschedule, Cancel, View Client Profile
- Last 3 visit history

**What happens next:** Owner reviews each team's workload visually. Proceeds to assign unassigned jobs.

---

#### Step 4: Assign Unassigned Jobs

**What they see:** Unassigned jobs queue at bottom of schedule (yellow background, pulsing red badge):
```
| Johnson | Standard | 2h | No preferred team | [Assign v] |
| Martinez| Deep     | 3h | All teams full    | [Assign v] |
| Wong    | Standard | 2h | New client        | [Assign v] |
```

**What they input:**
- Option A: Click `[Assign v]` dropdown. Shows teams ranked by score:
  ```
  Team Alpha  -- Score 87 (2 mi away, 1 slot open, knows client)
  Team Charlie -- Score 72 (5 mi away, 2 slots open)
  Team Delta  -- Score 65 (3 mi away, at capacity [!])
  ```
  Select a team. Job moves to team column.

- Option B (desktop): Drag job card from unassigned queue to a team column at desired time slot. Drop validation checks for conflicts.

**Validation:**
- If dropping on a time slot that conflicts with existing job: Modal appears: "This conflicts with Mitchell at 10 AM. Swap? Push later? Cancel?"
- If team exceeds max_daily_jobs: Warning shown but not blocked: "Team Alpha already has 6/6 jobs. Add anyway?"

**What happens next:** All jobs assigned. Summary bar updates: `18 jobs | 5 teams active | 32 total hours | 0 unassigned`.

---

#### Step 5: Confirm & Notify

**What they see:** All team columns filled. No unassigned jobs. Summary bar is green (all clear).

**What they input:** Click `[Confirm Schedule]` button (appears when changes exist).

**What happens next:**
1. All bookings saved to database with `status = scheduled`
2. Push notifications sent to ALL affected cleaners: "Tomorrow's schedule is ready. 3 jobs, 6.5 hours."
3. Each cleaner's `#/team/today` (for tomorrow) is populated
4. If any homeowner has notification preferences enabled, 24h reminder queued
5. Toast confirmation: "Schedule confirmed. 5 teams notified."

**Throughout the day (passive monitoring):**
- Dashboard auto-updates via SSE as cleaners check in/out
- Activity feed shows real-time events: "8:02 AM -- Team Alpha checked in at Henderson's"
- Team progress bars advance as jobs complete
- Owner can intervene anytime: cancel jobs, reassign teams, add emergency jobs

---

### Flow 1.3: Add New Client

**Trigger:** Owner receives a new client via phone/referral/walk-in.
**Goal:** Client fully set up with recurring schedule auto-generating bookings.
**Route:** `#/owner/clients` --> `#/owner/clients/:id`

```
Clients --> + Add Client --> Name/Phone/Email --> Address -->
Property Details --> Service Frequency --> Assign Team -->
Save --> Schedule Auto-Generated
```

#### Step 1: Navigate to Clients

**What they see:** `#/owner/clients` showing paginated table of all clients (127 total). Search bar, filters (status, tag, team, balance), sort options.

**What they input:** Click `[+ Add Client]` button (top right).

---

#### Step 2: Quick Add Modal (Minimum Required)

**What they see:** Modal with "Add New Client" title. Two modes: "Quick Add" (default) and "Full Form" button.

**Quick Add fields:**
| Field | Type | Required | Validation | Example |
|-------|------|----------|------------|---------|
| First Name | Text | Yes | 1-50 chars | Sarah |
| Last Name | Text | Yes | 1-50 chars | Henderson |
| Phone | Tel | Yes | US format | (303) 555-1234 |
| Email | Email | No | Valid email | sarah@email.com |
| Address | Address autocomplete | Yes | Google Places | 1234 Oak St, Denver CO |

**Validation:**
- Phone: Real-time format as user types
- Address: Must select from Google Places autocomplete suggestions
- Plan limit check: Basic = 50 clients max, Pro = 200, Business = unlimited
- If at limit: "You've reached your plan limit (50 clients). Upgrade to add more." with upgrade CTA

**What happens next:** Client record created in `cleaning_clients`. Homeowner invitation queued (optional). If "Quick Add", redirect to client detail page for property details.

---

#### Step 3: Property Details

**What they see:** Client detail page `#/owner/clients/:id` with expandable sections. "Property" section highlighted for completion.

**What they input:**
| Field | Type | Required | Example |
|-------|------|----------|---------|
| Property Type | Dropdown | Yes | House / Apartment / Condo / Townhouse / Office |
| Bedrooms | Number | No | 4 |
| Bathrooms | Number | No | 3 |
| Square Footage | Number | No | 2,800 |
| Floors | Number | No | 2 |

---

#### Step 4: Access & Preferences

**What they input (all optional but critical for operations):**
| Field | Type | Example |
|-------|------|---------|
| Key Location | Text | Under mat by back door |
| Alarm Code | Text (masked) | 4521 |
| Gate Code | Text | N/A |
| Parking Instructions | Text | Driveway, left side |
| Pet Type | Dropdown | Dog |
| Pet Name | Text | Max |
| Pet Notes | Text | Golden Retriever, friendly, stays in backyard |
| Rooms to Skip | Text | Master bedroom closet |
| Products to Avoid | Text | No bleach in kitchen |
| Special Instructions | Textarea | Shoes off at door |

**Validation:**
- Alarm/gate codes: Stored encrypted (Fernet AES-128)
- All text fields: Max 500 chars

---

#### Step 5: Service Frequency & Schedule

**What they input:**
| Field | Type | Required | Options |
|-------|------|----------|---------|
| Service Type | Dropdown | Yes | Standard Clean, Deep Clean, etc. |
| Frequency | Dropdown | Yes | Weekly / Biweekly / Monthly / Sporadic |
| Preferred Day | Dropdown | Yes (if recurring) | Monday-Saturday |
| Preferred Time | Time picker | Yes | 9:00 AM |
| Estimated Duration | Auto-calculated | Display only | 2.5 hrs (from service type) |
| Price | Currency | Yes (pre-filled from service) | $180 |
| Payment Method | Dropdown | No | Card on File / Cash / Invoice |

**Validation:**
- If Weekly: preferred_day_of_week required (0-6)
- If Biweekly: preferred_day + start_date required (to calculate alternating weeks)
- If Monthly: preferred_day + week_of_month (1st, 2nd, 3rd, 4th)
- If Sporadic: custom_interval_days (e.g., every 45 days)

---

#### Step 6: Assign Team

**What they input:**
| Field | Type | Required | Example |
|-------|------|----------|---------|
| Preferred Team | Dropdown | No | Team Alpha |

Dropdown shows teams ranked by:
1. Proximity to client address (uses service_area_ids matching)
2. Current workload (jobs/week)
3. Available capacity on preferred day

If no team selected: Job will appear in "Unassigned" queue during schedule generation.

---

#### Step 7: Save

**What they input:** Click `[Save Client]`.

**What happens next:**
1. Client record saved to `cleaning_clients`
2. House profile saved to `cleaning_houses`
3. Recurring schedule created in `cleaning_client_schedules`
4. Schedule engine picks up the new pattern on next generation
5. Toast: "Client Sarah Henderson added. Weekly Tuesday cleanings will appear in your schedule."
6. If homeowner email provided: "Invite Sarah to manage her bookings?" prompt
7. If accepted: Invitation email sent with link to `#/register/invite/:token` (homeowner role)

**Auto-generation behavior:**
- Next time owner clicks `[Generate Schedule]` for a date matching the pattern (e.g., next Tuesday), Henderson's booking is auto-created and assigned to Team Alpha
- If preferred team is at capacity, booking lands in unassigned queue

---

### Flow 1.4: Invoice Management

**Trigger:** Owner needs to review payment status, send invoices, or collect overdue payments.
**Goal:** Get paid for completed work with minimal manual effort.
**Route:** `#/owner/invoices`

```
Invoices --> See Overview (paid/pending/overdue) --> Click Invoice -->
View Detail --> Send to Client --> Client Pays Online --> Auto-Marked Paid
```

#### Step 1: Invoice Dashboard

**What they see:** `#/owner/invoices` with:
- Action bar: `[Batch Invoice]` `[Export CSV]` `[+ New Invoice]`
- Status tabs: `[All (245)]` `[Sent (18)]` `[Overdue (7)]` `[Paid (220)]`
- Search bar + date range filter
- Summary cards: This Month $8,240 | Outstanding $1,280 | Overdue $720

**What they input:** Click a status tab to filter. Default: "All" sorted by date descending.

---

#### Step 2: Batch Invoice (Auto-Generate)

**What they see:** Owner clicks `[Batch Invoice]`. Preview modal shows all completed jobs without invoices:
```
Generate invoices for 12 completed jobs:

[x] Henderson S. | Mar 19 | Deep Clean | $220
[x] Mitchell S.      | Mar 19 | Standard   | $160
[x] Rodriguez M. | Mar 19 | Standard   | $160
[x] Park J.      | Mar 18 | Standard   | $200
... (8 more)

Total: $2,140 across 12 invoices

[ ] Auto-send via email immediately
[ ] Auto-charge clients with card on file

[Generate All]  [Cancel]
```

**What they input:**
- Uncheck any jobs to exclude
- Toggle auto-send (sends invoice email to clients immediately)
- Toggle auto-charge (Pro+: charges clients with saved cards immediately)

**Validation:**
- Cannot invoice a job that is not "completed" status
- Cannot create duplicate invoice for same booking

**What happens next:**
1. Invoice records created in `cleaning_invoices` with unique sequential numbers (INV-248, INV-249, etc.)
2. If auto-send: Email sent to each client with payment link
3. If auto-charge: Stripe PaymentIntent created for each client with `payment_method` on file
4. Toast: "12 invoices generated. 8 auto-charged, 4 sent via email."

---

#### Step 3: View Invoice Detail

**What they see:** Click any invoice row. Side panel opens (desktop) or full-screen detail (mobile):
```
INV-246
Status: Sent (3 days ago)
Client: Sarah Mitchell
Service: Standard Clean (Mar 15)
Amount: $160.00
Due: Mar 15, 2026

Line Items:
  Standard Clean (2 hrs) ......... $160.00

Payment History:
  Mar 12 - Invoice created
  Mar 12 - Email sent to emily@email.com
  Mar 14 - Reminder sent (auto)

Actions:
  [Send Reminder]  [Mark Paid]  [Void]  [Download PDF]
```

**What they input:**
- `[Send Reminder]`: Sends reminder via client's preferred channel (email/WhatsApp/SMS)
- `[Mark Paid]`: Opens modal for manual payment recording:
  - Amount: $160 (pre-filled)
  - Method: Cash / Check / Venmo / Zelle / Other
  - Date: Today (editable)
  - Reference: Optional note
- `[Void]`: Cancels invoice with confirmation dialog
- `[Download PDF]`: Generates branded PDF invoice

---

#### Step 4: Client Pays Online

**What happens (client side):** Sarahreceives email with "Pay Now" button linking to `#/homeowner/invoices`. She clicks Pay Now. Stripe Checkout loads (in-app). Apple Pay/Google Pay available. She pays.

**What happens (owner side):**
1. Stripe webhook fires `payment_intent.succeeded`
2. Invoice status updated to `paid` in database
3. Owner receives push notification: "Sarah Mitchell paid INV-246 ($160)"
4. Invoice row in table updates to green "Paid" badge
5. Dashboard revenue KPI updates in real-time (SSE)

**Overdue handling:**
- Invoices past due date automatically get `overdue` status (daily cron)
- Overdue invoices show red badge with days count: "18 days overdue [!]"
- Auto-reminders configurable: 1 day before due, day of, 3 days after, 7 days after (owner sets in Settings)

---

### Flow 1.5: Team Management

**Trigger:** Owner needs to create a new team, handle a callout, or manage team composition.
**Goal:** Teams properly staffed and balanced for daily operations.
**Route:** `#/owner/teams`

```
Teams --> Create Team --> Name + Color --> Add Members (email invite) -->
Set Lead --> Set Max Jobs/Day --> Members Accept Invite --> Active
```

#### Step 1: Teams Overview

**What they see:** `#/owner/teams` showing team cards with stats:
```
Team Alpha [Active] (#3B82F6)
  Lead: Maria Santos
  Members: Maria Santos, Ana Ramirez, Carlos Lima
  Today: 4 jobs | 6.5 hrs | 2 completed
  This Week: 22 jobs | 38 hrs
  [Edit] [View Schedule] [Callout]
```

Workload Distribution chart (Pro+): Horizontal bars comparing hours per team.

---

#### Step 2: Create Team

**What they input:** Click `[+ Create Team]`. Modal opens:

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| Team Name | Text | Yes | 2-50 chars, unique within business |
| Color | Color picker | Yes | Hex color from palette or custom |
| Max Jobs/Day | Number | No (default: 6) | 1-15 |
| Service Areas | Multi-select checkboxes | No | From defined areas |

**Validation:**
- Plan limits: Basic = 1 team / 3 cleaners total, Pro = unlimited teams / 15 cleaners, Business = unlimited / 50 cleaners
- If at limit: Modal shows upgrade prompt instead of form

**What happens next:** Team record created in `cleaning_teams`. Team appears in list. No members yet.

---

#### Step 3: Add Members via Email Invite

**What they see:** After team creation, or via `[Edit]` on existing team. Member management section:
```
Members:
  Maria Santos (maria@email.com) -- Lead [Active]
  Ana Ramirez (ana@email.com) -- Member [Active]
  [+ Invite Member]

Invited (pending):
  Carlos Lima (carlos@email.com) -- Sent 2 days ago [Resend]
```

**What they input:**
| Field | Type | Required | Example |
|-------|------|----------|---------|
| Name | Text | Yes | Carlos Lima |
| Email | Email | Yes | carlos@email.com |
| Role in Team | Dropdown | Yes | Member / Team Lead |

**Validation:**
- Email must not already be a member of this business
- Plan member limit check
- Team can have only 1 lead (if selecting lead, current lead gets demoted to member with confirmation)

**What happens next:**
1. `cleaning_team_members` record created with `status = invited`
2. `cleaning_team_assignments` record created linking member to team
3. Email sent: "You've been invited to join Sparkle Clean Denver as a Cleaner"
4. Email contains link: `#/register/invite/:token`

---

#### Step 4: Set Team Lead

**What they input:** In team edit modal, click the crown icon next to a member name, or select "Team Lead" from role dropdown.

**What it means:**
- Team lead sees all team jobs (not just their own)
- Team lead can mark cash received on behalf of team
- Team lead appears first in team member list
- Team lead gets additional notifications (schedule changes for entire team)

---

#### Step 5: Members Accept Invite

**What happens (invitee side):**
1. Carlos opens email, clicks "Accept Invitation"
2. Lands on `#/register/invite/:token`
3. Sees: "You've been invited to join Sparkle Clean Denver as a Cleaner"
4. Creates account via Google OAuth or email/password
5. Account created. Role set to `cleaner` in `cleaning_user_roles`
6. `cleaning_team_members` status updated from `invited` to `active`
7. Redirected to `#/team/today` (cleaner home screen)

**What happens (owner side):**
1. Push notification: "Carlos Lima accepted the invitation and joined Team Alpha"
2. Team card updates: member count increases, "pending" label removed
3. Carlos now appears in team assignment suggestions

**Invitation expiry:**
- Token valid for 7 days
- After 7 days: "This invitation has expired. Contact your cleaning company."
- Owner can resend from Teams page

---

#### Step 6: Callout Handling (Team Member Sick)

**Trigger:** Owner learns Team Beta's lead is sick.

**What they input:** Click `[Callout]` on Team Beta card.

**What they see:** Callout flow modal:
```
Team Beta Callout

Who is unavailable?
  [x] Joao Silva (Lead)
  [ ] Lucia Fernandez
  [ ] Pedro Santos

Today's affected jobs (5):
  1. Park - 8:30 AM - Standard - 2h
  2. Mitchell - 11:00 AM - Standard - 2h
  3. Rodriguez - 1:30 PM - Standard - 2h
  4. White - 3:00 PM - Standard - 1.5h
  5. Brown - 4:30 PM - Standard - 1h

Suggested redistribution:
  Park --> Team Alpha (2 mi, has capacity) [Accept] [Change]
  Mitchell --> Team Charlie (same zip, 1 slot) [Accept] [Change]
  Rodriguez --> Team Delta (available, 3 mi) [Accept] [Change]
  White --> Team Delta (available, 3 mi) [Accept] [Change]
  Brown --> UNASSIGNED (all teams at capacity) [Assign v]

[Apply All Suggestions]  [Manual Reassign]  [Cancel All Jobs]
```

**What they input:**
- Accept individual suggestions or click `[Apply All Suggestions]`
- For jobs that cannot be auto-assigned, use `[Assign v]` dropdown or cancel

**What happens next:**
1. Bookings updated with new team assignments
2. All affected teams get push notification: "Schedule change: You have a new job today"
3. Original team (Beta) sees updated schedule (reduced jobs)
4. Owner dashboard updates in real-time

---

## 2. Cleaner Flows

### Flow 2.1: Daily Work Routine

**Trigger:** Cleaner (Ana) opens the app in the morning.
**Goal:** Complete all assigned jobs with GPS tracking, documentation, and real-time owner visibility.
**Route:** `#/team/today` --> `#/team/job/:id`

This is the CORE cleaner flow. Every interaction is designed for speed, large touch targets (48px+), and offline tolerance.

```
Open App --> Today's Jobs (list) --> See First Job --> Navigate (Google Maps) -->
Arrive --> Check In (GPS) --> Timer Starts --> Work (Checklist) -->
Add Notes/Photos --> Check Out (GPS) --> Timer Stops --> Next Job
```

#### Step 1: Open App / Today's Jobs

**What they see:** `#/team/today` with header showing date, team name, job count, and total hours.

```
Today's Jobs               Mar 18 [Sync]
Team Beta  |  3 jobs  |  6.5 hrs
```

Below header: ordered list of job cards. First job expanded (CURRENT), others collapsed (UPCOMING).

**Current job card (expanded):**
```
+----------------------------------------+
| [CURRENT]                              |
| 8:00 AM - 10:30 AM                    |
| Henderson, Sarah                       |
| 1234 Oak St, Denver CO                 |
| Deep Clean  |  2.5 hrs                 |
|                                        |
| [!] Alarm: 4521  Key: under mat       |
| [!] Pet: Max (Golden, friendly)       |
| [!] Skip master closet                |
|                                        |
| [  NAVIGATE  ]  [  CHECK IN  ]         |
+----------------------------------------+
```

- Access instructions shown with warning icons ([!]) for visibility
- NAVIGATE and CHECK IN buttons are full-width, 48px+ height, high contrast
- Travel time badge between cards: "30 min travel"

**Upcoming jobs (collapsed):**
```
| 11:00 AM | Mitchell, Sarah | Standard | 2h | [Navigate] |
| 2:00 PM  | Rodriguez   | Standard | 2h | [Navigate] |
```

**What they input:** None yet. Review jobs for the day.

**Offline behavior:** Jobs cached in IndexedDB from last sync. Yellow banner: "Offline -- showing last synced schedule (6:45 AM)." Pull-to-refresh attempts re-sync.

---

#### Step 2: Navigate to First Job

**What they input:** Tap `[NAVIGATE]` on Henderson card.

**What happens:**
1. App constructs navigation URI from client address
2. On Android: Opens Google Maps via `geo:` intent with address
3. On iOS: Opens Apple Maps (default), with "Open in Google Maps" option if installed
4. Fallback: Opens `https://maps.google.com/maps?daddr=1234+Oak+St+Denver+CO` in browser

**What they see:** Maps app with turn-by-turn directions. ETA displayed.

---

#### Step 3: Arrive & Check In

**What they see:** Back in CleanClaw app. Henderson card shows `[CHECK IN]` button (green, full-width, 56px height).

**What they input:** Tap `[CHECK IN]`.

**What happens (system):**
1. App requests GPS position via `navigator.geolocation.getCurrentPosition()`
2. GPS coordinates compared to client address geocode
3. Proximity check: Must be within 200 meters of client address
   - Within 200m: Green checkmark. Check-in recorded.
   - 200m - 1km: Yellow warning: "You appear to be 450m from the address. Check in anyway?" Allows override.
   - Beyond 1km: Red warning: "You appear to be far from this address. Are you at the right location?" Allows override with required note.
4. Timestamp recorded: `checked_in_at = NOW()` on `cleaning_bookings`
5. Timer starts: Visible at top of card, counts up from 0:00:00

**What the owner sees:** SSE event fires. Dashboard activity feed: "8:02 AM -- Team Beta checked in at Henderson's." Team progress bar updates.

**Card state changes to:**
```
+----------------------------------------+
| [IN PROGRESS] Timer: 0:04:22          |
| Henderson, Sarah                       |
| 1234 Oak St, Denver CO                 |
| Deep Clean  |  2.5 hrs est.           |
|                                        |
| [!] Alarm: 4521  Key: under mat       |
| [!] Skip master closet                |
|                                        |
| Checklist (0/6):                       |
|   [ ] Kitchen                          |
|   [ ] Bathrooms (3)                    |
|   [ ] Living room                      |
|   [ ] Bedrooms (3)                     |
|   [ ] Hallways and stairs              |
|   [ ] Windows (interior)               |
|                                        |
| [Add Note] [Add Photo] [Report Issue] |
|                                        |
| [         CHECK OUT         ]          |
+----------------------------------------+
```

---

#### Step 4: Work -- Checklist Progression

**What they see:** Service-specific checklist items with large checkboxes (48px tap target).

**What they input:** Tap checkboxes as they complete each area:
```
[x] Kitchen - counters, sink, floor
[x] Bathrooms (3) - full clean
[x] Living room - vacuum, dust, mop
[ ] Bedrooms (3) - vacuum, dust, beds
[ ] Hallways and stairs
[ ] Windows (interior)
Progress: 3/6 tasks
```

**Validation:** None -- checkboxes are optional but encouraged. Saved to IndexedDB immediately on tap. Synced to server when online.

---

#### Step 5: Add Notes / Photos

**Add Note:**
1. Tap `[Add Note]`
2. Text input opens inline (full-width textarea)
3. Type observation: "Kitchen faucet dripping, client should know"
4. Tap `[Save Note]`
5. Note saved to `cleaning_booking_notes` with timestamp
6. Owner can see notes in job detail side panel

**Add Photo:**
1. Tap `[Add Photo]`
2. Camera opens (native camera API via `<input type="file" accept="image/*" capture="camera">`)
3. Take photo
4. Photo compressed to max 1MB (canvas resize)
5. Preview shown with optional caption input
6. Tap `[Save]`
7. Photo saved to `photos_queue` in IndexedDB
8. Uploaded to server when online (background sync via service worker)
9. Owner sees photo in job detail

---

#### Step 6: Check Out

**What they input:** Tap `[CHECK OUT]` (green, full-width, 56px height).

**What happens (system):**
1. GPS captured (same proximity logic as check-in, but more lenient -- 500m threshold)
2. Timer stops. Duration calculated: `checked_out_at - checked_in_at`
3. Summary displayed:

```
+----------------------------------------+
| Job Complete!                          |
|                                        |
| Henderson, Sarah                       |
| Duration: 2h 22m (estimated: 2h 30m)  |
| Checklist: 6/6 complete               |
| Photos: 2 uploaded                     |
| Notes: 1 added                         |
|                                        |
| Cash payment?                          |
| Amount: [$          ] [Record Cash]    |
|                                        |
| [Done -- Next Job]                     |
+----------------------------------------+
```

4. Booking status updated to `completed`
5. Owner receives SSE event: "10:22 AM -- Team Beta completed Henderson's (2h 22m)"
6. If auto-invoice enabled: Invoice auto-generated

**What they input (optional):** If client paid cash, enter amount and tap `[Record Cash]`.

---

#### Step 7: Transition to Next Job

**What they input:** Tap `[Done -- Next Job]`.

**What they see:** Today's Jobs list refreshes. Henderson card collapsed (gray, completed). Mitchell card now expanded as CURRENT:
```
[COMPLETED] Henderson (2h 22m)

[CURRENT]
11:00 AM - 1:00 PM
Mitchell, Sarah
567 Maple Ave, Austin TX
Standard Clean  |  2 hrs
Travel time: 30 min

No shoes. Eco products. Dog "Buddy" in yard.

[  NAVIGATE  ]  [  CHECK IN  ]
```

**Cycle repeats** for each remaining job.

---

#### Step 8: End of Day

**What they see after all jobs completed:**
```
All done for today! Great job.

Summary:
  Jobs: 3/3 completed
  Total time: 6h 15m
  Cash collected: $160 (Rodriguez)

[View Earnings]
```

**Offline sync:** Any queued data (check-ins, check-outs, notes, photos) syncs automatically when connection restored. Green toast: "All data synced."

---

### Flow 2.2: Report Issue

**Trigger:** Cleaner finds a problem during a job (damage, safety hazard, access issue).
**Goal:** Document the issue with evidence and alert the owner immediately.
**Route:** `#/team/job/:id` (during active job)

```
During Job --> Report Issue Button --> Select Type -->
Describe --> Take Photo --> Submit --> Owner Notified Instantly
```

#### Step 1: Initiate Report

**What they see:** During an active job, the action bar shows `[Report Issue]` button (orange/warning color).

**What they input:** Tap `[Report Issue]`.

---

#### Step 2: Select Issue Type

**What they see:** Modal with category buttons (large, 48px height each):

```
What type of issue?

[  Locked Out / No Access  ]
[  Property Damage (Found) ]
[  Property Damage (Caused)]
[  Safety Hazard            ]
[  Pet Issue                ]
[  Client Not Home          ]
[  Missing Supplies         ]
[  Other                    ]
```

**What they input:** Tap one category.

**Category-specific behavior:**
| Category | Photo Required? | Severity | Owner Alert |
|----------|----------------|----------|-------------|
| Locked Out / No Access | No | High | Immediate push |
| Property Damage (Found) | **Yes** | Medium | Immediate push |
| Property Damage (Caused) | **Yes** | **Critical** | Immediate push + SMS |
| Safety Hazard | Yes | High | Immediate push |
| Pet Issue | No | Medium | Push |
| Client Not Home | No | Low | Push |
| Missing Supplies | No | Low | Push (batched) |
| Other | No | Medium | Push |

---

#### Step 3: Describe Issue

**What they see:** Text area with category-specific prompt:

For "Property Damage (Found)":
```
Describe the damage:
[Found broken vase in living room.        ]
[It was already broken before we arrived.  ]
[Client may not be aware.                  ]

Where in the house?
[Living room, on the shelf by the window   ]
```

**Validation:** Description required (min 10 characters). Location optional but encouraged.

---

#### Step 4: Take Photo (if required)

**What they see:** Camera prompt: "Take a photo of the issue."

**What they input:**
1. Camera opens
2. Take photo of the damage/issue
3. Preview shown
4. Option to take additional photos (up to 5)
5. Tap `[Confirm]`

**Validation:** For "Property Damage (Found)" and "Property Damage (Caused)" categories, at least 1 photo is mandatory. Submit button disabled until photo attached.

---

#### Step 5: Submit Report

**What they input:** Tap `[Submit Report]`.

**What happens:**
1. Issue record created in `cleaning_booking_issues` with:
   - `booking_id`, `category`, `description`, `location`, `severity`
   - `reported_by` (cleaner user ID)
   - `reported_at` (timestamp)
   - Photo URLs (queued for upload if offline)
2. Owner notification:
   - Push notification: "ISSUE: Property Damage at Henderson's -- broken vase found. View details."
   - For Critical severity: SMS also sent to owner phone
   - Notification links to job detail with issue section highlighted
3. Cleaner sees confirmation: "Issue reported. Maria has been notified."
4. Issue appears in job detail card with orange badge: "[Issue Reported]"
5. Cleaner continues working (job not paused by issue report)

**Offline behavior:**
- Issue saved to IndexedDB
- Queued for sync
- Photo queued for upload
- Yellow note: "Issue saved locally. Owner will be notified when you're back online."
- Issue still shows on job card with "(pending sync)" label

---

### Flow 2.3: View Earnings

**Trigger:** Cleaner wants to see their work summary and estimated pay.
**Goal:** Transparency into hours worked and jobs completed.
**Route:** `#/team/earnings`

```
Earnings Tab --> See This Week/Month --> Daily Breakdown -->
Performance Metrics
```

#### Step 1: Navigate to Earnings

**What they see:** Tap "Earnings" in bottom tab bar. Screen loads with KPI cards and breakdowns.

**Period selector:** Dropdown at top right: `[This Week v]` options: This Week, Last Week, This Month, Last Month.

---

#### Step 2: KPI Summary

**What they see:**
```
+----------+ +----------+ +-----------+
| 14.5 hrs | | 7 jobs   | | $XXX.XX   |
| Worked   | | Completed| | Estimated |
+----------+ +----------+ +-----------+
```

Note: Estimated earnings shown only if owner has enabled pay rate visibility in settings. Otherwise: "Contact Sparkle Clean Denver for pay info."

---

#### Step 3: Daily Breakdown

**What they see:**
```
Mon 18 | 6.5 hrs | 3 jobs | $XXX
  Henderson (Deep) - 2h 22m
  Mitchell (Standard) - 1h 55m
  Rodriguez (Standard) - 2h 10m

Tue 19 | 8.0 hrs | 3 jobs | $XXX
  Park (Standard) - 2h 05m
  Williams (Deep) - 3h 10m
  Thompson (Standard) - 1h 45m

Wed 20 | -- (today, in progress)
Thu 21 | -- (scheduled)
Fri 22 | -- (day off)
```

**What they input:** Tap a day row to expand and see individual job details.

---

#### Step 4: Monthly Summary

**What they see:**
```
This Month Summary:
  Total Hours: 52.5
  Total Jobs: 24
  On-Time Rate: 96%    (checked in within 10 min of scheduled time)
  Average Rating: 4.8  (from homeowner reviews)
  Completion Rate: 100% (no missed jobs)
```

**What happens next:** Informational only. No actions required. Cleaner can screenshot for personal records.

---

## 3. Homeowner Flows

### Flow 3.1: Request Cleaning

**Trigger:** Homeowner wants a one-time or additional cleaning outside their recurring schedule.
**Goal:** Submit a request that the owner can approve and schedule.
**Route:** `#/homeowner/bookings`

```
My Bookings --> + Request Cleaning --> Select Service -->
Pick Date --> Pick Time Slot --> Add Instructions -->
Submit --> Confirmation --> Appears in Upcoming
```

#### Step 1: Navigate to Bookings

**What they see:** `#/homeowner/bookings` with:
- NEXT CLEANING hero card (largest element on screen)
- Upcoming cleanings list
- Past cleanings with rating prompt
- Outstanding payment card (if any)
- `[+ Request Cleaning]` button (top right on desktop, floating action button on mobile)

---

#### Step 2: Select Service

**What they input:** Tap `[+ Request Cleaning]`. Modal/page opens:

```
Request a Cleaning

Service Type:
  [ ] Standard Clean ($160, ~2 hrs)
  [x] Deep Clean ($220, ~3.5 hrs)
  [ ] Move In/Out ($350, ~4 hrs)
```

Select one service. Price and estimated duration shown for each.

---

#### Step 3: Pick Date

**What they see:** Calendar view showing next 2 weeks. Days with available slots shown in blue. Days fully booked shown in gray. Past days disabled.

```
March 2026
     Mon  Tue  Wed  Thu  Fri  Sat
     18   19   20   21   22   23
          [x]       [x]  [x]
     25   26   27   28   29   30
     [x]       [x]            [x]

[x] = Available slot
```

**What they input:** Tap an available date (e.g., Friday Mar 22).

**Availability logic:** System checks team capacity for that date. Available means at least one team has a slot that fits the requested service duration.

---

#### Step 4: Pick Time Slot

**What they see:** Available time slots for the selected date:

```
Available times for Friday, Mar 22:

[  8:00 AM - 11:30 AM  ]
[  1:00 PM - 4:30 PM   ]
[  2:30 PM - 6:00 PM   ]
```

**What they input:** Tap a time slot.

---

#### Step 5: Add Instructions

**What they see:** Optional text area:

```
Any special instructions for this cleaning?
[Please focus on the kitchen and bathrooms.    ]
[We're having guests this weekend.              ]
[                                               ]

Your saved access instructions will be shared
with the team. [Review/Edit]

[Submit Request]
```

**What they input:** Optional instructions text. Can also tap `[Review/Edit]` to update access instructions before the visit.

---

#### Step 6: Submit & Confirmation

**What they input:** Tap `[Submit Request]`.

**What happens:**
1. Booking request created in `cleaning_bookings` with `status = requested` (not yet confirmed)
2. Owner receives push notification: "Sarah Mitchell requested a Deep Clean on Fri Mar 22, 1:00 PM"
3. Homeowner sees confirmation:

```
Request Submitted!

Deep Clean
Friday, March 22 at 1:00 PM
Estimated: 3.5 hrs | $220

Status: Pending Confirmation
We'll notify you once your cleaning is confirmed.
```

4. Owner reviews in Schedule Builder, assigns team, confirms
5. Booking status changes to `scheduled`
6. Homeowner receives push: "Your Deep Clean on Fri Mar 22 at 1:00 PM is confirmed! Team Alpha will be there."
7. Booking appears in "Upcoming" list on homeowner's bookings page

---

### Flow 3.2: Manage Booking (Reschedule / Cancel)

**Trigger:** Homeowner needs to change or cancel an upcoming cleaning.
**Goal:** Easy self-service with policy enforcement.
**Route:** `#/homeowner/bookings` or `#/homeowner/bookings/:id`

```
My Bookings --> Click Booking --> See Details -->
Reschedule (pick new date) --> OR Cancel (reason) --> Confirmation
```

#### Step 1: View Booking Details

**What they see:** Tap on a booking card or the "Next Cleaning" hero card. Detail view:

```
Thursday, March 20, 2026
10:00 AM - 12:00 PM (2 hours)
Status: Scheduled

Service: Standard Clean
Team: Team Beta (Joao, Lucia)
Price: $160.00

Your Access Instructions:
  Key: Under mat by back door
  Alarm: 4521
  Pet: Dog "Max" in backyard
  Special: No shoes, no bleach in kitchen
  [Edit Instructions]

[Reschedule This Cleaning]
[Cancel This Cleaning]
```

---

#### Step 2a: Reschedule

**What they input:** Tap `[Reschedule This Cleaning]`.

**What they see:** Date/time picker (same as Request flow):
```
Select a new date:
  [Calendar showing next 2 weeks with available dates]

Select a new time:
  [8:00 AM]  [10:00 AM]  [1:00 PM]  [3:00 PM]
```

Select new date + time.

**Policy check:**
```
Reschedule from Thu Mar 20 10:00 AM
           to   Fri Mar 21 2:00 PM

Notice: 36 hours (Free reschedule)
Policy: Reschedules with 24+ hours notice are free.

Monthly limit: 1 of 2 used this month.

[Confirm Reschedule]  [Cancel]
```

**What happens on confirm:**
1. Original booking updated: `scheduled_date` changed, `status = rescheduled`
2. Homeowner sees updated "Next Cleaning" card with new date
3. Owner gets push: "Sarah Mitchell rescheduled Thu 10 AM to Fri 2 PM"
4. Team schedule updated automatically (Thursday slot freed, Friday slot booked)
5. If team is different on new date: Team assignment may change (owner notified)
6. Confirmation email sent to homeowner

**If within 24 hours (late reschedule):**
```
Late Reschedule

Your cleaning is in 18 hours.
Rescheduling within 24 hours incurs a fee per our policy.

Fee: $50
New date: Fri Mar 21 2:00 PM

[Accept Fee & Reschedule]  [Keep Original Date]
```

Fee invoice auto-generated if accepted.

---

#### Step 2b: Cancel

**What they input:** Tap `[Cancel This Cleaning]`.

**What they see:**
```
Cancel your Thursday cleaning?

Reason (optional):
  [ ] Traveling / Not home
  [ ] Schedule conflict
  [ ] No longer need service
  [ ] Other: [________________]
```

**Policy check (>24h notice):**
```
Free cancellation (36 hours notice).
[Confirm Cancellation]  [Keep Booking]
```

**Policy check (<24h notice):**
```
Late Cancellation

Your cleaning is in 6 hours.
Late cancellations incur a $50 fee per our policy.

[Accept Fee & Cancel]  [Keep Booking]
```

**What happens on confirm:**
1. Booking status set to `cancelled`. Reason recorded.
2. Team schedule updated: slot freed
3. Owner gets push: "Sarah Mitchell cancelled Thu 10 AM cleaning"
4. Homeowner sees: "Cleaning cancelled. Your next cleaning is Apr 3."
5. If fee applies: Invoice auto-generated and sent
6. If recurring: Next occurrence in schedule unaffected (only this instance cancelled)

---

### Flow 3.3: Pay Invoice

**Trigger:** Homeowner has an outstanding invoice (cleaning completed, payment due).
**Goal:** Fast, secure online payment with receipt.
**Route:** `#/homeowner/invoices`

```
My Invoices --> See Balance Due --> Click Pay -->
Stripe Checkout --> Payment Confirmed --> Receipt Email -->
Invoice Marked Paid
```

#### Step 1: View Invoices

**What they see:** `#/homeowner/invoices` with tabs: `[Unpaid (1)]` `[Paid (18)]` `[All]`

Unpaid invoice card (prominent, at top):
```
INV-246  |  Mar 15  |  Standard Clean  |  $160.00
Status: Sent  |  Due in 3 days
[Pay Now]                     [View Details]
```

Card on file section at bottom:
```
Card on File: Visa ****4242  [Manage]
Auto-Pay: ON  [Turn Off]
```

---

#### Step 2: Pay Now

**What they input:** Tap `[Pay Now]`.

**What they see:** Stripe Checkout embedded or redirected:
```
Pay Sparkle Clean Denver
INV-246 - Standard Clean (Mar 15)

Amount: $160.00

[Apple Pay]  [Google Pay]

Or pay with card:
  Card: Visa ****4242 (saved)
  [Use saved card]

  Or enter new card:
  [Card Number          ]
  [MM/YY]  [CVC]

Add a tip? (optional)
  [No tip]  [$10]  [$20]  [Custom]

[Pay $160.00]
```

**What they input:** Tap saved card or enter new card. Optional tip. Tap `[Pay $160.00]`.

---

#### Step 3: Payment Confirmation

**What they see (in-app):**
```
Payment Successful!

$160.00 paid to Sparkle Clean Denver
Invoice: INV-246
Date: March 15, 2026
Method: Visa ****4242

A receipt has been sent to emily@email.com.

[Download Receipt]  [Back to Invoices]
```

**What happens (system):**
1. Stripe processes payment. `payment_intent.succeeded` webhook fires.
2. Invoice status updated to `paid` in database
3. Payment recorded: amount, method, timestamp, Stripe charge ID
4. Receipt email sent to homeowner automatically
5. Owner receives push: "Sarah Mitchell paid INV-246 ($160)"
6. Owner dashboard revenue KPI updates in real-time

**Auto-pay behavior:**
- If auto-pay is ON and card on file exists:
  - Invoice auto-charged on creation (no homeowner action needed)
  - Homeowner receives: "Your card was charged $160 for Standard Clean on Mar 15. Receipt attached."
  - If charge fails: Email sent: "Payment failed for INV-246. Please update your card." Invoice moves to "unpaid" with retry button.

---

### Flow 3.4: Set Preferences

**Trigger:** Homeowner needs to update house details, access info, or cleaning preferences.
**Goal:** Keep cleaning team informed with accurate property information.
**Route:** `#/homeowner/preferences`

```
My Home --> Contact Info --> Address --> Property Details -->
Pets --> Access Instructions --> Cleaning Preferences --> Save
```

#### Step 1: Navigate to My Home

**What they see:** `#/homeowner/preferences` (bottom tab "My Home" on mobile). Page title: "My Home -- 567 Maple Ave, Austin TX"

---

#### Step 2: Review & Edit Sections

**Access Instructions (most critical):**
| Field | Type | Editable | Example |
|-------|------|----------|---------|
| Key Location | Text | Yes | Under the blue pot on the porch |
| Alarm Code | Text (masked, reveal on tap) | Yes | 7788 |
| Gate/Garage Code | Text | Yes | N/A |
| Parking Instructions | Text | Yes | Park on street, not in driveway |

**Pet Information:**
| Field | Type | Editable | Example |
|-------|------|----------|---------|
| Pet Type | Dropdown | Yes | Dog / Cat / Bird / Reptile / Other / None |
| Pet Name | Text | Yes | Buddy |
| Temperament | Textarea | Yes | Friendly, stays in backyard during cleaning |

**Cleaning Preferences:**
| Field | Type | Editable | Example |
|-------|------|----------|---------|
| Rooms to Skip | Textarea | Yes | Home office (door will be closed) |
| Products to Avoid | Textarea | Yes | No bleach anywhere. Use eco products. |
| Special Instructions | Textarea | Yes | Please remove shoes at door. Don't move items on desk in office. |

**Read-only fields (contact business to change):**
| Field | Value | Why Read-Only |
|-------|-------|--------------|
| Address | 567 Maple Ave, Austin TX | Changing address is a service-level change |
| Service Type | Standard Clean | Affects pricing, must go through owner |
| Frequency | Biweekly | Schedule change requires owner approval |
| Price | $160 | Business pricing decision |

Footer text: "To change your address, service, or schedule, contact Sparkle Clean Denver at (303) 555-0000."

---

#### Step 3: Save

**What they input:** Edit any field. Tap `[Save Changes]` at bottom.

**Validation:**
- All text fields: Max 500 chars
- Alarm/gate codes: Stored encrypted
- At least one field must have changed (button disabled if no changes)

**What happens:**
1. House profile updated in `cleaning_houses`
2. Toast: "Preferences saved. Your team will see the updates."
3. Owner gets push: "Sarah Mitchell updated access instructions." (for security-sensitive fields: alarm code, key location)
4. Next time a cleaner opens a job at this address, they see updated info
5. If cleaner is currently checked in at this house: SSE event pushes update to their job detail screen

**Offline behavior:**
- Changes saved to IndexedDB
- Banner: "You're offline. Changes will be saved when you're back online."
- On reconnect: Changes synced automatically. Toast: "Preferences synced."

---

## 4. Cross-Role Interactions

### 4.1: The Complete Booking Lifecycle

This traces a single cleaning from creation to payment across all 3 roles.

```
PHASE 1: SCHEDULE CREATION (Owner)
Owner --> Settings: Creates "Standard Clean" service ($160, 2h)
Owner --> Clients: Adds Sarah Mitchell (biweekly, Tuesday 10am, Team Beta)
Owner --> Schedule: cleaning_client_schedules record created

PHASE 2: BOOKING GENERATION (System / Owner)
Sunday night or Monday morning:
  Owner --> Schedule Builder: Clicks [Generate Tuesday's Schedule]
  System reads cleaning_client_schedules WHERE day=Tuesday
  System creates cleaning_bookings entry:
    client=Sarah Mitchell, service=Standard, team=Team Beta,
    date=Tuesday, time=10:00 AM, status=scheduled

PHASE 3: NOTIFICATIONS (System)
  24h before (Monday 10 AM):
    System --> Sarah: Push + Email "Reminder: Cleaning tomorrow at 10 AM"
    System --> Team Beta: Push "Tomorrow: 5 jobs starting at 8 AM"

PHASE 4: EXECUTION (Cleaner)
  Tuesday 9:55 AM:
    Ana (Team Beta) --> Navigates to 567 Maple Ave
  Tuesday 10:02 AM:
    Ana --> CHECK IN (GPS verified)
    System --> Owner dashboard: "Team Beta checked in at Mitchell's"
  Tuesday 10:02 - 12:05 PM:
    Ana --> Works through checklist
    Ana --> Takes 1 photo (kitchen)
    Ana --> Adds note: "Microwave needs cleaning inside"
  Tuesday 12:05 PM:
    Ana --> CHECK OUT
    System --> Booking status = completed, duration = 2h 03m

PHASE 5: INVOICING (System / Owner)
  Immediately after checkout (if auto-invoice ON):
    System --> Creates INV-258 ($160) linked to booking
    System --> Sarah: Email with "Pay Now" link
  OR end-of-day batch:
    Owner --> Invoices: Clicks [Batch Invoice]
    Reviews and sends all day's invoices at once

PHASE 6: PAYMENT (Homeowner)
  If auto-pay ON:
    System --> Charges Sarah's Visa ****4242 for $160
    System --> Sarah: "Payment processed. Receipt attached."
    System --> Owner: "Sarah Mitchell paid INV-258 ($160)"
  If manual pay:
    Sarah--> #/homeowner/invoices --> [Pay Now]
    Sarah--> Stripe Checkout --> Pays $160
    System --> Owner: "Sarah Mitchell paid INV-258 ($160)"

PHASE 7: REPORTING (Owner)
  Owner --> Dashboard: Revenue KPI shows $160 added
  Owner --> Invoices: INV-258 shows "Paid" (green)
  Owner --> Client detail (Sarah): LTV increases to $2,960
```

---

### 4.2: Notification Flow

**Who gets notified, when, and how for each event:**

| Event | Owner | Cleaner (Team) | Homeowner |
|-------|-------|----------------|-----------|
| **New booking created** | Push: "New booking: Mitchell, Tue 10 AM" | Push: "New job added to Tuesday" | Email: "Your cleaning on Tuesday is confirmed" |
| **Booking confirmed** (from request) | -- (owner confirms manually) | Push: "New job confirmed for Friday" | Push + Email: "Your Deep Clean on Friday is confirmed" |
| **24h reminder** | -- | Push: "Tomorrow: 5 jobs starting at 8 AM" | Push + Email: "Reminder: Cleaning tomorrow at 10 AM" |
| **Cleaner checked in** | Push: "Team Beta checked in at Mitchell's" | -- (they did it) | Push: "Your team has arrived!" |
| **Job completed** | SSE dashboard update | Summary shown on screen | Push: "Your cleaning is complete!" |
| **Invoice sent** | -- (owner sends it) | -- | Email: "Invoice $160 from Sparkle Clean. Pay Now." |
| **Payment received** | Push: "Sarah Mitchell paid $160" | -- | Email: "Receipt for $160 payment" |
| **Booking cancelled by homeowner** | Push: "Sarah cancelled Tue 10 AM" | Push: "Job cancelled: Mitchell, Tue 10 AM" | Email: "Cancellation confirmed" |
| **Booking rescheduled by homeowner** | Push: "Sarah rescheduled Tue 10 AM to Fri 2 PM" | Push: "Schedule changed for this week" | Email: "Reschedule confirmed: Fri 2 PM" |
| **Issue reported by cleaner** | Push (immediate): "ISSUE at Mitchell's: Property Damage" | -- (they reported it) | -- (owner decides whether to inform) |
| **Schedule changed by owner** | -- (they did it) | Push: "Schedule updated. Pull to refresh." | Push (if their booking affected): "Your cleaning time has changed" |
| **Callout / team reassignment** | -- (they initiated it) | Push (new team): "New job: Mitchell, 10 AM (reassigned)" | Push: "Your cleaning team has changed to Team Alpha" |

**Notification channels by role:**
| Role | Push (PWA) | Email | SMS (Twilio) | WhatsApp |
|------|-----------|-------|-------------|----------|
| Owner | Always | Summary (daily digest optional) | Critical issues only | -- |
| Cleaner | Always (primary) | Invitation only | Schedule changes | Schedule changes (if enabled) |
| Homeowner | Booking events | Invoices + receipts + confirmations | Reminders (if opted in) | Reminders (if opted in) |

**Notification channels by tier:**

| Channel | Basic | Pro | Business |
|---------|-------|-----|----------|
| Email | Yes | Yes | Yes |
| Push | Yes | Yes | Yes |
| SMS | No | Yes (500/mo) | Yes (unlimited) |
| WhatsApp | No | No | Yes |

---

## 5. Error States & Edge Cases

### 5.1: No Internet (Offline Mode)

**Cleaner (offline-FIRST design):**

| Action | Online | Offline |
|--------|--------|---------|
| View Today's Jobs | Live from server | Cached in IndexedDB (today + 2 days synced) |
| Navigate to address | Google Maps (online) | Cached address text, "Maps unavailable offline" |
| Check In | GPS + server write | GPS captured, write queued in `sync_queue` |
| Check Out | GPS + server write | GPS captured, write queued in `sync_queue` |
| Checklist | Live sync | Saved to IndexedDB, synced on reconnect |
| Add Note | Live sync | Saved to IndexedDB, synced on reconnect |
| Add Photo | Upload immediately | Compressed, saved to `photos_queue`, uploaded on reconnect |
| Report Issue | Live sync + push notification | Saved locally, synced on reconnect (owner notified late) |

Banner: "Offline -- showing last synced schedule (6:45 AM). Your check-ins and notes will sync when you're back online."

**Owner:**

| Screen | Offline Behavior |
|--------|-----------------|
| Dashboard | Cached KPIs + team progress. "Showing data from 5 min ago." No real-time updates. |
| Schedule Builder | Cached schedule (read-only). No drag-drop. No generate. "Offline -- changes cannot be saved." |
| Clients | Cached list. Search works (client-side filter). Add/Edit disabled. |
| Invoices | Cached list. Create/Send disabled. View details works. |

**Homeowner:**

| Screen | Offline Behavior |
|--------|-----------------|
| My Bookings | Cached bookings shown. Reschedule/Cancel disabled. |
| My Invoices | Cached list. Pay Now disabled. Download Receipt works (if cached). |
| My Preferences | Edit locally, saved to IndexedDB, synced on reconnect. |

**Reconnection behavior (all roles):**
1. Service worker detects connection restored
2. `sync_queue` processed in order (FIFO)
3. Conflicts resolved: server wins for schedule changes, client wins for notes/preferences
4. Toast: "Back online. All changes synced."
5. SSE connection re-established for real-time updates

---

### 5.2: GPS Unavailable

**Trigger:** Cleaner tries to Check In but GPS is denied, unavailable, or inaccurate.

**Scenario 1: GPS permission denied**
```
Location Access Required

CleanClaw needs your location to verify check-in.

[Open Settings]  [Check In Without GPS]
```
- "Check In Without GPS" allowed but flagged for owner: "Ana checked in without GPS verification."
- Owner sees orange warning badge on the check-in event

**Scenario 2: GPS timeout (>10 seconds)**
```
Location taking too long...

Your check-in will be recorded without GPS.
You can also try:
  1. Go outside briefly for better signal
  2. Turn on Wi-Fi (helps GPS accuracy)
  3. Check in without location

[Retry]  [Check In Without GPS]
```

**Scenario 3: GPS wildly inaccurate (>1km from address)**
```
Location Mismatch

Your GPS shows you're 2.3 km from this address.

Are you at the right location?
  [Yes, Check In Anyway]  (requires note)
  [Cancel]

Note: [I'm inside the building, GPS is off  ]
```
- If "Check In Anyway": Recorded with override flag + mandatory note. Owner sees: "Ana checked in at Henderson's (GPS override: 2.3 km away -- 'inside building')"

---

### 5.3: Payment Fails

**Scenario 1: Homeowner's card declined at Stripe Checkout**
```
Payment Failed

Your card ending in 4242 was declined.
Reason: Insufficient funds

[Try Different Card]  [Try Again Later]
```
- Invoice stays "Sent" (not "Failed")
- Owner NOT notified immediately (avoids embarrassment)
- If auto-pay fails: Homeowner gets email: "Your automatic payment for INV-246 could not be processed. Please update your payment method."
- After 3 failed auto-pay attempts: Auto-pay disabled for this client. Owner notified: "Auto-pay disabled for Sarah Mitchell after 3 failed attempts."

**Scenario 2: Stripe is down / network error**
```
Payment Error

We couldn't process your payment right now.
This is a temporary issue, not a problem with your card.

[Try Again]  [Pay Later]
```
- No status change on invoice
- Retry recommended

**Scenario 3: Owner marks paid manually (fallback)**
- If online payment consistently fails, owner can mark invoice as paid manually
- Records: amount, method (cash/check/Venmo/Zelle), date, reference
- Invoice marked "Paid (manual)" -- different badge from "Paid (online)"

---

### 5.4: Team Fully Booked

**Trigger:** Owner tries to assign a job but all teams are at max_daily_jobs.

**Scenario 1: During schedule generation**
```
Schedule Generated with Issues

18 bookings scheduled across 5 teams.
3 bookings could not be assigned:
  - Johnson (Standard, 2h) -- All teams at capacity
  - Martinez (Deep, 3h) -- All teams at capacity for 3h block
  - Wong (Standard, 2h) -- New client, no preferred team

These appear in your Unassigned queue.

[View Schedule]  [Increase Team Capacity]
```

**Scenario 2: Owner manually assigning**
```
Team Alpha is at capacity (6/6 jobs)

Options:
  [Assign Anyway]  -- Exceeds daily limit (team will be overworked)
  [Find Another Team]  -- Show teams with available slots
  [Reschedule to Tomorrow]  -- Move job to next available date
  [Cancel Job]
```

**Scenario 3: Homeowner requests cleaning on fully booked day**
```
No Available Times

Sorry, all our teams are fully booked on Friday, March 22.

Available alternatives:
  Thursday, March 21: [8 AM] [1 PM]
  Saturday, March 23: [9 AM]
  Monday, March 25: [8 AM] [10 AM] [2 PM]

[Select Alternative]  [Request Waitlist]
```
- "Request Waitlist": Homeowner added to waitlist. If a cancellation opens a slot, they get notified: "A slot opened up on Friday at 10 AM. Book now?"

---

### 5.5: Client Cancels Last Minute

**Trigger:** Homeowner cancels within 1-2 hours of cleaning start. Team may already be en route.

**Timeline:**

```
8:00 AM -- Job scheduled (Mitchell, Team Beta)
7:30 AM -- Team Beta starts driving to first job (Henderson, 8 AM)
7:45 AM -- Sarahcancels her 10 AM booking

SYSTEM RESPONSE:
1. Sarah's booking status = cancelled
2. Policy check: <24h notice = $50 late fee
3. Sarahsees: "Late cancellation fee: $50. Cancel anyway?"
4. Sarahconfirms

NOTIFICATIONS:
5. Owner gets IMMEDIATE push:
   "Sarah Mitchell cancelled 10 AM booking (late). $50 fee applied."

6. Team Beta gets IMMEDIATE push:
   "CANCELLED: Mitchell, 10 AM - 567 Maple Ave. Do NOT go."

7. If cleaner has already navigated to this address:
   RED URGENT banner on #/team/today:
   "CANCELLED: Mitchell, Sarah. Do NOT go to 567 Maple Ave."
   Banner persists until cleaner dismisses (prevents driving to house)

8. Schedule auto-adjusts:
   - Gap appears in Team Beta's schedule (10-12 PM)
   - If unassigned jobs exist for this time window:
     Owner sees suggestion: "Fill gap? Assign Wong (Standard, 2h) to Team Beta 10 AM?"

INVOICING:
9. $50 cancellation fee invoice auto-generated
10. Sent to Sarahvia email
11. If auto-pay: Charged to card on file
```

**If cleaner already checked in (worst case):**
```
Scenario: Sarahcancels AFTER team checked in at her house.

System blocks cancellation:
"Your team has already arrived and started.
This cleaning can no longer be cancelled online.
Contact Sparkle Clean Denver at (303) 555-0000."

Full price charged (no partial refund via self-service).
Owner handles exceptions manually.
```

---

### 5.6: Double-Booking Detection

**Trigger:** Schedule generation or manual assignment creates a time overlap for a team.

**Detection:** System checks all bookings for the team on that date. If `start_time + duration` overlaps with another booking's `start_time`:

```
Conflict Detected

Team Alpha has overlapping jobs:

  9:00 AM - 11:00 AM  Henderson (Standard)
  10:30 AM - 12:30 PM  Wilson (Standard)

  Overlap: 30 minutes (10:30 - 11:00 AM)

Resolution options:
  [Push Wilson to 11:30 AM]  -- Adds 30 min gap
  [Swap Wilson to Team Beta]  -- Team Beta has a 10:30 slot
  [Shorten Henderson by 30m]  -- Reduce from 2h to 1.5h
  [Cancel one of these jobs]
  [Ignore conflict]  -- Proceed with overlap (not recommended)
```

**Prevention:** During drag-and-drop, visual indicator shows if dropping a card would create a conflict (red border flash on conflicting card).

---

### 5.7: Invitation Edge Cases

**Invited cleaner never accepts:**
- After 7 days: Token expires
- Owner sees: "Carlos Lima -- Invitation expired (sent 8 days ago)" with `[Resend]` button
- Resend creates new 7-day token

**Invited person already has an account:**
- On clicking invitation link: "You already have a CleanClaw account. Sign in to accept this invitation."
- After sign-in: Cleaner role added to existing account. Existing owner/homeowner role preserved (multi-role).
- Role switcher becomes available in their UI

**Owner invites email that belongs to a homeowner:**
- Homeowner becomes multi-role (homeowner + cleaner)
- They can switch between views using role switcher
- All existing homeowner bookings and preferences preserved

---

### 5.8: Rate Limiting and Abuse Prevention

| Action | Rate Limit | Exceeded Behavior |
|--------|-----------|-------------------|
| Login attempts | 5 per 15 minutes | "Account locked for 30 minutes" |
| Password reset requests | 3 per hour | "Too many requests. Try again later." |
| Homeowner reschedules | Max per month (set by owner, default 2) | "You've reached the maximum reschedules this month. Contact your cleaner." |
| Homeowner cancellations | No hard limit, but fee escalation | 3rd cancellation in 30 days: "Frequent cancellations may result in service review" |
| Issue reports (cleaner) | 10 per day | Soft limit, owner notified if exceeded |
| SMS notifications | Plan limit per month | Beyond limit: Falls back to push + email only |

---

*CleanClaw User Flows v1.0 -- @ux-design-expert (Sati)*
*Traceability: All flows map to PRD v3.0 Epics 1-9, Wireframes v3 Sections 4-8, and Schema v3.*

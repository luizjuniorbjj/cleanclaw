-- ============================================
-- MIGRATION 011: CleanClaw — Cleaning Business Management Module
-- ClaWtoBusiness Ecosystem
-- ============================================
-- Adds 17 tables for end-to-end cleaning business operations:
-- services, bookings, recurring schedules, clients, team,
-- availability, checklists, job logs, invoices, reviews,
-- leads, service areas, pricing rules, notifications,
-- and daily analytics.
--
-- All tables scoped by business_id for multi-tenant isolation.
-- Safe to run on a live system (additive only, IF NOT EXISTS).
-- ============================================

-- ============================================
-- 1. CLEANING_SERVICES
-- ============================================
-- Service types offered by each cleaning business.
-- Examples: deep clean, regular, move-out, post-construction.
CREATE TABLE IF NOT EXISTS cleaning_services (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50) DEFAULT 'residential' CHECK (category IN (
        'residential', 'commercial', 'specialized', 'addon'
    )),
    base_price NUMERIC(10,2),                       -- base price in cents or dollars (app decides)
    price_unit VARCHAR(20) DEFAULT 'flat' CHECK (price_unit IN (
        'flat', 'hourly', 'per_sqft', 'per_room'
    )),
    estimated_duration_minutes INTEGER,              -- typical duration for scheduling
    min_team_size INTEGER DEFAULT 1,                 -- minimum cleaners needed
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,                    -- display ordering
    icon VARCHAR(50),                                -- emoji or icon identifier for UI
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(business_id, slug)
);

CREATE INDEX IF NOT EXISTS idx_cleaning_services_biz ON cleaning_services(business_id, is_active);

CREATE TRIGGER tr_cleaning_services_updated_at BEFORE UPDATE ON cleaning_services
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ============================================
-- 2. CLEANING_CLIENTS
-- ============================================
-- End customers who book cleaning services.
-- Separate from platform users — these are the cleaning business's own customers.
CREATE TABLE IF NOT EXISTS cleaning_clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,   -- optional link to platform user (if they chatted via AI)
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(30),
    phone_secondary VARCHAR(30),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    country VARCHAR(50) DEFAULT 'US',
    latitude NUMERIC(10,7),                                  -- for distance/routing calculations
    longitude NUMERIC(10,7),
    property_type VARCHAR(30) CHECK (property_type IN (
        'house', 'apartment', 'condo', 'townhouse', 'office', 'retail', 'other'
    )),
    bedrooms INTEGER,
    bathrooms NUMERIC(3,1),                                  -- 2.5 bathrooms
    square_feet INTEGER,
    has_pets BOOLEAN DEFAULT FALSE,
    pet_details VARCHAR(255),                                -- "2 dogs, 1 cat"
    access_instructions TEXT,                                -- gate code, key location, etc.
    preferred_day VARCHAR(15),                                -- "monday", "friday"
    preferred_time_start TIME,                               -- preferred window start
    preferred_time_end TIME,                                 -- preferred window end
    notes TEXT,                                              -- internal notes about this client
    source VARCHAR(30) DEFAULT 'manual' CHECK (source IN (
        'manual', 'ai_chat', 'booking_page', 'referral', 'import', 'lead_conversion'
    )),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN (
        'active', 'inactive', 'blocked'
    )),
    lifetime_value NUMERIC(12,2) DEFAULT 0.00,               -- total revenue from this client
    total_bookings INTEGER DEFAULT 0,
    last_service_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cleaning_clients_biz ON cleaning_clients(business_id, status);
CREATE INDEX IF NOT EXISTS idx_cleaning_clients_email ON cleaning_clients(business_id, email);
CREATE INDEX IF NOT EXISTS idx_cleaning_clients_phone ON cleaning_clients(business_id, phone);
CREATE INDEX IF NOT EXISTS idx_cleaning_clients_user ON cleaning_clients(user_id) WHERE user_id IS NOT NULL;

CREATE TRIGGER tr_cleaning_clients_updated_at BEFORE UPDATE ON cleaning_clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ============================================
-- 3. CLEANING_TEAM_MEMBERS
-- ============================================
-- Cleaners/employees who perform the work.
-- May or may not be platform users (user_id is optional).
CREATE TABLE IF NOT EXISTS cleaning_team_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,    -- optional platform user link
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(30),
    pin_hash VARCHAR(255),                                  -- hashed PIN for cleaner portal login (bcrypt)
    role VARCHAR(30) DEFAULT 'cleaner' CHECK (role IN (
        'cleaner', 'lead_cleaner', 'supervisor', 'manager'
    )),
    employment_type VARCHAR(20) DEFAULT 'employee' CHECK (employment_type IN (
        'employee', 'contractor', 'part_time'
    )),
    hourly_rate NUMERIC(8,2),                                -- pay rate
    color VARCHAR(7),                                        -- hex color for calendar UI (#FF5733)
    photo_url TEXT,
    certifications TEXT[],                                    -- ["insured", "bonded", "background_check"]
    max_daily_hours NUMERIC(4,1) DEFAULT 8.0,
    can_drive BOOLEAN DEFAULT TRUE,                          -- can travel to jobs independently
    home_zip VARCHAR(20),                                    -- for routing optimization
    notes TEXT,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN (
        'active', 'inactive', 'on_leave', 'terminated'
    )),
    hire_date DATE,
    termination_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cleaning_team_biz ON cleaning_team_members(business_id, status);

CREATE TRIGGER tr_cleaning_team_updated_at BEFORE UPDATE ON cleaning_team_members
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ============================================
-- 4. CLEANING_TEAM_AVAILABILITY
-- ============================================
-- Weekly recurring availability windows for each team member.
-- day_of_week: 0=Sunday, 6=Saturday (ISO convention).
CREATE TABLE IF NOT EXISTS cleaning_team_availability (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    team_member_id UUID NOT NULL REFERENCES cleaning_team_members(id) ON DELETE CASCADE,
    day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,                       -- false = blocked/off
    effective_from DATE DEFAULT CURRENT_DATE,                -- when this schedule starts
    effective_until DATE,                                    -- NULL = indefinite
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chk_time_range CHECK (start_time < end_time)
);

CREATE INDEX IF NOT EXISTS idx_cleaning_avail_member ON cleaning_team_availability(team_member_id, day_of_week);
CREATE INDEX IF NOT EXISTS idx_cleaning_avail_biz ON cleaning_team_availability(business_id);


-- ============================================
-- 5. CLEANING_RECURRING_SCHEDULES
-- ============================================
-- Defines recurring booking patterns (weekly, bi-weekly, monthly, custom).
-- Each occurrence generates a booking row via the scheduler.
CREATE TABLE IF NOT EXISTS cleaning_recurring_schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES cleaning_clients(id) ON DELETE CASCADE,
    service_id UUID NOT NULL REFERENCES cleaning_services(id) ON DELETE RESTRICT,
    frequency VARCHAR(20) NOT NULL CHECK (frequency IN (
        'weekly', 'biweekly', 'monthly', 'custom'
    )),
    custom_interval_days INTEGER,                            -- only used when frequency='custom'
    preferred_day_of_week SMALLINT CHECK (preferred_day_of_week BETWEEN 0 AND 6),
    preferred_time TIME,
    estimated_duration_minutes INTEGER,
    assigned_team JSONB DEFAULT '[]',                        -- array of team_member_id UUIDs
    notes TEXT,
    agreed_price NUMERIC(10,2),                              -- locked-in recurring price
    start_date DATE NOT NULL,
    end_date DATE,                                           -- NULL = ongoing
    next_occurrence DATE,                                    -- precomputed next booking date
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN (
        'active', 'paused', 'cancelled', 'completed'
    )),
    pause_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cleaning_recurring_biz ON cleaning_recurring_schedules(business_id, status);
CREATE INDEX IF NOT EXISTS idx_cleaning_recurring_client ON cleaning_recurring_schedules(client_id);
CREATE INDEX IF NOT EXISTS idx_cleaning_recurring_next ON cleaning_recurring_schedules(next_occurrence)
    WHERE status = 'active';

CREATE TRIGGER tr_cleaning_recurring_updated_at BEFORE UPDATE ON cleaning_recurring_schedules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ============================================
-- 6. CLEANING_BOOKINGS
-- ============================================
-- Individual booking/appointment records.
-- Can be standalone or generated from a recurring schedule.
CREATE TABLE IF NOT EXISTS cleaning_bookings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES cleaning_clients(id) ON DELETE RESTRICT,
    service_id UUID NOT NULL REFERENCES cleaning_services(id) ON DELETE RESTRICT,
    recurring_schedule_id UUID REFERENCES cleaning_recurring_schedules(id) ON DELETE SET NULL,
    -- Scheduling
    scheduled_date DATE NOT NULL,
    scheduled_start TIME NOT NULL,
    scheduled_end TIME,
    actual_start TIMESTAMPTZ,                                -- clock-in time
    actual_end TIMESTAMPTZ,                                  -- clock-out time
    estimated_duration_minutes INTEGER,
    -- Location (snapshot from client, can be overridden for one-off addresses)
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    latitude NUMERIC(10,7),
    longitude NUMERIC(10,7),
    access_instructions TEXT,
    -- Assignment
    assigned_team JSONB DEFAULT '[]',                        -- array of team_member_id UUIDs
    lead_cleaner_id UUID REFERENCES cleaning_team_members(id) ON DELETE SET NULL,
    -- Pricing
    quoted_price NUMERIC(10,2),                              -- price shown to customer
    final_price NUMERIC(10,2),                               -- actual charged amount (may differ after extras)
    discount_amount NUMERIC(10,2) DEFAULT 0.00,
    discount_reason VARCHAR(255),
    -- Status
    status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN (
        'draft', 'scheduled', 'confirmed', 'in_progress',
        'completed', 'cancelled', 'no_show', 'rescheduled'
    )),
    cancellation_reason TEXT,
    cancelled_at TIMESTAMPTZ,
    cancelled_by VARCHAR(20) CHECK (cancelled_by IN ('client', 'business', 'system')),
    -- Extras
    special_instructions TEXT,                               -- per-booking notes
    extras JSONB DEFAULT '[]',                               -- add-on services [{service_id, name, price}]
    source VARCHAR(30) DEFAULT 'manual' CHECK (source IN (
        'manual', 'ai_chat', 'booking_page', 'recurring', 'phone', 'referral'
    )),
    confirmation_sent BOOLEAN DEFAULT FALSE,
    reminder_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cleaning_bookings_biz ON cleaning_bookings(business_id, status);
CREATE INDEX IF NOT EXISTS idx_cleaning_bookings_date ON cleaning_bookings(business_id, scheduled_date);
CREATE INDEX IF NOT EXISTS idx_cleaning_bookings_client ON cleaning_bookings(client_id);
CREATE INDEX IF NOT EXISTS idx_cleaning_bookings_team ON cleaning_bookings(lead_cleaner_id)
    WHERE lead_cleaner_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_cleaning_bookings_recurring ON cleaning_bookings(recurring_schedule_id)
    WHERE recurring_schedule_id IS NOT NULL;
-- Composite index for calendar view: fetch all bookings for a business in a date range
CREATE INDEX IF NOT EXISTS idx_cleaning_bookings_calendar ON cleaning_bookings(business_id, scheduled_date, scheduled_start);

CREATE TRIGGER tr_cleaning_bookings_updated_at BEFORE UPDATE ON cleaning_bookings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ============================================
-- 7. CLEANING_CHECKLISTS
-- ============================================
-- Cleaning task checklists per service type.
-- Each service can have one default checklist; custom per-client is possible.
CREATE TABLE IF NOT EXISTS cleaning_checklists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    service_id UUID REFERENCES cleaning_services(id) ON DELETE SET NULL,     -- NULL = generic/reusable
    name VARCHAR(150) NOT NULL,
    description TEXT,
    is_default BOOLEAN DEFAULT FALSE,                        -- default checklist for this service
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cleaning_checklists_biz ON cleaning_checklists(business_id);
CREATE INDEX IF NOT EXISTS idx_cleaning_checklists_service ON cleaning_checklists(service_id)
    WHERE service_id IS NOT NULL;

CREATE TRIGGER tr_cleaning_checklists_updated_at BEFORE UPDATE ON cleaning_checklists
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ============================================
-- 8. CLEANING_CHECKLIST_ITEMS
-- ============================================
-- Individual items in a checklist.
CREATE TABLE IF NOT EXISTS cleaning_checklist_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    checklist_id UUID NOT NULL REFERENCES cleaning_checklists(id) ON DELETE CASCADE,
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    room VARCHAR(100),                                       -- "kitchen", "bathroom", "living_room"
    task_description VARCHAR(500) NOT NULL,                  -- "Wipe countertops", "Vacuum floors"
    is_required BOOLEAN DEFAULT TRUE,                        -- must-do vs optional
    sort_order INTEGER DEFAULT 0,
    estimated_minutes INTEGER,                               -- time estimate for this task
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cleaning_checklist_items_list ON cleaning_checklist_items(checklist_id, sort_order);


-- ============================================
-- 9. CLEANING_JOB_LOGS
-- ============================================
-- Clock-in/out, GPS data, photos, and notes per job.
-- Multiple log entries per booking (arrival, task completion, departure, etc.)
CREATE TABLE IF NOT EXISTS cleaning_job_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    booking_id UUID NOT NULL REFERENCES cleaning_bookings(id) ON DELETE CASCADE,
    team_member_id UUID REFERENCES cleaning_team_members(id) ON DELETE SET NULL,
    log_type VARCHAR(30) NOT NULL CHECK (log_type IN (
        'clock_in', 'clock_out', 'task_complete', 'photo',
        'note', 'issue', 'break_start', 'break_end'
    )),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    latitude NUMERIC(10,7),                                  -- GPS at time of log
    longitude NUMERIC(10,7),
    photo_url TEXT,                                          -- before/after photos
    checklist_item_id UUID REFERENCES cleaning_checklist_items(id) ON DELETE SET NULL,
    note TEXT,
    metadata JSONB DEFAULT '{}',                             -- extensible: device info, etc.
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cleaning_job_logs_booking ON cleaning_job_logs(booking_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_cleaning_job_logs_biz ON cleaning_job_logs(business_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_cleaning_job_logs_member ON cleaning_job_logs(team_member_id, timestamp DESC)
    WHERE team_member_id IS NOT NULL;


-- ============================================
-- 10. CLEANING_INVOICES
-- ============================================
-- Invoices generated from completed bookings.
CREATE TABLE IF NOT EXISTS cleaning_invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES cleaning_clients(id) ON DELETE RESTRICT,
    booking_id UUID REFERENCES cleaning_bookings(id) ON DELETE SET NULL,    -- can invoice without a specific booking
    invoice_number VARCHAR(50) NOT NULL,                     -- human-readable: "INV-2026-0001"
    -- Amounts
    subtotal NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    tax_rate NUMERIC(5,4) DEFAULT 0.0000,                    -- e.g. 0.0875 for 8.75%
    tax_amount NUMERIC(10,2) DEFAULT 0.00,
    discount_amount NUMERIC(10,2) DEFAULT 0.00,
    total NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    amount_paid NUMERIC(10,2) DEFAULT 0.00,
    balance_due NUMERIC(10,2) GENERATED ALWAYS AS (total - amount_paid) STORED,
    -- Dates
    issue_date DATE NOT NULL DEFAULT CURRENT_DATE,
    due_date DATE NOT NULL,
    paid_at TIMESTAMPTZ,
    -- Status
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN (
        'draft', 'sent', 'viewed', 'paid', 'partial', 'overdue', 'void', 'refunded'
    )),
    payment_method VARCHAR(30),                              -- "stripe", "cash", "check", "zelle", "venmo"
    payment_reference VARCHAR(255),                          -- transaction id, check number, etc.
    notes TEXT,                                              -- invoice-level notes visible to client
    internal_notes TEXT,                                     -- not visible to client
    stripe_invoice_id VARCHAR(100),                          -- if paid via Stripe
    pdf_url TEXT,                                            -- generated PDF storage
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(business_id, invoice_number)
);

CREATE INDEX IF NOT EXISTS idx_cleaning_invoices_biz ON cleaning_invoices(business_id, status);
CREATE INDEX IF NOT EXISTS idx_cleaning_invoices_client ON cleaning_invoices(client_id);
CREATE INDEX IF NOT EXISTS idx_cleaning_invoices_due ON cleaning_invoices(due_date)
    WHERE status IN ('sent', 'viewed', 'partial');
CREATE INDEX IF NOT EXISTS idx_cleaning_invoices_booking ON cleaning_invoices(booking_id)
    WHERE booking_id IS NOT NULL;

CREATE TRIGGER tr_cleaning_invoices_updated_at BEFORE UPDATE ON cleaning_invoices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ============================================
-- 11. CLEANING_INVOICE_ITEMS
-- ============================================
-- Line items on invoices.
CREATE TABLE IF NOT EXISTS cleaning_invoice_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id UUID NOT NULL REFERENCES cleaning_invoices(id) ON DELETE CASCADE,
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    service_id UUID REFERENCES cleaning_services(id) ON DELETE SET NULL,
    description VARCHAR(500) NOT NULL,                       -- "Deep Clean - 3BR/2BA"
    quantity NUMERIC(8,2) DEFAULT 1.00,
    unit_price NUMERIC(10,2) NOT NULL,
    total NUMERIC(10,2) NOT NULL,                            -- quantity * unit_price
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cleaning_invoice_items_inv ON cleaning_invoice_items(invoice_id);


-- ============================================
-- 12. CLEANING_REVIEWS
-- ============================================
-- Client reviews/ratings after service completion.
CREATE TABLE IF NOT EXISTS cleaning_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES cleaning_clients(id) ON DELETE CASCADE,
    booking_id UUID REFERENCES cleaning_bookings(id) ON DELETE SET NULL,
    rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    -- Detailed ratings (optional)
    quality_rating SMALLINT CHECK (quality_rating BETWEEN 1 AND 5),
    punctuality_rating SMALLINT CHECK (punctuality_rating BETWEEN 1 AND 5),
    communication_rating SMALLINT CHECK (communication_rating BETWEEN 1 AND 5),
    value_rating SMALLINT CHECK (value_rating BETWEEN 1 AND 5),
    -- Response
    business_response TEXT,                                  -- owner reply
    responded_at TIMESTAMPTZ,
    -- Display
    is_public BOOLEAN DEFAULT TRUE,                          -- visible on booking page / site
    is_verified BOOLEAN DEFAULT FALSE,                       -- verified completed booking
    source VARCHAR(20) DEFAULT 'internal' CHECK (source IN (
        'internal', 'google', 'yelp', 'thumbtack', 'manual'
    )),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cleaning_reviews_biz ON cleaning_reviews(business_id, is_public);
CREATE INDEX IF NOT EXISTS idx_cleaning_reviews_client ON cleaning_reviews(client_id);
CREATE INDEX IF NOT EXISTS idx_cleaning_reviews_rating ON cleaning_reviews(business_id, rating);

CREATE TRIGGER tr_cleaning_reviews_updated_at BEFORE UPDATE ON cleaning_reviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ============================================
-- 13. CLEANING_LEADS
-- ============================================
-- Leads from AI chat, booking page, referrals, etc.
-- Distinct from platform leads — these are cleaning-business-specific.
CREATE TABLE IF NOT EXISTS cleaning_leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    client_id UUID REFERENCES cleaning_clients(id) ON DELETE SET NULL,       -- set when lead converts
    -- Contact info
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(30),
    -- Property info (captured during lead)
    address VARCHAR(500),
    city VARCHAR(100),
    zip_code VARCHAR(20),
    property_type VARCHAR(30),
    bedrooms INTEGER,
    bathrooms NUMERIC(3,1),
    square_feet INTEGER,
    has_pets BOOLEAN,
    -- Request
    service_requested VARCHAR(150),                          -- "deep clean", "move-out"
    preferred_date DATE,
    preferred_time VARCHAR(50),                              -- "morning", "afternoon", "9am-12pm"
    message TEXT,                                            -- free-form message from lead
    estimated_quote NUMERIC(10,2),                           -- AI-generated or manual estimate
    -- Tracking
    source VARCHAR(30) DEFAULT 'website' CHECK (source IN (
        'website', 'ai_chat', 'phone', 'referral', 'google_ads',
        'facebook', 'thumbtack', 'yelp', 'nextdoor', 'import', 'other'
    )),
    utm_source VARCHAR(100),
    utm_medium VARCHAR(100),
    utm_campaign VARCHAR(100),
    referral_source VARCHAR(255),                            -- who referred them
    -- Pipeline
    status VARCHAR(20) DEFAULT 'new' CHECK (status IN (
        'new', 'contacted', 'quoted', 'follow_up',
        'won', 'lost', 'disqualified'
    )),
    temperature VARCHAR(10) DEFAULT 'warm' CHECK (temperature IN (
        'hot', 'warm', 'cold'
    )),
    lost_reason VARCHAR(255),
    follow_up_date DATE,
    follow_up_note TEXT,
    assigned_to UUID REFERENCES cleaning_team_members(id) ON DELETE SET NULL,
    -- Conversion
    converted_at TIMESTAMPTZ,
    conversion_booking_id UUID REFERENCES cleaning_bookings(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cleaning_leads_biz ON cleaning_leads(business_id, status);
CREATE INDEX IF NOT EXISTS idx_cleaning_leads_email ON cleaning_leads(business_id, email);
CREATE INDEX IF NOT EXISTS idx_cleaning_leads_phone ON cleaning_leads(business_id, phone);
CREATE INDEX IF NOT EXISTS idx_cleaning_leads_followup ON cleaning_leads(follow_up_date)
    WHERE status IN ('contacted', 'quoted', 'follow_up');
CREATE INDEX IF NOT EXISTS idx_cleaning_leads_source ON cleaning_leads(business_id, source);

CREATE TRIGGER tr_cleaning_leads_updated_at BEFORE UPDATE ON cleaning_leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ============================================
-- 14. CLEANING_AREAS
-- ============================================
-- Service areas/zones the business covers.
-- Used for lead qualification and routing.
CREATE TABLE IF NOT EXISTS cleaning_areas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,                              -- "Downtown Austin", "North Side"
    zip_codes TEXT[] DEFAULT '{}',                            -- list of covered zip codes
    city VARCHAR(100),
    state VARCHAR(50),
    radius_miles NUMERIC(6,1),                               -- service radius from center point
    center_latitude NUMERIC(10,7),
    center_longitude NUMERIC(10,7),
    travel_fee NUMERIC(8,2) DEFAULT 0.00,                    -- extra fee for this zone
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,                              -- higher = preferred area
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cleaning_areas_biz ON cleaning_areas(business_id, is_active);

CREATE TRIGGER tr_cleaning_areas_updated_at BEFORE UPDATE ON cleaning_areas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ============================================
-- 15. CLEANING_PRICING_RULES
-- ============================================
-- Pricing logic: base prices, multipliers, extras, discounts.
-- Evaluated in priority order to compute final price.
CREATE TABLE IF NOT EXISTS cleaning_pricing_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    service_id UUID REFERENCES cleaning_services(id) ON DELETE CASCADE,      -- NULL = applies to all services
    name VARCHAR(150) NOT NULL,                              -- "Pet Surcharge", "Weekend Premium"
    rule_type VARCHAR(30) NOT NULL CHECK (rule_type IN (
        'base_price',          -- base price for a service configuration
        'addon',               -- flat add-on fee (e.g., inside fridge +$30)
        'multiplier',          -- percentage multiplier (e.g., deep clean 1.5x)
        'surcharge',           -- conditional flat fee (e.g., pets +$25)
        'discount',            -- percentage or flat discount
        'minimum'              -- minimum charge threshold
    )),
    -- Conditions (JSONB for flexibility)
    -- Examples:
    --   {"bedrooms_gte": 4}
    --   {"has_pets": true}
    --   {"day_of_week": [0, 6]}  (weekends)
    --   {"frequency": "weekly"}  (recurring discount)
    --   {"square_feet_gte": 3000}
    conditions JSONB DEFAULT '{}',
    -- Value
    amount NUMERIC(10,2),                                    -- flat amount (for addon, surcharge, base, minimum)
    percentage NUMERIC(5,2),                                 -- percentage (for multiplier, discount)
    -- Control
    priority INTEGER DEFAULT 0,                              -- evaluation order (lower = first)
    is_active BOOLEAN DEFAULT TRUE,
    valid_from DATE,
    valid_until DATE,                                        -- NULL = no expiry (promotions use this)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cleaning_pricing_biz ON cleaning_pricing_rules(business_id, is_active);
CREATE INDEX IF NOT EXISTS idx_cleaning_pricing_service ON cleaning_pricing_rules(service_id)
    WHERE service_id IS NOT NULL;

CREATE TRIGGER tr_cleaning_pricing_updated_at BEFORE UPDATE ON cleaning_pricing_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ============================================
-- 16. CLEANING_NOTIFICATIONS
-- ============================================
-- Outbound notifications (SMS, WhatsApp, email, push) to clients, cleaners, and owners.
-- Tracks delivery status, cost, and retries for all notification channels.
CREATE TABLE IF NOT EXISTS cleaning_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('sms', 'whatsapp', 'email', 'push')),
    provider VARCHAR(30),                                      -- 'twilio', 'evolution_api', 'vapid', 'smtp'
    target_type VARCHAR(20) NOT NULL CHECK (target_type IN ('client', 'cleaner', 'owner')),
    target_id UUID NOT NULL,                                   -- references cleaning_clients.id, cleaning_team_members.id, or users.id
    phone_number VARCHAR(20),                                  -- destination phone (SMS/WhatsApp)
    email_address VARCHAR(255),                                -- destination email
    template_key VARCHAR(100) NOT NULL,                        -- e.g. 'booking_confirmation', 'reminder_24h', 'job_completed'
    payload_json JSONB DEFAULT '{}',                           -- template variables: {client_name, date, time, address, ...}
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'sent', 'delivered', 'failed', 'bounced'
    )),
    cost DECIMAL(10,4) DEFAULT 0,                              -- per-message cost (e.g. $0.0079 for Twilio SMS)
    retry_count INTEGER DEFAULT 0,
    sent_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cleaning_notifications_biz_status ON cleaning_notifications(business_id, status);
CREATE INDEX IF NOT EXISTS idx_cleaning_notifications_channel ON cleaning_notifications(business_id, channel, created_at);
CREATE INDEX IF NOT EXISTS idx_cleaning_notifications_target ON cleaning_notifications(target_id);


-- ============================================
-- 17. CLEANING_DAILY_ANALYTICS
-- ============================================
-- Pre-aggregated daily metrics for dashboard performance.
-- One row per business per day. Updated by a scheduled job or on-demand.
CREATE TABLE IF NOT EXISTS cleaning_daily_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    total_bookings INTEGER DEFAULT 0,
    completed_bookings INTEGER DEFAULT 0,
    cancelled_bookings INTEGER DEFAULT 0,
    revenue DECIMAL(12,2) DEFAULT 0,
    new_leads INTEGER DEFAULT 0,
    converted_leads INTEGER DEFAULT 0,
    new_clients INTEGER DEFAULT 0,
    sms_sent INTEGER DEFAULT 0,
    sms_cost DECIMAL(10,4) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(business_id, date)
);

CREATE TRIGGER tr_cleaning_daily_analytics_updated_at BEFORE UPDATE ON cleaning_daily_analytics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================
-- SMS QUOTA TIERS (enforced in service layer)
-- ============================================
-- Tier limits for monthly SMS/notification quota:
--   Starter  = 100 SMS/month
--   Pro      = 500 SMS/month
--   Business = 2000 SMS/month
-- Enforcement is done in app/modules/cleaning/notification_service.py
-- by checking business subscription tier against monthly send count.
-- The cleaning_notifications table tracks all sends for quota calculation.


-- ============================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================
-- Enforce multi-tenant isolation at the database level.
-- All cleaning tables are protected so that queries MUST
-- include a business_id filter matching the authenticated context.

-- Enable RLS on all cleaning tables
ALTER TABLE cleaning_services ENABLE ROW LEVEL SECURITY;
ALTER TABLE cleaning_clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE cleaning_team_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE cleaning_team_availability ENABLE ROW LEVEL SECURITY;
ALTER TABLE cleaning_recurring_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE cleaning_bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE cleaning_checklists ENABLE ROW LEVEL SECURITY;
ALTER TABLE cleaning_checklist_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE cleaning_job_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE cleaning_invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE cleaning_invoice_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE cleaning_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE cleaning_leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE cleaning_areas ENABLE ROW LEVEL SECURITY;
ALTER TABLE cleaning_pricing_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE cleaning_notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE cleaning_daily_analytics ENABLE ROW LEVEL SECURITY;

-- RLS Policies: business_id isolation
-- The application sets current_setting('app.current_business_id') on each request.
-- Superusers (the app service role) bypass RLS by default.
-- These policies protect against accidental cross-business data access.

CREATE POLICY cleaning_services_isolation ON cleaning_services
    USING (business_id::text = current_setting('app.current_business_id', true));

CREATE POLICY cleaning_clients_isolation ON cleaning_clients
    USING (business_id::text = current_setting('app.current_business_id', true));

CREATE POLICY cleaning_team_members_isolation ON cleaning_team_members
    USING (business_id::text = current_setting('app.current_business_id', true));

CREATE POLICY cleaning_team_availability_isolation ON cleaning_team_availability
    USING (business_id::text = current_setting('app.current_business_id', true));

CREATE POLICY cleaning_recurring_schedules_isolation ON cleaning_recurring_schedules
    USING (business_id::text = current_setting('app.current_business_id', true));

CREATE POLICY cleaning_bookings_isolation ON cleaning_bookings
    USING (business_id::text = current_setting('app.current_business_id', true));

CREATE POLICY cleaning_checklists_isolation ON cleaning_checklists
    USING (business_id::text = current_setting('app.current_business_id', true));

CREATE POLICY cleaning_checklist_items_isolation ON cleaning_checklist_items
    USING (business_id::text = current_setting('app.current_business_id', true));

CREATE POLICY cleaning_job_logs_isolation ON cleaning_job_logs
    USING (business_id::text = current_setting('app.current_business_id', true));

CREATE POLICY cleaning_invoices_isolation ON cleaning_invoices
    USING (business_id::text = current_setting('app.current_business_id', true));

CREATE POLICY cleaning_invoice_items_isolation ON cleaning_invoice_items
    USING (business_id::text = current_setting('app.current_business_id', true));

CREATE POLICY cleaning_reviews_isolation ON cleaning_reviews
    USING (business_id::text = current_setting('app.current_business_id', true));

CREATE POLICY cleaning_leads_isolation ON cleaning_leads
    USING (business_id::text = current_setting('app.current_business_id', true));

CREATE POLICY cleaning_areas_isolation ON cleaning_areas
    USING (business_id::text = current_setting('app.current_business_id', true));

CREATE POLICY cleaning_pricing_rules_isolation ON cleaning_pricing_rules
    USING (business_id::text = current_setting('app.current_business_id', true));

CREATE POLICY cleaning_notifications_isolation ON cleaning_notifications
    USING (business_id::text = current_setting('app.current_business_id', true));

CREATE POLICY cleaning_daily_analytics_isolation ON cleaning_daily_analytics
    USING (business_id::text = current_setting('app.current_business_id', true));


-- ============================================
-- VIEWS — Dashboard Queries
-- ============================================

-- Revenue summary per business (monthly)
CREATE OR REPLACE VIEW v_cleaning_revenue_monthly AS
SELECT
    b.business_id,
    DATE_TRUNC('month', b.scheduled_date) AS month,
    COUNT(*) FILTER (WHERE b.status = 'completed') AS completed_jobs,
    COUNT(*) FILTER (WHERE b.status = 'cancelled') AS cancelled_jobs,
    COALESCE(SUM(b.final_price) FILTER (WHERE b.status = 'completed'), 0) AS revenue,
    COALESCE(AVG(b.final_price) FILTER (WHERE b.status = 'completed'), 0) AS avg_ticket
FROM cleaning_bookings b
GROUP BY b.business_id, DATE_TRUNC('month', b.scheduled_date);

-- Today's schedule for a business
CREATE OR REPLACE VIEW v_cleaning_today_schedule AS
SELECT
    b.id AS booking_id,
    b.business_id,
    b.scheduled_start,
    b.scheduled_end,
    b.status,
    c.first_name || ' ' || COALESCE(c.last_name, '') AS client_name,
    c.address_line1 AS client_address,
    c.city AS client_city,
    s.name AS service_name,
    b.quoted_price,
    b.assigned_team,
    b.lead_cleaner_id
FROM cleaning_bookings b
JOIN cleaning_clients c ON c.id = b.client_id
JOIN cleaning_services s ON s.id = b.service_id
WHERE b.scheduled_date = CURRENT_DATE
  AND b.status NOT IN ('cancelled', 'no_show');

-- Lead pipeline summary
CREATE OR REPLACE VIEW v_cleaning_lead_pipeline AS
SELECT
    business_id,
    status,
    temperature,
    source,
    COUNT(*) AS lead_count,
    MIN(created_at) AS oldest_lead,
    MAX(created_at) AS newest_lead
FROM cleaning_leads
GROUP BY business_id, status, temperature, source;

-- Team member performance (last 30 days)
CREATE OR REPLACE VIEW v_cleaning_team_performance AS
SELECT
    tm.business_id,
    tm.id AS team_member_id,
    tm.first_name || ' ' || COALESCE(tm.last_name, '') AS member_name,
    COUNT(DISTINCT b.id) AS jobs_completed,
    COALESCE(AVG(r.rating), 0) AS avg_rating,
    COUNT(DISTINCT r.id) AS review_count,
    COALESCE(SUM(
        EXTRACT(EPOCH FROM (b.actual_end - b.actual_start)) / 3600
    ), 0) AS total_hours
FROM cleaning_team_members tm
LEFT JOIN cleaning_bookings b ON b.lead_cleaner_id = tm.id
    AND b.status = 'completed'
    AND b.scheduled_date >= CURRENT_DATE - INTERVAL '30 days'
LEFT JOIN cleaning_reviews r ON r.booking_id = b.id
WHERE tm.status = 'active'
GROUP BY tm.business_id, tm.id, tm.first_name, tm.last_name;

-- Invoice aging report
CREATE OR REPLACE VIEW v_cleaning_invoice_aging AS
SELECT
    business_id,
    COUNT(*) FILTER (WHERE balance_due > 0 AND due_date >= CURRENT_DATE) AS current_count,
    COALESCE(SUM(balance_due) FILTER (WHERE balance_due > 0 AND due_date >= CURRENT_DATE), 0) AS current_amount,
    COUNT(*) FILTER (WHERE balance_due > 0 AND due_date < CURRENT_DATE AND due_date >= CURRENT_DATE - 30) AS overdue_30_count,
    COALESCE(SUM(balance_due) FILTER (WHERE balance_due > 0 AND due_date < CURRENT_DATE AND due_date >= CURRENT_DATE - 30), 0) AS overdue_30_amount,
    COUNT(*) FILTER (WHERE balance_due > 0 AND due_date < CURRENT_DATE - 30 AND due_date >= CURRENT_DATE - 60) AS overdue_60_count,
    COALESCE(SUM(balance_due) FILTER (WHERE balance_due > 0 AND due_date < CURRENT_DATE - 30 AND due_date >= CURRENT_DATE - 60), 0) AS overdue_60_amount,
    COUNT(*) FILTER (WHERE balance_due > 0 AND due_date < CURRENT_DATE - 60) AS overdue_90_plus_count,
    COALESCE(SUM(balance_due) FILTER (WHERE balance_due > 0 AND due_date < CURRENT_DATE - 60), 0) AS overdue_90_plus_amount
FROM cleaning_invoices
WHERE status NOT IN ('void', 'refunded', 'draft')
GROUP BY business_id;

-- Client lifetime value leaderboard
CREATE OR REPLACE VIEW v_cleaning_client_ltv AS
SELECT
    c.business_id,
    c.id AS client_id,
    c.first_name || ' ' || COALESCE(c.last_name, '') AS client_name,
    c.total_bookings,
    c.lifetime_value,
    c.last_service_date,
    COALESCE(AVG(r.rating), 0) AS avg_given_rating,
    rs.frequency AS recurring_frequency,
    rs.status AS recurring_status
FROM cleaning_clients c
LEFT JOIN cleaning_reviews r ON r.client_id = c.id
LEFT JOIN cleaning_recurring_schedules rs ON rs.client_id = c.id AND rs.status = 'active'
WHERE c.status = 'active'
GROUP BY c.business_id, c.id, c.first_name, c.last_name, c.total_bookings,
         c.lifetime_value, c.last_service_date, rs.frequency, rs.status;

-- Notification stats by channel/month — sent, failed, total cost
CREATE OR REPLACE VIEW v_cleaning_notification_stats AS
SELECT
    n.business_id,
    DATE_TRUNC('month', n.created_at) AS month,
    n.channel,
    COUNT(*) AS total_notifications,
    COUNT(*) FILTER (WHERE n.status = 'sent') AS sent_count,
    COUNT(*) FILTER (WHERE n.status = 'delivered') AS delivered_count,
    COUNT(*) FILTER (WHERE n.status = 'failed') AS failed_count,
    COUNT(*) FILTER (WHERE n.status = 'bounced') AS bounced_count,
    COALESCE(SUM(n.cost), 0) AS total_cost
FROM cleaning_notifications n
GROUP BY n.business_id, DATE_TRUNC('month', n.created_at), n.channel;


-- ============================================
-- SEED DATA — Standard Residential Cleaning Services
-- ============================================
-- These are inserted as templates with a NULL business_id.
-- The application copies them into a business when onboarding a cleaning business.
-- Using a dedicated seed table to avoid polluting the main table with NULL business_ids.

CREATE TABLE IF NOT EXISTS cleaning_service_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(150) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    category VARCHAR(50) DEFAULT 'residential',
    suggested_base_price NUMERIC(10,2),
    price_unit VARCHAR(20) DEFAULT 'flat',
    estimated_duration_minutes INTEGER,
    min_team_size INTEGER DEFAULT 1,
    icon VARCHAR(50),
    sort_order INTEGER DEFAULT 0
);

INSERT INTO cleaning_service_templates (name, slug, description, category, suggested_base_price, price_unit, estimated_duration_minutes, min_team_size, icon, sort_order)
VALUES
    ('Standard Clean', 'standard-clean',
     'Regular maintenance cleaning including dusting, vacuuming, mopping, kitchen and bathroom cleaning.',
     'residential', 150.00, 'flat', 120, 1, 'broom', 1),

    ('Deep Clean', 'deep-clean',
     'Thorough top-to-bottom cleaning including baseboards, inside cabinets, behind appliances, detailed scrubbing.',
     'residential', 250.00, 'flat', 240, 2, 'sparkles', 2),

    ('Move-In / Move-Out Clean', 'move-in-out',
     'Complete cleaning for vacant properties. Inside all cabinets, appliances, closets, fixtures, and detailed floor care.',
     'residential', 300.00, 'flat', 300, 2, 'truck', 3),

    ('Post-Construction Clean', 'post-construction',
     'Heavy-duty cleaning after renovation or construction. Dust removal, debris cleanup, surface polishing, window cleaning.',
     'specialized', 400.00, 'flat', 360, 2, 'hammer', 4),

    ('Office / Commercial Clean', 'office-commercial',
     'Workspace cleaning including desks, common areas, restrooms, break rooms, and floor care.',
     'commercial', 200.00, 'flat', 180, 2, 'building', 5),

    ('Carpet Cleaning', 'carpet-cleaning',
     'Professional carpet shampooing and steam cleaning. Price per room.',
     'specialized', 75.00, 'per_room', 45, 1, 'rug', 6),

    ('Window Cleaning', 'window-cleaning',
     'Interior and exterior window cleaning including tracks and sills.',
     'addon', 10.00, 'per_sqft', 60, 1, 'window', 7),

    ('Laundry Service', 'laundry-service',
     'Wash, dry, fold laundry. Includes linens and towels.',
     'addon', 40.00, 'flat', 60, 1, 'shirt', 8),

    ('Refrigerator Deep Clean', 'fridge-clean',
     'Complete interior and exterior refrigerator cleaning, shelf removal, sanitizing.',
     'addon', 35.00, 'flat', 30, 1, 'fridge', 9),

    ('Oven Deep Clean', 'oven-clean',
     'Interior and exterior oven cleaning, rack removal, degreasing.',
     'addon', 30.00, 'flat', 30, 1, 'oven', 10),

    ('Garage Cleaning', 'garage-clean',
     'Sweep, organize, and clean garage floors and surfaces.',
     'addon', 75.00, 'flat', 90, 1, 'garage', 11),

    ('Airbnb / Short-Term Rental', 'airbnb-turnover',
     'Quick turnaround cleaning between guests. Linen change, restock supplies, detailed bathroom/kitchen.',
     'residential', 120.00, 'flat', 90, 1, 'key', 12)
ON CONFLICT (slug) DO NOTHING;


-- ============================================
-- SEED DATA — Default Checklist Template
-- ============================================

-- We insert a reusable checklist template. The application copies
-- it for each new cleaning business during onboarding.
-- Using a template table to keep seeds clean.

CREATE TABLE IF NOT EXISTS cleaning_checklist_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_slug VARCHAR(100) NOT NULL,                      -- matches cleaning_service_templates.slug
    room VARCHAR(100),
    task_description VARCHAR(500) NOT NULL,
    is_required BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0
);

INSERT INTO cleaning_checklist_templates (service_slug, room, task_description, is_required, sort_order)
VALUES
    -- Standard Clean checklist
    ('standard-clean', 'Kitchen', 'Wipe countertops and backsplash', true, 1),
    ('standard-clean', 'Kitchen', 'Clean stovetop and exterior of appliances', true, 2),
    ('standard-clean', 'Kitchen', 'Clean and sanitize sink', true, 3),
    ('standard-clean', 'Kitchen', 'Empty trash and replace liner', true, 4),
    ('standard-clean', 'Kitchen', 'Sweep and mop floors', true, 5),
    ('standard-clean', 'Bathrooms', 'Clean and sanitize toilet (inside and out)', true, 6),
    ('standard-clean', 'Bathrooms', 'Clean shower/tub surfaces', true, 7),
    ('standard-clean', 'Bathrooms', 'Clean mirrors and glass', true, 8),
    ('standard-clean', 'Bathrooms', 'Wipe counters and sink', true, 9),
    ('standard-clean', 'Bathrooms', 'Sweep and mop floors', true, 10),
    ('standard-clean', 'Bedrooms', 'Make beds and straighten linens', true, 11),
    ('standard-clean', 'Bedrooms', 'Dust all surfaces and furniture', true, 12),
    ('standard-clean', 'Bedrooms', 'Vacuum floors and rugs', true, 13),
    ('standard-clean', 'Living Areas', 'Dust furniture, shelves, and decor', true, 14),
    ('standard-clean', 'Living Areas', 'Vacuum carpets and rugs', true, 15),
    ('standard-clean', 'Living Areas', 'Mop hard floors', true, 16),
    ('standard-clean', 'All Rooms', 'Empty all trash cans', true, 17),
    ('standard-clean', 'All Rooms', 'Dust ceiling fan blades (reachable)', false, 18),
    ('standard-clean', 'All Rooms', 'Wipe light switches and door handles', true, 19),
    -- Deep Clean additions
    ('deep-clean', 'Kitchen', 'Clean inside microwave', true, 1),
    ('deep-clean', 'Kitchen', 'Clean inside oven (exterior included)', true, 2),
    ('deep-clean', 'Kitchen', 'Wipe cabinet fronts and handles', true, 3),
    ('deep-clean', 'Kitchen', 'Clean behind and under movable appliances', true, 4),
    ('deep-clean', 'Bathrooms', 'Scrub tile grout', true, 5),
    ('deep-clean', 'Bathrooms', 'Clean exhaust fan cover', true, 6),
    ('deep-clean', 'Bathrooms', 'Descale faucets and showerheads', true, 7),
    ('deep-clean', 'All Rooms', 'Clean baseboards throughout', true, 8),
    ('deep-clean', 'All Rooms', 'Clean window sills and tracks', true, 9),
    ('deep-clean', 'All Rooms', 'Dust blinds/shutters', true, 10),
    ('deep-clean', 'All Rooms', 'Clean interior doors and frames', true, 11),
    ('deep-clean', 'All Rooms', 'Clean air vents and registers', true, 12)
ON CONFLICT DO NOTHING;

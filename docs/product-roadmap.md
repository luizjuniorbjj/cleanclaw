# CleanClaw Product Roadmap

> **Status:** Draft v1.0
> **Author:** @pm (Trinity)
> **Date:** 2026-03-23
> **First Client:** Clean New Orleans
> **MVP Status:** 91 API endpoints, 20 screens, 23 DB tables

---

## 1. Product Vision

**One-liner:** "The Shopify of cleaning businesses."

**Problem:** Cleaning business owners with 100+ residential clients and multiple teams spend 2-3 hours daily on manual scheduling, rescheduling, payment tracking, and team coordination -- work that generates zero revenue. Existing tools are either generic (Google Calendar, spreadsheets) or overpriced enterprise software built for janitorial corporations, not local residential cleaning companies. There is no affordable, purpose-built platform that handles the full operations lifecycle from scheduling to payment collection for the $90B residential cleaning market.

**Why now:** Three forces are converging. First, the residential cleaning industry is experiencing rapid professionalization post-COVID, with clients expecting digital booking, automated reminders, and online payments as standard. Second, AI scheduling optimization is now accessible at consumer price points, enabling a solo operator to manage capacity like a 50-person operation. Third, the fragmentation is extreme -- there are 1.2M cleaning businesses in the US alone, 95% using manual processes, creating a massive greenfield opportunity for a vertical SaaS play.

---

## 2. Pricing Strategy

### Tier Comparison

| Feature | Basic ($29/mo) | Pro ($49/mo) | Business ($99/mo) |
|---------|:-:|:-:|:-:|
| **Schedule management** | Manual | AI-assisted | Full AI auto |
| **Teams** | 1 team | 3 teams | Unlimited |
| **Clients** | 50 | 200 | Unlimited |
| **Client portal** | No | Yes | Yes |
| **Invoicing** | Basic (manual) | Auto-generate | Auto + Stripe payments |
| **SMS/Email notifications** | Email only | Email + SMS | All channels |
| **Reports** | Basic (weekly) | Advanced (daily + trends) | Custom + export |
| **WhatsApp integration** | No | No | Yes |
| **AI scheduling** | No | Yes | Yes |
| **Recurring schedules** | Yes | Yes | Yes |
| **Team check-in/check-out** | Yes | Yes | Yes + GPS |
| **Marketing site** | No | No | Yes (full ClaWtoBusiness site) |
| **AI chat for lead capture** | No | No | Yes |
| **Dedicated support** | Email (48h) | Email + Chat (24h) | Phone + Chat (4h) |

### Notification Channels by Tier

| Channel | Basic | Pro | Business |
|---------|-------|-----|----------|
| Email | Yes | Yes | Yes |
| Push | Yes | Yes | Yes |
| SMS | No | Yes (500/mo) | Yes (unlimited) |
| WhatsApp | No | No | Yes |

### Revenue Model

- **ARPU target:** $55/mo (weighted average across tiers)
- **Annual discount:** 20% off (2 months free)
- **Upsell path:** Basic -> Pro is natural at ~80 clients; Pro -> Business when wanting online payments and marketing site

### Free Trial

- **Duration:** 14 days, all Pro features unlocked
- **No credit card required** -- reduce friction to zero
- **Onboarding wizard:** Pre-loads sample data (3 teams, 15 clients, 1 week of schedules) so the owner sees value in under 2 minutes
- **Trial-to-paid trigger:** SMS notification at day 10 with usage summary ("You scheduled 47 jobs this week -- keep going?")

---

## 3. Launch Phases

### Phase 1: MVP Launch (Week 1-2) -- P0

**Goal:** Validate product-market fit with one real business.

| Deliverable | Details |
|-------------|---------|
| Beta deployment | Clean New Orleans on production environment |
| Core features live | Schedule, Teams, Clients, Invoices (manual) |
| Bug triage process | Daily feedback channel (WhatsApp group with owner) |
| Performance baseline | < 2s load time on mobile, 99.5% uptime |
| PWA install flow | Add-to-homescreen prompt on first visit |

**Exit criteria:** Clean New Orleans uses the app daily for 2 consecutive weeks with no critical bugs.

### Phase 2: Client Portal + Payments (Week 3-4) -- P0

**Goal:** Enable homeowners to self-serve and pay online.

| Deliverable | Details |
|-------------|---------|
| Client login | Gmail OAuth + email/password (same app, role-based) |
| Booking flow | Homeowner can view schedule, request booking, reschedule, cancel |
| Online payment | Stripe integration -- pay per service or recurring |
| Automated confirmations | Email notification on booking/change/cancellation |
| Client dashboard | Upcoming appointments, payment history, house notes |

**Exit criteria:** 30% of Clean New Orleans clients create accounts within 2 weeks of launch.

### Phase 3: AI and Automation (Week 5-8) -- P1

**Goal:** Reduce owner's daily scheduling time from 2 hours to 15 minutes.

| Deliverable | Details |
|-------------|---------|
| AI schedule generation | One-click daily/weekly schedule based on recurring patterns, team availability, and proximity |
| Auto-invoicing | Invoice generated automatically when team marks job complete |
| Smart team assignment | Algorithm considers proximity (zip code clusters), team skills, and workload balance |
| Recurring schedule engine | Support weekly, biweekly, monthly, and custom frequencies with conflict detection |
| SMS notifications | Automated reminders to clients (24h before) and teams (morning of) |

**Exit criteria:** Owner reports 50%+ reduction in scheduling time; AI-generated schedules accepted without modification 70% of the time.

### Phase 4: Growth and Distribution (Week 9-12) -- P1

**Goal:** Acquire first 10 paying customers.

| Deliverable | Details |
|-------------|---------|
| Marketing site | cleanclaw.com -- landing page with demo video, pricing, signup |
| Referral program | Existing customer refers new business -> 1 month free for both |
| App store listing | PWA wrapper for Google Play and Apple App Store |
| Multi-language | English (primary), Spanish, Portuguese |
| Self-serve onboarding | New business can sign up, configure, and start using without human intervention |
| Content marketing | 5 blog posts targeting "cleaning business software" keywords |

**Exit criteria:** 10 active businesses, $500+ MRR.

---

## 4. Success Metrics (KPIs)

### 90-Day Targets

| Metric | Target | How We Measure |
|--------|--------|---------------|
| Active businesses | 10 | Businesses with >= 1 login in last 7 days |
| Monthly recurring revenue | $1,000 | Stripe MRR dashboard |
| Bookings managed/month | 2,000 | Total jobs scheduled across all businesses |
| Cleaner app adoption | 80% of teams | Teams that check in via app (vs. owner marking manually) |
| Client portal usage | 40% of clients | Clients with >= 1 login in last 30 days |
| Churn rate | < 5%/month | Businesses that cancel / total businesses |
| NPS | > 50 | In-app survey at day 30 |
| Time-to-value | < 5 min | Time from signup to first schedule created |
| Support tickets | < 3/business/month | Zendesk/email tracking |

### Leading Indicators (Weekly)

| Indicator | Signal |
|-----------|--------|
| Daily active businesses | Product stickiness |
| Jobs scheduled per business | Depth of usage |
| Client portal signups | Viral growth potential |
| AI schedule acceptance rate | AI value delivery |
| Feature request frequency | Product-market fit signal |

---

## 5. Epic Breakdown (90-Day Plan)

### Epic 1: Production Hardening -- P0

**Scope:** Stabilize MVP for real-world daily usage. Error handling, edge cases, data validation, mobile responsiveness audit.
**Effort:** 1 week
**Dependencies:** None
**Deliverables:** Zero critical bugs, < 2s load times, error logging/alerting

### Epic 2: Client Portal and Self-Service -- P0

**Scope:** Homeowner login, booking view, reschedule/cancel flow, house profile, appointment history.
**Effort:** 2 weeks
**Dependencies:** Epic 1
**Deliverables:** Client-facing screens (5), role-based routing, notification system

### Epic 3: Stripe Payment Integration -- P0

**Scope:** Online payment collection, invoice auto-generation on job completion, payment history, Stripe Connect for business payouts.
**Effort:** 2 weeks
**Dependencies:** Epic 2
**Deliverables:** Payment flow, webhook handlers, invoice PDF generation, payout dashboard

### Epic 4: Notification Engine -- P1

**Scope:** Email and SMS notifications for bookings, reminders, cancellations, payment confirmations. Configurable per business.
**Effort:** 1.5 weeks
**Dependencies:** Epic 2
**Deliverables:** Notification templates, SMS provider integration (Twilio), preference management

### Epic 5: AI Schedule Optimizer -- P1

**Scope:** One-click schedule generation using recurring patterns, team availability, proximity optimization. Manual override capability.
**Effort:** 3 weeks
**Dependencies:** Epic 1
**Deliverables:** Scheduling algorithm, suggestion UI, acceptance/rejection flow, learning from overrides

### Epic 6: Recurring Schedule Engine -- P1

**Scope:** Support weekly, biweekly, monthly, custom frequencies. Conflict detection, holiday handling, bulk reschedule.
**Effort:** 2 weeks
**Dependencies:** Epic 1
**Deliverables:** Recurrence rules engine, conflict resolver, calendar sync

### Epic 7: Reporting and Analytics -- P1

**Scope:** Business dashboard with revenue trends, team utilization, client retention, schedule fill rate. Export to CSV/PDF.
**Effort:** 1.5 weeks
**Dependencies:** Epic 3
**Deliverables:** Dashboard screens (3), report generation, data aggregation jobs

### Epic 8: Marketing Site and Self-Serve Onboarding -- P1

**Scope:** cleanclaw.com landing page, signup flow, onboarding wizard with sample data, pricing page, demo video.
**Effort:** 2 weeks
**Dependencies:** Epic 1
**Deliverables:** Marketing site, onboarding flow (5 steps), trial activation

### Epic 9: Multi-Language Support -- P2

**Scope:** i18n infrastructure, English/Spanish/Portuguese translations for all UI strings and notifications.
**Effort:** 1.5 weeks
**Dependencies:** Epic 4
**Deliverables:** Translation files, language selector, locale-aware formatting (dates, currency)

### Epic 10: App Store Distribution -- P2

**Scope:** PWA wrapper for Google Play (TWA) and Apple App Store. Push notification support. App store assets (screenshots, description, metadata).
**Effort:** 1.5 weeks
**Dependencies:** Epic 8
**Deliverables:** Store listings, push notification integration, install flow optimization

### Priority and Timeline Summary

```
Week  1-2:  [Epic 1: Production Hardening -------]
Week  2-4:  [Epic 2: Client Portal -------------------------]
Week  3-5:  [Epic 3: Stripe Payments -----------------------]
Week  4-5:  [Epic 4: Notification Engine ----------]
Week  3-6:  [Epic 5: AI Schedule Optimizer --------------------------------]
Week  5-7:  [Epic 6: Recurring Schedules -------------------]
Week  6-8:  [Epic 7: Reporting/Analytics ----------]
Week  7-9:  [Epic 8: Marketing Site + Onboarding ----------]
Week  9-10: [Epic 9: Multi-Language ----------]
Week 10-12: [Epic 10: App Store Distribution ----------]
```

---

## 6. Risks and Mitigations

### Risk 1: Single-Client Dependency

**Probability:** High | **Impact:** High
**Risk:** Clean New Orleans is our only user. If they churn, we lose 100% of feedback and revenue.
**Mitigation:** Aggressively onboard 3-5 businesses during Phase 1-2 through local cleaning business Facebook groups and Nextdoor. Offer free 3-month Pro plan to first 5 signups. Goal: never depend on a single customer past week 4.

### Risk 2: AI Scheduling Accuracy

**Probability:** Medium | **Impact:** High
**Risk:** If AI-generated schedules require heavy manual correction, the core value proposition fails and Pro/Business tiers become unjustifiable.
**Mitigation:** Start with rule-based optimization (proximity + availability + recurrence), not ML. Use owner overrides as training data. Set clear expectation: "AI suggests, you approve." Target 70% acceptance rate before marketing AI as a feature.

### Risk 3: Payment Integration Complexity

**Probability:** Medium | **Impact:** Medium
**Risk:** Stripe Connect onboarding for small businesses can be friction-heavy (KYC, bank verification). Delayed payouts frustrate owners.
**Mitigation:** Offer Stripe Connect Express (simplified onboarding). Support manual invoice-and-collect as fallback for Basic tier. Document the Stripe onboarding flow with screenshots. Test with 3 businesses before public launch.

### Risk 4: Mobile Performance on Low-End Devices

**Probability:** Medium | **Impact:** Medium
**Risk:** Cleaning teams use budget Android phones. PWA performance on older devices (2-3GB RAM, Android 10) may degrade.
**Mitigation:** Performance budget: < 200KB initial JS, < 2s First Contentful Paint on 3G. Test on low-end devices (Samsung A03, Moto G). Implement offline-first for team check-in/check-out. Progressive loading for non-critical features.

### Risk 5: Market Education and Discovery

**Probability:** High | **Impact:** Medium
**Risk:** Cleaning business owners are not actively searching for SaaS tools. They use WhatsApp groups and paper schedules. They do not know a solution exists.
**Mitigation:** Go where they are: Facebook groups ("Cleaning Business Owners"), local cleaning associations, Nextdoor. Lead with pain ("How much time do you spend scheduling?"), not product ("Try our SaaS"). Build case study with Clean New Orleans showing time saved and revenue impact. Target Google Ads for "cleaning business scheduling software" (low competition, $2-4 CPC).

---

## Appendix: Competitive Landscape

| Competitor | Pricing | Weakness | Our Advantage |
|------------|---------|----------|---------------|
| Jobber | $49-249/mo | Generic field service, not cleaning-specific | Purpose-built for residential cleaning workflows |
| ZenMaid | $49-149/mo | No AI, limited mobile | AI scheduling, PWA-first, modern UX |
| Housecall Pro | $59-199/mo | Enterprise-oriented, complex setup | 5-minute onboarding, affordable entry at $29 |
| Launch27 | $75-175/mo | Focused on booking, weak on operations | Full operations management (schedule + team + payment) |
| Spreadsheets | Free | No automation, error-prone, not scalable | Everything automated, scales from 10 to 500 clients |

---

*Document generated by @pm (Trinity) -- ClaWtoBusiness Product Management*
*Next action: @po validate epic breakdown, @sm draft stories for Epic 1*

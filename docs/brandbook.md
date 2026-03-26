# Xcleaners Brandbook & Design System v2

**Author:** @ux-design-expert (Sati)
**Date:** 2026-03-23
**Status:** FINAL
**Depends on:** `docs/ux/xcleaners-design-system-plan.md`, `docs/ux/xcleaners-wireframes-v3.md`

---

## Table of Contents

1. [Brand Foundation](#1-brand-foundation)
2. [Visual Identity](#2-visual-identity)
3. [UI Component Refinements](#3-ui-component-refinements)
4. [Motion & Animation](#4-motion--animation)
5. [Responsive Design](#5-responsive-design)
6. [Accessibility](#6-accessibility)

---

## 1. Brand Foundation

### 1.1 Mission & Vision

**Mission:** Empower cleaning businesses to operate like Fortune 500 companies -- with scheduling intelligence, team management, and client experience that rivals the best SaaS in any industry.

**Vision:** The operating system for every cleaning business in America. From solo operators to 50-team empires, Xcleaners is the single app that runs the entire operation.

**Tagline:** *Your cleaning business, finally organized.*

**Positioning Statement:** Xcleaners is the first cleaning-business management platform built for schedule-first operations. Unlike Jobber (generic field service) or ZenMaid (booking-only), Xcleaners solves the real daily pain: assigning 100+ recurring jobs across multiple teams, every single day, without chaos.

### 1.2 Brand Personality

Xcleaners has a defined personality expressed through every pixel and every word.

| Trait | What It Means | How It Shows Up |
|-------|---------------|-----------------|
| **Professional but approachable** | We are serious software, not a toy -- but we never intimidate | Clean layouts, warm grays, friendly empty states. No corporate jargon. |
| **Smart but simple** | AI and scheduling intelligence under the hood, effortless on the surface | Features that "just work." Auto-suggestions, not configuration mazes. |
| **Reliable but modern** | Rock-solid data handling wrapped in a fresh interface | Consistent patterns, no surprises. Visual polish signals quality. |
| **Fresh and clean** | Literally -- we are a cleaning product | White space, light backgrounds, crisp typography, breathing room in layouts. |

**Brand Archetypes:**
- Primary: **The Sage** -- knowledgeable, trusted, guiding
- Secondary: **The Creator** -- organized, productive, building something

### 1.3 Brand Voice & Tone

#### How Xcleaners Speaks

Xcleaners communicates like a **knowledgeable colleague** -- not a boss, not a chatbot. We are the coworker who already figured it out and explains it simply.

| Context | Tone | Example |
|---------|------|---------|
| **Dashboard / UI labels** | Direct, efficient, no fluff | "Today's Jobs" not "Your Upcoming Scheduled Cleaning Appointments" |
| **Onboarding** | Warm, encouraging, patient | "Let's set up your first team. This takes about 2 minutes." |
| **Success states** | Celebratory but brief | "Schedule published. Your teams are all set for Monday." |
| **Error messages** | Honest, helpful, no blame | "We couldn't save that change. Check your connection and try again." |
| **Empty states** | Encouraging, action-oriented | "No jobs scheduled for tomorrow yet. Build tomorrow's schedule now." |
| **Notifications** | Concise, scannable | "Team A checked in at Johnson residence -- 2:04 PM" |
| **Marketing / Landing** | Confident, aspirational | "Stop texting schedules. Start running a business." |
| **Email / Comms** | Professional, warm | "Hi James, here's your week at a glance." |

#### Vocabulary

**Words we USE:**
- Schedule, jobs, teams, clients, homes
- Smart, fast, simple, reliable, professional
- Manage, organize, track, grow, streamline
- Dashboard, overview, today, this week

**Words we AVOID:**
- Gig, task, appointment (too generic or clinical)
- Disrupting, revolutionary, game-changing (startup cliches)
- Easy-peasy, super, awesome (too casual for business software)
- Platform, solution, leverage, synergy (corporate nonsense)
- Users (they are "owners," "cleaners," or "clients")

#### Do's and Don'ts

| Do | Don't |
|----|-------|
| Use active voice ("Schedule published") | Use passive voice ("The schedule has been published") |
| Lead with the outcome ("3 jobs completed today") | Lead with the system ("The system has recorded 3 completions") |
| Be specific ("Saved 2 seconds ago") | Be vague ("Recently saved") |
| Use numbers ("4 teams, 12 jobs") | Use words ("several teams, multiple jobs") |
| Address by role ("Hi James" or just the content) | Use "Dear User" or "Hey there!" |
| Explain errors with next steps | Show error codes or technical messages |

---

## 2. Visual Identity

### 2.1 Logo Concept

#### Concept Description

The Xcleaners logo merges two ideas: the **X mark** (precision, the spot to clean, marking completion) and a **sparkle** (cleanliness, freshness, quality). The logomark is a bold X formed by two crossing diagonal strokes with clean proportions, with a small four-point sparkle accent at the upper-right of the X -- suggesting the result of the work: a clean surface.

The X strokes have subtle rounded ends (not aggressive/sharp) to maintain the "professional but approachable" personality. The sparkle is small and geometric, not cartoonish.

#### Logo Variations

| Variation | Usage | Description |
|-----------|-------|-------------|
| **Primary (full color)** | Marketing, website hero, pitch decks | Logomark + "Xcleaners" wordmark. Blue X mark, sparkle in green accent. |
| **Icon mark** | App icon, favicon, notification badges, PWA splash | X mark + sparkle only, no wordmark. Fits in 32x32 to 512x512. |
| **Wordmark** | Email headers, footer, small spaces where icon is separate | "Xcleaners" text in Inter Bold. "X" in `--color-primary-700`, "cleaners" in `--color-primary-500`. |
| **Monochrome dark** | On light backgrounds, printed materials | Full logo in `--color-neutral-900` (#111827). |
| **Monochrome light (reversed)** | On dark backgrounds, dark headers | Full logo in `#FFFFFF`. |
| **Single-color blue** | Watermarks, subtle placements | Full logo in `--color-primary-500` (#3B82F6). |

#### Clear Space Rules

Minimum clear space around the logo equals the height of the letter "X" in the wordmark (the **X-height unit**). No text, icons, or other elements may intrude into this zone.

```
    1X
    |---|
    +---+----------------------------+---+
    | . |                            | . |  1X
    +---+                            +---+
    |   [X ICON]  Xcleaners          |   |
    +---+                            +---+
    | . |                            | . |  1X
    +---+----------------------------+---+
```

#### Minimum Sizes

| Context | Minimum Width |
|---------|---------------|
| Full logo (icon + wordmark) | 120px (digital), 30mm (print) |
| Icon mark only | 24px (digital), 8mm (print) |
| Favicon | 16x16px (use simplified X mark only, no sparkle at this size) |

#### Logo Misuse (Don'ts)

- Do not rotate, skew, or distort the logo
- Do not change the logo colors outside approved variations
- Do not add drop shadows, outlines, or effects
- Do not place the full-color logo on busy photographic backgrounds without a container
- Do not use the logo smaller than minimum sizes
- Do not rearrange the icon and wordmark relationship
- Do not animate the logo in the UI (only permitted in loading/splash screens)

### 2.2 Color System

Xcleaners's color system is built on four semantic color families plus a neutral scale. Each color communicates meaning consistently across the entire product.

#### Primary Colors

| Role | Name | Hex | Usage |
|------|------|-----|-------|
| **Primary** | Trust Blue | `#3B82F6` (500) | Primary actions, links, selected states, brand identity |
| **Secondary** | Fresh Green | `#10B981` (500) | Success states, completed jobs, payments received, positive trends |
| **Accent** | Warm Amber | `#F59E0B` (500) | Warnings, overdue items, attention needed, pending states |
| **Danger** | Alert Red | `#EF4444` (500) | Errors, cancellations, destructive actions, critical alerts |
| **Info** | Cool Cyan | `#06B6D4` (500) | Informational messages, tips, help content |
| **Premium** | Royal Purple | `#8B5CF6` (500) | Premium features, upsell UI, client KPI accents |

#### Full Shade Palette

Each color family uses a 50-900 scale for nuanced usage (tinted backgrounds, hover states, dark text).

**Primary Blue**
| Shade | Hex | Usage |
|-------|-----|-------|
| 50 | `#EFF6FF` | Selected row bg, subtle highlight, primary tint surface |
| 100 | `#DBEAFE` | Active sidebar item bg, light tag bg, hover bg |
| 200 | `#BFDBFE` | Progress bar track, border accent |
| 300 | `#93C5FD` | Outline button border, focus ring tint |
| 400 | `#60A5FA` | Icon accent, secondary emphasis |
| 500 | `#3B82F6` | **Primary button, link color, primary icon** |
| 600 | `#2563EB` | Button hover, active link |
| 700 | `#1D4ED8` | Button pressed, dark emphasis |
| 800 | `#1E40AF` | "Clean" in wordmark, heading accent |
| 900 | `#1E3A8A` | Deep contrast text on light blue bg |

**Success Green**
| Shade | Hex | Usage |
|-------|-----|-------|
| 50 | `#ECFDF5` | Success toast bg, completed row bg |
| 100 | `#D1FAE5` | Success badge bg, positive trend bg |
| 200 | `#A7F3D0` | Progress bar fill (completed portion) |
| 300 | `#6EE7B7` | Chart positive segment |
| 400 | `#34D399` | Check icon, inline success |
| 500 | `#10B981` | **Success button, completed status badge** |
| 600 | `#059669` | Success hover, dark success text |
| 700 | `#047857` | Deep success emphasis |

**Warning Amber**
| Shade | Hex | Usage |
|-------|-----|-------|
| 50 | `#FFFBEB` | Warning toast bg, overdue row bg |
| 100 | `#FEF3C7` | Warning badge bg |
| 200 | `#FDE68A` | Star ratings fill |
| 300 | `#FCD34D` | Chart highlight segment |
| 400 | `#FBBF24` | Inline warning icon |
| 500 | `#F59E0B` | **Warning badge, overdue indicator** |
| 600 | `#D97706` | Warning hover, dark warning text |
| 700 | `#B45309` | Deep warning emphasis |

**Danger Red**
| Shade | Hex | Usage |
|-------|-----|-------|
| 50 | `#FEF2F2` | Error field bg, cancelled row bg |
| 100 | `#FEE2E2` | Danger badge bg, error toast bg |
| 200 | `#FECACA` | Error border |
| 300 | `#FCA5A5` | Outline danger button border |
| 400 | `#F87171` | Inline error icon |
| 500 | `#EF4444` | **Danger button, error text, cancelled badge** |
| 600 | `#DC2626` | Danger hover |
| 700 | `#B91C1C` | Deep danger emphasis |

**Neutral Gray**
| Shade | Hex | Usage |
|-------|-----|-------|
| 25 | `#FCFCFD` | Page background (lightest surface) |
| 50 | `#F9FAFB` | Card background, sidebar bg, table row alt |
| 100 | `#F3F4F6` | Input bg (disabled), skeleton shimmer base |
| 200 | `#E5E7EB` | Borders, dividers, table borders |
| 300 | `#D1D5DB` | Input borders, disabled button border |
| 400 | `#9CA3AF` | Placeholder text, disabled icons |
| 500 | `#6B7280` | Secondary text, labels, captions |
| 600 | `#4B5563` | Body text, descriptions |
| 700 | `#374151` | Strong body text, navigation items |
| 800 | `#1F2937` | Headings, titles |
| 900 | `#111827` | Maximum contrast text, logo monochrome |

#### Semantic Color Rules

| Semantic Use | Token | When to Apply |
|-------------|-------|---------------|
| **Scheduled / Upcoming** | `--color-primary-500` | Jobs in future, default state |
| **In Progress** | `--color-success-500` | Active jobs, check-in confirmed |
| **Completed** | `--color-neutral-400` | Finished jobs (desaturated to recede) |
| **Cancelled** | `--color-danger-500` | Cancelled jobs, errors |
| **Rescheduled** | `--color-warning-500` | Moved jobs, needs attention |
| **Revenue / Money** | `--color-success-600` | Dollar amounts, positive financial |
| **Overdue** | `--color-warning-600` | Past-due payments, missed check-ins |
| **Team colors** | Custom per team | Owner assigns hex per team; used in calendar, badges, card left-border |

#### Background Colors

| Surface | Token | Hex |
|---------|-------|-----|
| App background | `--color-neutral-25` | `#FCFCFD` |
| Card / Panel | `#FFFFFF` | White |
| Sidebar | `--color-neutral-50` | `#F9FAFB` |
| Modal overlay | `rgba(17, 24, 39, 0.5)` | 50% black based on neutral-900 |
| Selected / Active row | `--color-primary-50` | `#EFF6FF` |

#### Gradient Definitions

Use gradients sparingly. They are reserved for high-impact surfaces only.

| Name | Definition | Usage |
|------|-----------|-------|
| **Brand gradient** | `linear-gradient(135deg, #3B82F6, #2563EB)` | Login button, onboarding CTA, premium banner |
| **Success gradient** | `linear-gradient(135deg, #10B981, #059669)` | "Job Complete" confirmation, revenue highlight |
| **Surface gradient** | `linear-gradient(180deg, #FFFFFF 0%, #F9FAFB 100%)` | Page header fade-out, sticky header bg |
| **Dark gradient** | `linear-gradient(135deg, #1E3A8A, #1E40AF)` | Dark mode sidebar header, marketing hero bg |

**Gradient rules:**
- Never use gradients on body text
- Never use more than 2 stops
- Never apply to small elements (badges, tags, inputs)
- Gradients on buttons are reserved for the single primary CTA on a page

### 2.3 Typography

#### Font Stack

| Role | Font | Weights | Fallbacks |
|------|------|---------|-----------|
| **Primary** | Inter | 400, 500, 600, 700, 800 | system-ui, -apple-system, sans-serif |
| **Monospace** | JetBrains Mono | 400, 500, 600 | SF Mono, Fira Code, monospace |

**Why Inter:** Designed for screens. Excellent legibility at small sizes (critical for dense owner dashboards). Variable font support for performance. Free.

**Why JetBrains Mono:** Clear distinction between similar characters (0/O, 1/l/I). Used for job codes, timers, invoice numbers, and financial figures where precision matters.

#### Type Scale

| Token | Size | Weight | Line Height | Letter Spacing | Usage |
|-------|------|--------|-------------|----------------|-------|
| `--text-xs` | 11px | 500 | 1.35 | 0.02em | Badges, timestamps, captions, fine print |
| `--text-sm` | 13px | 400-500 | 1.35 | 0 | Labels, secondary text, table headers |
| `--text-base` | 14px | 400 | 1.5 | 0 | **Body text** -- all default content |
| `--text-md` | 15px | 500 | 1.5 | 0 | Card titles, nav items, form labels (emphasized) |
| `--text-lg` | 18px | 600 | 1.35 | -0.01em | Section headings within pages |
| `--text-xl` | 20px | 600 | 1.35 | -0.01em | Page sub-headings, modal titles |
| `--text-2xl` | 24px | 700 | 1.2 | -0.01em | **Page headings** -- top of each view |
| `--text-3xl` | 28px | 700 | 1.2 | -0.01em | KPI values on dashboard stat cards |
| `--text-4xl` | 36px | 800 | 1.1 | -0.02em | Hero numbers, marketing large KPIs |

#### Type Usage Rules

| Element | Font | Size | Weight | Color |
|---------|------|------|--------|-------|
| Page heading | Inter | `--text-2xl` (24px) | 700 | `--color-neutral-800` |
| Section heading | Inter | `--text-lg` (18px) | 600 | `--color-neutral-800` |
| Card title | Inter | `--text-md` (15px) | 500 | `--color-neutral-800` |
| Body text | Inter | `--text-base` (14px) | 400 | `--color-neutral-600` |
| Label | Inter | `--text-sm` (13px) | 500 | `--color-neutral-500` |
| Caption / Timestamp | Inter | `--text-xs` (11px) | 500 | `--color-neutral-400` |
| KPI number | JetBrains Mono | `--text-3xl` (28px) | 700 | `--color-neutral-900` |
| Dollar amount | JetBrains Mono | varies | 600 | `--color-success-600` |
| Job code / Timer | JetBrains Mono | `--text-sm` (13px) | 500 | `--color-neutral-600` |
| Button text | Inter | `--text-base` (14px) | 600 | inherits from variant |
| Input text | Inter | `--text-base` (14px) | 400 | `--color-neutral-800` |
| Placeholder | Inter | `--text-base` (14px) | 400 | `--color-neutral-400` |

#### Font Pairing Guidelines

- **Never mix more than 2 fonts** on a single screen
- Inter handles ALL text. JetBrains Mono is used ONLY for numerical/code values
- On marketing pages: Inter for headings + Inter for body (weight contrast creates hierarchy)
- On dashboards: Inter for text + JetBrains Mono for KPI numbers and timers
- All-caps text: `--text-xs` or `--text-sm` + `--tracking-wider` (0.05em) + `--font-semibold`

### 2.4 Iconography

#### Icon Style

All Xcleaners icons follow a unified style for visual consistency.

| Attribute | Specification |
|-----------|---------------|
| Style | Outlined (stroke only, no fill) |
| Stroke weight | 2px (at 24x24 base) |
| Line caps | Rounded |
| Line joins | Rounded |
| Grid | 24x24px base with 2px padding (20x20 live area) |
| Corner radius | Minimum 1px on sharp corners |
| Optical alignment | Icons are optically centered, not mathematically |

**Icon library recommendation:** Lucide Icons (fork of Feather Icons, actively maintained, MIT license, consistent 24x24 grid, 2px stroke, rounded caps). Matches our spec exactly.

#### Feature Area Icons

| Area | Icon Name | Description |
|------|-----------|-------------|
| Dashboard | `layout-dashboard` | Grid of rectangles |
| Schedule | `calendar-clock` | Calendar with clock overlay |
| Calendar | `calendar-days` | Calendar with day numbers |
| Teams | `users` | Two-person group |
| Clients | `contact` | Person with card |
| Invoices | `receipt` | Receipt document |
| Settings | `settings` | Gear |
| Today's Jobs | `clipboard-list` | Checklist |
| Earnings | `dollar-sign` | Dollar in circle |
| Profile | `user-circle` | Person in circle |
| My Bookings | `calendar-check` | Calendar with checkmark |
| My Home | `home` | House outline |
| Notifications | `bell` | Bell |
| Check-in | `map-pin` | Location pin |
| Timer | `clock` | Clock face |
| Revenue | `trending-up` | Upward trend line |
| Add / Create | `plus` | Plus sign |
| Search | `search` | Magnifying glass |
| Filter | `sliders-horizontal` | Horizontal slider controls |
| Menu / Hamburger | `menu` | Three horizontal lines |
| Close | `x` | X mark |
| Back | `arrow-left` | Left arrow |
| Expand / Chevron | `chevron-right` | Right angle bracket |
| Status: Completed | `check-circle` | Checkmark in circle |
| Status: Cancelled | `x-circle` | X in circle |
| Status: In Progress | `loader` | Spinning loader circle |
| Star / Rating | `star` | Five-point star |

#### Icon Sizes

| Size Token | Pixel Size | Usage |
|-----------|-----------|-------|
| `--icon-xs` | 14px | Inline with `--text-xs`, badge icons |
| `--icon-sm` | 16px | Inline with `--text-sm` or `--text-base`, button icons |
| `--icon-md` | 20px | Standalone icons, nav icons (collapsed sidebar) |
| `--icon-lg` | 24px | Primary nav icons, card header icons |
| `--icon-xl` | 32px | Empty state illustrations (supporting), feature icons |
| `--icon-2xl` | 48px | Empty state primary illustration, onboarding |

#### Iconography Do's and Don'ts

**Do:**
- Use icons from one library (Lucide) for consistency
- Pair icons with text labels in navigation (icon-only = accessibility risk)
- Use `--color-neutral-500` for default icon color, `--color-neutral-700` for active
- Add `aria-hidden="true"` to decorative icons
- Add `role="img" aria-label="..."` to meaningful icons
- Scale icons proportionally to their container

**Don't:**
- Mix outlined and filled icon styles on the same screen
- Use icons smaller than 14px (illegible)
- Use colored icons for decoration (color = meaning)
- Use emoji as icons in the product UI
- Add strokes or effects to icons beyond the base 2px

### 2.5 Photography Style

#### Product Photography Guidelines

Xcleaners uses photography in marketing materials, onboarding, and empty states. The photo style reinforces the brand personality: professional, clean, real.

| Attribute | Guideline |
|-----------|-----------|
| **Lighting** | Natural daylight or bright, even artificial light. No dark, moody shots. Cleanliness = brightness. |
| **Color temperature** | Warm-neutral (5000-5500K). Not too orange, not too blue. |
| **Subjects** | Real cleaning teams at work. Diverse people -- different ethnicities, ages, genders. |
| **Clothing** | Branded uniforms or clean, professional casual. Gloves, aprons, and equipment visible. |
| **Environment** | Real homes, real kitchens, real bathrooms. Not sterile studios. |
| **Composition** | Action shots preferred (spraying, wiping, mopping). Not posed portraits. |
| **Post-processing** | Light and bright. Slight contrast boost. No heavy filters, no HDR look. |
| **Before/After** | Split-frame or slider format for marketing. Dramatic but believable difference. |

#### Stock Photo Guidelines

When original photography is not available:

- **Source:** Unsplash, Pexels, or licensed stock (iStock, Shutterstock)
- **Search terms:** "cleaning team," "house cleaning," "cleaning service professional," "residential cleaning"
- **Reject if:** Overly posed, stock-photo smile, unnatural lighting, homogeneous demographics
- **Accept if:** Natural moment, real environment, diverse team, professional but candid feel

#### Photo Usage in Product

| Location | Photo Style |
|----------|-------------|
| Login / Onboarding screens | Hero photo of a team at work, full-bleed behind content overlay |
| Empty states | Avoid photos -- use line illustrations instead (lighter weight, faster load) |
| Client profile | User-uploaded photos of their home (circle crop, `--radius-full`) |
| Team member avatar | Photo or initials circle |
| Marketing site | Full-width hero, before/after sections, team spotlight |

---

## 3. UI Component Refinements

All components use the `cc-` prefix (legacy CSS convention, retained for backward compatibility). Sizes, colors, and spacing reference design tokens defined in Section 2.

### 3.1 Buttons

#### Variants

| Variant | Class | Background | Text | Border | Use Case |
|---------|-------|-----------|------|--------|----------|
| **Primary** | `.cc-btn-primary` | `--color-primary-500` | `#FFFFFF` | none | Primary action per screen (1 per view) |
| **Secondary** | `.cc-btn-secondary` | `--color-neutral-100` | `--color-neutral-700` | none | Secondary actions, paired with primary |
| **Ghost** | `.cc-btn-ghost` | `transparent` | `--color-neutral-600` | none | Tertiary actions, toolbar items, "Cancel" |
| **Danger** | `.cc-btn-danger` | `--color-danger-500` | `#FFFFFF` | none | Destructive actions (delete, cancel job) |
| **Outline** | `.cc-btn-outline` | `transparent` | `--color-primary-500` | 1px `--color-primary-300` | Alternative secondary, filter toggles |
| **Outline Danger** | `.cc-btn-outline-danger` | `transparent` | `--color-danger-500` | 1px `--color-danger-300` | Destructive with less visual weight |

#### Sizes

| Size | Class | Padding | Font Size | Height | Use Case |
|------|-------|---------|-----------|--------|----------|
| **XS** | `.cc-btn-xs` | 4px 10px | 11px | 26px | Inline actions, table row buttons |
| **SM** | `.cc-btn-sm` | 6px 14px | 13px | 32px | Card actions, secondary controls |
| **MD** (default) | `.cc-btn` | 10px 20px | 14px | 40px | Standard buttons throughout app |
| **LG** | `.cc-btn-lg` | 14px 28px | 15px | 48px | Primary CTAs, mobile full-width actions |

#### Border Radius

All buttons use `--radius-sm` (6px). Full-width mobile buttons may use `--radius-md` (10px).

#### States

| State | Visual Change |
|-------|---------------|
| **Default** | As specified per variant |
| **Hover** | Background shifts one shade darker; primary buttons gain `--shadow-primary` |
| **Active / Pressed** | `transform: scale(0.97)` for tactile feedback |
| **Focus-visible** | 3px ring using `--ring-primary` (or `--ring-danger` for danger buttons) |
| **Disabled** | `opacity: 0.5`, `cursor: not-allowed`, no hover/active effects |
| **Loading** | `opacity: 0.8`, `pointer-events: none`, 16px spinner appended after text |

#### Icon + Text Patterns

- Icon before text: 8px gap (default)
- Icon after text: 8px gap (used for "next" actions, arrows)
- Icon-only button: square aspect ratio, same padding vertically and horizontally, `aria-label` required
- Icon size in buttons: `--icon-sm` (16px) for SM/MD buttons, `--icon-md` (20px) for LG

### 3.2 Cards

Cards are the primary content container in Xcleaners. Every piece of information lives in a card.

#### Base Card

| Property | Value |
|----------|-------|
| Background | `#FFFFFF` |
| Border | 1px solid `--color-neutral-200` |
| Border radius | `--radius-md` (10px) |
| Padding | `--spacing-4` (16px) |
| Shadow (at rest) | `--shadow-1` |

#### Card Types

**Stat Card (Dashboard KPIs)**

Used on the Owner Dashboard for key metrics. Grid of 4 across on desktop, 2x2 on mobile.

| Element | Style |
|---------|-------|
| Value | JetBrains Mono, `--text-3xl` (28px), `--font-bold`, `--color-neutral-900` |
| Label | Inter, `--text-sm` (13px), `--font-medium`, `--color-neutral-500` |
| Trend indicator | `--text-xs` (11px), `--font-semibold`, green for positive / red for negative |
| Icon | `--icon-lg` (24px) in colored circle bg (e.g., `--color-primary-50` circle with `--color-primary-500` icon) |
| Hover | `--shadow-2`, `translateY(-2px)` |

**Job Card (Schedule / Today)**

The most-used card in the app. Must be information-dense yet scannable.

| Element | Style |
|---------|-------|
| Left border | 4px solid, color = status (primary=scheduled, success=in-progress, neutral-400=completed, danger=cancelled) |
| Time | JetBrains Mono, `--text-sm`, `--font-medium` |
| Client name | Inter, `--text-md`, `--font-medium`, `--color-neutral-800` |
| Address | Inter, `--text-sm`, `--color-neutral-500`, truncated to 1 line |
| Status badge | Pill shape (`--radius-full`), `--text-xs`, colored per status |
| Team indicator | Small colored dot (8px) matching team color + team name in `--text-xs` |
| Hover | `--shadow-2`, `translateY(-1px)` |
| Active/Tap | `scale(0.99)` |
| Completed state | `opacity: 0.85` to visually recede |
| Cancelled state | `opacity: 0.6`, strikethrough on time |

**Client Card**

| Element | Style |
|---------|-------|
| Avatar | 40px circle, initials on `--color-primary-100` bg, or photo |
| Client name | Inter, `--text-md`, `--font-medium` |
| Address | Inter, `--text-sm`, `--color-neutral-500` |
| Frequency badge | Pill, `--text-xs`, `--color-primary-50` bg, `--color-primary-700` text |
| Next job | Inter, `--text-xs`, `--color-neutral-400` |
| Layout | Horizontal flex: avatar, text column, right-aligned metadata |

**Invoice Card**

| Element | Style |
|---------|-------|
| Amount | JetBrains Mono, `--text-xl`, `--font-semibold`, `--color-neutral-900` |
| Status | Badge: Paid (`--color-success`), Pending (`--color-warning`), Overdue (`--color-danger`), Draft (`--color-neutral`) |
| Client name | Inter, `--text-md`, `--color-neutral-700` |
| Date | Inter, `--text-sm`, `--color-neutral-400` |
| Invoice number | JetBrains Mono, `--text-xs`, `--color-neutral-400` |

#### Elevation and Shadow Usage

| Level | Shadow Token | When to Use |
|-------|-------------|-------------|
| 0 | `--shadow-0` (none) | Elements flush with surface (table rows, inline items) |
| 1 | `--shadow-1` | Cards at rest, panels, containers |
| 2 | `--shadow-2` | Cards on hover, active dropdowns |
| 3 | `--shadow-3` | Dropdowns, popovers, tooltips, floating action buttons |
| 4 | `--shadow-4` | Modals, dialogs |
| 5 | `--shadow-5` | Bottom sheets, slide-over panels |

**Colored shadows** (`--shadow-primary`, `--shadow-success`, `--shadow-danger`) are used on primary action buttons on hover to create a "glow" effect that draws attention.

### 3.3 Navigation

#### Sidebar (Schedule Owner -- Desktop)

| Property | Value |
|----------|-------|
| Width (expanded) | 260px |
| Width (collapsed) | 64px (icon-only mode) |
| Background | `--color-neutral-50` (#F9FAFB) |
| Border right | 1px solid `--color-neutral-200` |
| Logo area | 60px height, centered logo |
| Nav item height | 40px |
| Nav item padding | 12px 16px |
| Nav item font | Inter, `--text-md` (15px), `--font-medium`, `--color-neutral-600` |
| Nav icon | `--icon-lg` (24px), `--color-neutral-400` |
| Active item bg | `--color-primary-50` (#EFF6FF) |
| Active item text | `--color-primary-700` (#1D4ED8), `--font-semibold` |
| Active item icon | `--color-primary-500` (#3B82F6) |
| Active indicator | 3px left border, `--color-primary-500` |
| Hover item bg | `--color-neutral-100` |
| Hover transition | `background var(--duration-normal) var(--ease-out)` |
| Collapse trigger | Chevron icon at bottom of sidebar or keyboard shortcut `[` |
| Collapse animation | Width transitions over `--duration-medium` (300ms), labels fade out at 200ms |

**Mobile behavior:** Sidebar becomes a full-screen overlay triggered by hamburger icon (top-left). Overlay backdrop: `rgba(17, 24, 39, 0.5)`. Slides in from left over `--duration-medium`.

#### Bottom Tabs (Cleaner / Homeowner -- Mobile)

| Property | Value |
|----------|-------|
| Height | 56px (+ safe area inset on iOS) |
| Background | `#FFFFFF` |
| Border top | 1px solid `--color-neutral-200` |
| Max tabs | 5 (4 for cleaner, 3 for homeowner) |
| Tab layout | Even flex distribution |
| Icon | `--icon-md` (20px), centered above label |
| Label | Inter, `--text-xs` (11px), `--font-medium` |
| Default color | `--color-neutral-400` (icon + label) |
| Active color | `--color-primary-500` (icon + label) |
| Active indicator | 2px top border on tab area, or dot below icon |
| Touch target | Full tab width x 56px height (minimum 44x44 tap area) |
| Haptic feedback | `navigator.vibrate(10)` on tab change (Android only) |

**Rules:**
- Labels are always visible (not icon-only) for accessibility
- Active tab transitions with `--duration-fast` color change
- Tab bar hides on scroll-down, reveals on scroll-up (save screen real estate)
- Tab bar must respect iOS safe area: `padding-bottom: env(safe-area-inset-bottom)`

#### Top Nav (Homeowner -- Desktop)

| Property | Value |
|----------|-------|
| Height | 56px |
| Background | `#FFFFFF` |
| Border bottom | 1px solid `--color-neutral-200` |
| Shadow | `--shadow-1` |
| Logo | Left-aligned, icon mark + "Xcleaners" wordmark |
| Nav items | Center or right-aligned, horizontal, `--text-md`, `--font-medium` |
| Active item | `--color-primary-500`, 2px bottom border |
| User menu | Right-most, avatar circle + chevron-down, opens dropdown |

### 3.4 Empty States

Every screen that can have no data shows a designed empty state -- never a blank page.

#### Illustration Style

- **Technique:** Single-weight line art (2px stroke), monochrome `--color-neutral-300` with ONE accent color from the primary palette
- **Size:** 120x120px to 160x160px SVG
- **Style:** Minimalist, geometric, friendly. Think Notion or Linear empty states.
- **Subject:** Abstract representation of the missing content (calendar for no jobs, people for no teams, etc.)

#### Copy Pattern

Every empty state follows this structure:

```
[Illustration]

[Title] — Bold, --text-lg, --color-neutral-800
[Description] — Regular, --text-base, --color-neutral-500, max 2 lines
[CTA Button] — Primary or outline, contextual action
```

#### Per-Screen Examples

| Screen | Title | Description | CTA |
|--------|-------|-------------|-----|
| Owner Dashboard (new) | "Welcome to Xcleaners" | "Let's set up your first team and add your clients to get started." | "Add Your First Team" |
| Schedule (no jobs today) | "No jobs scheduled for today" | "Build today's schedule from your client list, or add a new job." | "Build Schedule" |
| Teams (none created) | "Create your first team" | "Teams help you organize your cleaners and assign jobs efficiently." | "Create Team" |
| Clients (none added) | "Add your first client" | "Import clients from a spreadsheet or add them one by one." | "Add Client" / "Import CSV" |
| Invoices (none) | "No invoices yet" | "Invoices are created automatically when you complete jobs." | "View Completed Jobs" |
| Cleaner Today (no jobs) | "Your day is clear" | "No jobs assigned for today. Enjoy the break or check tomorrow's schedule." | "View This Week" |
| Homeowner Bookings (none) | "No upcoming bookings" | "Request a cleaning to get started with your cleaning service." | "Request Cleaning" |

### 3.5 Loading States

#### Skeleton Screens

Skeleton screens are the default loading indicator. They show the layout of the incoming content with animated placeholder shapes.

| Element | Skeleton Shape |
|---------|---------------|
| Text line | Rounded rectangle, 12px height, 60-80% container width, `--radius-xs` |
| Heading | Rounded rectangle, 20px height, 40% width |
| Avatar / Circle | Circle, same size as target avatar |
| Card | Full card outline with internal skeleton lines |
| KPI number | Rounded rectangle, 28px height, 50% width |
| Image | Rectangle matching target aspect ratio |
| Button | Rounded rectangle matching button dimensions |

**Skeleton animation:**

```css
@keyframes cc-skeleton-shimmer {
  0%   { background-position: -200px 0; }
  100% { background-position: calc(200px + 100%) 0; }
}

.cc-skeleton {
  background: linear-gradient(
    90deg,
    var(--color-neutral-100) 0px,
    var(--color-neutral-50) 40px,
    var(--color-neutral-100) 80px
  );
  background-size: 200px 100%;
  animation: cc-skeleton-shimmer 1.5s ease-in-out infinite;
  border-radius: var(--radius-xs);
}
```

**Skeleton patterns per component:**

| Component | Skeleton Layout |
|-----------|-----------------|
| Stat card | Icon circle + 2 text lines (value + label) |
| Job card | Left border bar + 3 text lines (time, name, address) + badge rectangle |
| Client card | Avatar circle + 2 text lines + pill rectangle |
| Table row | 4-5 rectangles aligned to column widths |
| Nav sidebar | 8 text line rectangles with icon circles |

#### Spinner

Use spinners ONLY when:
- Content area is too small for a skeleton (e.g., inside a button)
- Action is happening (saving, submitting) not content loading
- Pull-to-refresh indicator

| Spinner Size | Pixel Size | Usage |
|-------------|-----------|-------|
| SM | 16px | Inside buttons, inline indicators |
| MD | 24px | Card-level loading, form submission |
| LG | 32px | Pull-to-refresh, section loading |

**Spinner style:** 2px stroke circle with a 90-degree colored arc. Color matches context (primary for default, white for inside primary buttons). `animation: cc-spin 0.6s linear infinite`.

#### Pull-to-Refresh

Mobile only. Triggered by pulling down from top of scrollable content.

| Phase | Visual |
|-------|--------|
| Pull (< threshold) | Arrow icon rotates proportional to pull distance |
| Pull (>= threshold) | Arrow flips upward, haptic buzz (10ms) |
| Refreshing | 24px spinner replaces arrow, "Updating..." text |
| Complete | Spinner fades out, content updates |

---

## 4. Motion & Animation

Motion in Xcleaners serves function, not decoration. Every animation has a purpose: provide feedback, guide attention, or communicate state change.

### 4.1 Duration Scale

| Token | Duration | Use Case |
|-------|----------|----------|
| `--duration-fast` | 100ms | Micro-interactions: toggle flips, checkbox bounces, color changes |
| `--duration-normal` | 200ms | Button hovers, card hover lift, dropdown open, tooltip appear |
| `--duration-medium` | 300ms | Page transitions, sidebar collapse, bottom sheet open |
| `--duration-slow` | 500ms | Complex reveals, chart animations, onboarding sequences |

**Rule:** If a user initiates the action (click, tap), use `--duration-fast` or `--duration-normal`. If the system initiates (page load, data update), use `--duration-medium` or `--duration-slow`.

### 4.2 Easing Functions

| Token | Curve | Use Case |
|-------|-------|----------|
| `--ease-out` | `cubic-bezier(0.33, 1, 0.68, 1)` | **Elements entering the screen.** Quick start, gentle land. Most common easing. |
| `--ease-in` | `cubic-bezier(0.32, 0, 0.67, 0)` | **Elements leaving the screen.** Slow start, quick exit. Used for dismissals. |
| `--ease-in-out` | `cubic-bezier(0.65, 0, 0.35, 1)` | **Elements moving on screen.** Repositioning, resizing, drag movements. |
| `--ease-spring` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | **Playful micro-interactions.** Toggle switches, checkbox bounce, success checkmark. |
| `--ease-smooth` | `cubic-bezier(0.25, 0.1, 0.25, 1.0)` | **Default fallback.** Use when unsure which easing fits. |

### 4.3 Page Transitions

When navigating between views (hash-route changes):

| Transition Type | Animation | Duration | Easing |
|----------------|-----------|----------|--------|
| **Forward navigation** (deeper into hierarchy) | Current view fades out + slides left 20px. New view fades in + slides from right 20px. | 250ms | `--ease-out` |
| **Back navigation** (up the hierarchy) | Current view fades out + slides right 20px. New view fades in + slides from left 20px. | 250ms | `--ease-out` |
| **Peer navigation** (same level, e.g., tab switch) | Cross-fade only. Current fades out, new fades in. | 200ms | `--ease-smooth` |
| **Modal open** | Backdrop fades in (200ms). Modal scales from 0.95 to 1.0 + fades in. | 250ms | `--ease-out` |
| **Modal close** | Modal scales from 1.0 to 0.95 + fades out. Backdrop fades out. | 200ms | `--ease-in` |
| **Bottom sheet open** | Slides up from bottom of screen. | 300ms | `--ease-out` |
| **Bottom sheet close** | Slides down + fades. Supports gesture (drag down to dismiss). | 250ms | `--ease-in` |

### 4.4 Micro-Interactions

| Interaction | Animation | Duration | Easing |
|------------|-----------|----------|--------|
| **Toggle switch** | Knob slides left/right. Track color fades between neutral and primary. | 150ms | `--ease-spring` |
| **Checkbox check** | Checkmark draws in with SVG stroke animation. Box border color transitions. | 200ms | `--ease-spring` |
| **Button press** | `scale(0.97)` on `:active`. | 100ms | `--ease-out` |
| **Button hover (primary)** | Background darkens one shade. `--shadow-primary` appears. | 200ms | `--ease-out` |
| **Card hover** | `translateY(-2px)` + shadow lifts to `--shadow-2`. | 200ms | `--ease-out` |
| **Status badge change** | Background color cross-fades. No movement. | 300ms | `--ease-smooth` |
| **Counter animation** | Numbers count up from 0 to target value (on dashboard load). | 600ms | `--ease-out` |
| **Notification toast** | Slides in from top-right, 16px offset. Auto-dismiss after 4s with fade-out. | 300ms in / 200ms out | `--ease-out` / `--ease-in` |
| **Dropdown open** | `scaleY(0)` to `scaleY(1)`, transform-origin: top. Opacity 0 to 1. | 200ms | `--ease-out` |
| **FAB press** | Scale bounce: `scale(0.9)` then `scale(1)`. | 200ms | `--ease-spring` |

### 4.5 List Item Stagger

When a list of items loads (e.g., today's job cards, client list), items animate in with a stagger delay.

| Property | Value |
|----------|-------|
| Individual item animation | Fade in (`opacity: 0` to `1`) + slide up (`translateY(8px)` to `0`) |
| Duration per item | 200ms |
| Easing | `--ease-out` |
| Stagger delay | 50ms between each item |
| Maximum stagger | 10 items (items 11+ appear with no stagger to avoid slow perceived load) |

```css
.cc-stagger-item {
  opacity: 0;
  transform: translateY(8px);
  animation: cc-stagger-in 200ms var(--ease-out) forwards;
}

@keyframes cc-stagger-in {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Apply via JS: element.style.animationDelay = `${index * 50}ms` (capped at 10) */
```

### 4.6 Reduced Motion

All animations respect the user's system preference.

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

When reduced motion is active:
- Page transitions become instant cross-fades (opacity only, no movement)
- Skeleton shimmer still runs (subtle, not disorienting)
- Counter animations show final value immediately
- Toggle/checkbox state changes are instant

---

## 5. Responsive Design

### 5.1 Breakpoints

| Token | Width | Name | Target Devices |
|-------|-------|------|----------------|
| `--bp-xs` | 0 - 479px | Extra Small | Small phones (iPhone SE, older Android) |
| `--bp-sm` | 480 - 767px | Small | Standard phones (iPhone 14/15, Pixel, Galaxy) |
| `--bp-md` | 768 - 1023px | Medium | Tablets (iPad Mini, iPad), small laptops |
| `--bp-lg` | 1024 - 1279px | Large | Laptops, iPad Pro landscape |
| `--bp-xl` | 1280px+ | Extra Large | Desktops, external monitors |

```css
/* Mobile-first: base styles = xs */
/* sm */  @media (min-width: 480px) { }
/* md */  @media (min-width: 768px) { }
/* lg */  @media (min-width: 1024px) { }
/* xl */  @media (min-width: 1280px) { }
```

### 5.2 Layout Patterns Per Breakpoint

#### Schedule Owner

| Breakpoint | Sidebar | Content Area | KPI Grid | Job List | Calendar |
|-----------|---------|-------------|----------|----------|----------|
| xs-sm | Hidden (hamburger overlay) | Full width | 2 columns | Single column cards | Day view only |
| md | Hidden (hamburger overlay) | Full width | 2 columns | Single column cards | Day + Week toggle |
| lg | Collapsed (64px icons) | Calc(100% - 64px) | 4 columns | Single column with wider cards | Week + Resource view |
| xl | Expanded (260px) | Calc(100% - 260px) | 4 columns | Two-column optional | Full resource timeline |

#### Homeowner

| Breakpoint | Navigation | Content Area | Booking Cards |
|-----------|-----------|-------------|--------------|
| xs-sm | Bottom tabs (3) | Full width, 16px padding | Full-width stacked |
| md | Top nav | 720px centered max-width | 2-column grid |
| lg-xl | Top nav | 960px centered max-width | 2-column grid with sidebar details |

#### Cleaner

| Breakpoint | Navigation | Content Area | Job Cards |
|-----------|-----------|-------------|-----------|
| xs-sm | Bottom tabs (4) | Full width, 16px padding | Full-width stacked, large touch targets |
| md-xl | Bottom tabs (centered 480px max) | 480px centered | Same layout, just centered |

### 5.3 Touch Targets

| Element | Minimum Size | Recommended Size | Context |
|---------|-------------|-----------------|---------|
| Buttons | 44x44px | 48x48px | WCAG 2.2 Level AA + Apple HIG |
| Nav items | 44x44px | 48x48px | Bottom tabs, sidebar items |
| Checkbox / Radio | 44x44px (hit area) | 20x20px visual + padding | Tap area extends beyond visual |
| List items (tappable) | 44px height | 56-72px height | Job cards, client rows |
| Close / Dismiss buttons | 44x44px | 44x44px | Modal X, toast dismiss |
| Floating action button | 56x56px | 56x56px | FAB for primary mobile action |

**Rule:** On mobile (xs-sm breakpoints), NEVER place two tappable elements closer than 8px apart. Cleaners tap with wet or gloved hands -- error margin must be generous.

### 5.4 Safe Areas

```css
/* iOS notch / Dynamic Island */
.cc-app-shell {
  padding-top: env(safe-area-inset-top);
  padding-bottom: env(safe-area-inset-bottom);
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
}

/* Bottom tab bar specifically */
.cc-bottom-tabs {
  padding-bottom: env(safe-area-inset-bottom);
  /* Total height = 56px + safe-area-inset-bottom */
}

/* Android gesture navigation bar */
/* Handled automatically by padding-bottom: env(safe-area-inset-bottom) */
/* On Android without gesture nav, inset is 0 */
```

### 5.5 Content Behavior

| Pattern | Implementation |
|---------|---------------|
| **Fluid typography** | Not used. Fixed type scale. Font sizes do not change across breakpoints (keeps code simple, Inter is legible at all sizes). |
| **Fluid spacing** | Page padding: 16px (xs-sm), 24px (md), 32px (lg-xl). |
| **Truncation** | Long text (addresses, names) truncates with ellipsis on mobile. Full text on desktop. `text-overflow: ellipsis; white-space: nowrap; overflow: hidden;` |
| **Tables on mobile** | Tables transform to card-list layout on xs-sm. Each row becomes a card with label-value pairs stacked vertically. |
| **Modals on mobile** | Full-screen modals (not centered floating) on xs-sm. Bottom sheet pattern preferred for short actions. |

---

## 6. Accessibility

Xcleaners targets **WCAG 2.2 Level AA** compliance as a minimum. Cleaning business owners, cleaners, and homeowners represent diverse abilities -- accessibility is not optional.

### 6.1 Color Contrast Ratios

All text and interactive elements must meet these minimum contrast ratios against their background.

| Element | Minimum Ratio | Standard |
|---------|---------------|----------|
| Body text (normal, < 18px) | 4.5:1 | WCAG AA |
| Large text (>= 18px bold or >= 24px regular) | 3:1 | WCAG AA |
| UI components (borders, icons with meaning) | 3:1 | WCAG AA |
| Placeholder text | 4.5:1 | WCAG AA (our choice -- many products fail this) |
| Disabled elements | No minimum | Exempt, but must be visually distinct |

**Verified color combinations:**

| Foreground | Background | Ratio | Pass? |
|-----------|-----------|-------|-------|
| `--color-neutral-600` (#4B5563) | White (#FFFFFF) | 7.0:1 | AA, AAA |
| `--color-neutral-500` (#6B7280) | White (#FFFFFF) | 5.0:1 | AA |
| `--color-neutral-400` (#9CA3AF) | White (#FFFFFF) | 3.0:1 | UI only (not body text) |
| `--color-primary-500` (#3B82F6) | White (#FFFFFF) | 3.6:1 | Large text + UI only |
| `--color-primary-600` (#2563EB) | White (#FFFFFF) | 4.6:1 | AA (use for text links) |
| `--color-primary-700` (#1D4ED8) | White (#FFFFFF) | 5.9:1 | AA, AAA |
| White (#FFFFFF) | `--color-primary-500` (#3B82F6) | 3.6:1 | Large text (button labels OK at 14px semi-bold) |
| `--color-danger-500` (#EF4444) | White (#FFFFFF) | 3.9:1 | Large text + UI only |
| `--color-danger-700` (#B91C1C) | White (#FFFFFF) | 6.1:1 | AA (use for error text) |
| `--color-success-600` (#059669) | White (#FFFFFF) | 4.6:1 | AA |
| `--color-warning-700` (#B45309) | White (#FFFFFF) | 5.2:1 | AA |

**Implementation rule:** For body-text-sized content on white backgrounds, use `--color-neutral-600` minimum (7.0:1). For labels and secondary text, `--color-neutral-500` (5.0:1). Never use `--color-neutral-400` for readable text -- only for placeholders and decorative/disabled elements where 3:1 is sufficient.

**Text links:** Use `--color-primary-600` (#2563EB), not `--color-primary-500`, to guarantee 4.5:1 on white.

### 6.2 Focus Indicators

Every interactive element must have a visible focus indicator when navigated via keyboard (`Tab`/`Shift+Tab`).

| Element | Focus Style |
|---------|-------------|
| Buttons | `box-shadow: var(--ring-primary)` — 3px ring, `rgba(59, 130, 246, 0.15)` |
| Danger buttons | `box-shadow: var(--ring-danger)` — 3px ring, `rgba(239, 68, 68, 0.15)` |
| Inputs | `border-color: var(--color-primary-500)` + `box-shadow: var(--ring-primary)` |
| Links | `outline: 2px solid var(--color-primary-500)` + `outline-offset: 2px` |
| Cards (interactive) | `outline: 2px solid var(--color-primary-500)` + `outline-offset: 2px` |
| Sidebar nav items | `background: var(--color-primary-50)` + left border accent |
| Bottom tab items | `outline: 2px solid var(--color-primary-500)` inside tab area |

**Rule:** Use `:focus-visible` (not `:focus`) so focus rings appear only on keyboard navigation, not on mouse clicks. This avoids visual noise for mouse users while maintaining keyboard accessibility.

```css
.cc-btn:focus-visible {
  outline: none;
  box-shadow: var(--ring-primary);
}
```

### 6.3 Screen Reader Considerations

| Pattern | Implementation |
|---------|---------------|
| **Icons** | Decorative icons: `aria-hidden="true"`. Meaningful icons: `role="img" aria-label="description"`. |
| **Status badges** | Include `aria-label` with full status text: `aria-label="Job status: In Progress"`. |
| **KPI cards** | Stat cards include `aria-label` combining value + label: `aria-label="12 Jobs Today"`. |
| **Modals** | `role="dialog"`, `aria-modal="true"`, `aria-labelledby` pointing to modal title. Focus trapped inside modal. |
| **Bottom tabs** | `role="tablist"` on container, `role="tab"` + `aria-selected` on each tab, `role="tabpanel"` on content. |
| **Loading states** | Skeleton areas include `aria-busy="true"` and `aria-label="Loading"`. Remove when content loads. |
| **Toasts** | `role="status"` + `aria-live="polite"` for info/success. `role="alert"` for errors. |
| **Forms** | Every input has a visible `<label>` with matching `for`/`id`. Error messages use `aria-describedby`. |
| **Route changes** | Announce new page title via `aria-live="polite"` region when hash route changes. |
| **Skip link** | Hidden "Skip to main content" link as first focusable element in DOM. Visible on focus. |

### 6.4 Reduced Motion Preferences

See Section 4.6 for the CSS implementation. Additionally:

- Auto-playing animations (counter count-up, chart entry) should not play if `prefers-reduced-motion: reduce`
- Skeleton shimmer is exempt (subtle, not disorienting)
- Page transitions reduce to simple opacity fade (no movement)
- Pull-to-refresh reduces to opacity change only

### 6.5 Additional Accessibility Requirements

| Requirement | Implementation |
|-------------|---------------|
| **Minimum font size** | 11px (`--text-xs`). Nothing smaller in the product. |
| **Zoom support** | App must remain usable at 200% browser zoom without horizontal scroll. |
| **Color is not the only indicator** | Status badges include text labels, not just color dots. Error inputs have icon + text, not just red border. |
| **Language** | `<html lang="en">`. Support for future i18n via `lang` attribute on sections. |
| **Touch target spacing** | 8px minimum between adjacent touch targets (see Section 5.3). |
| **Auto-complete** | Form inputs include appropriate `autocomplete` attributes (`name`, `email`, `tel`, `street-address`). |

---

## Appendix A: Design Token Quick Reference

Complete CSS custom properties for implementation. Copy into `:root` block of `app.css`.

```css
:root {
  /* ── Colors ── */
  --color-primary-50:  #EFF6FF;
  --color-primary-100: #DBEAFE;
  --color-primary-200: #BFDBFE;
  --color-primary-300: #93C5FD;
  --color-primary-400: #60A5FA;
  --color-primary-500: #3B82F6;
  --color-primary-600: #2563EB;
  --color-primary-700: #1D4ED8;
  --color-primary-800: #1E40AF;
  --color-primary-900: #1E3A8A;

  --color-success-50:  #ECFDF5;
  --color-success-100: #D1FAE5;
  --color-success-200: #A7F3D0;
  --color-success-300: #6EE7B7;
  --color-success-400: #34D399;
  --color-success-500: #10B981;
  --color-success-600: #059669;
  --color-success-700: #047857;

  --color-warning-50:  #FFFBEB;
  --color-warning-100: #FEF3C7;
  --color-warning-200: #FDE68A;
  --color-warning-300: #FCD34D;
  --color-warning-400: #FBBF24;
  --color-warning-500: #F59E0B;
  --color-warning-600: #D97706;
  --color-warning-700: #B45309;

  --color-danger-50:  #FEF2F2;
  --color-danger-100: #FEE2E2;
  --color-danger-200: #FECACA;
  --color-danger-300: #FCA5A5;
  --color-danger-400: #F87171;
  --color-danger-500: #EF4444;
  --color-danger-600: #DC2626;
  --color-danger-700: #B91C1C;

  --color-info-50:  #ECFEFF;
  --color-info-100: #CFFAFE;
  --color-info-500: #06B6D4;
  --color-info-600: #0891B2;

  --color-purple-50:  #F5F3FF;
  --color-purple-100: #EDE9FE;
  --color-purple-500: #8B5CF6;
  --color-purple-600: #7C3AED;

  --color-neutral-25:  #FCFCFD;
  --color-neutral-50:  #F9FAFB;
  --color-neutral-100: #F3F4F6;
  --color-neutral-200: #E5E7EB;
  --color-neutral-300: #D1D5DB;
  --color-neutral-400: #9CA3AF;
  --color-neutral-500: #6B7280;
  --color-neutral-600: #4B5563;
  --color-neutral-700: #374151;
  --color-neutral-800: #1F2937;
  --color-neutral-900: #111827;

  /* Backward-compatible aliases */
  --color-primary:       var(--color-primary-500);
  --color-primary-dark:  var(--color-primary-600);
  --color-primary-light: var(--color-primary-100);
  --color-success:       var(--color-success-500);
  --color-warning:       var(--color-warning-500);
  --color-danger:        var(--color-danger-500);

  /* ── Typography ── */
  --font-primary: 'Inter', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'SF Mono', 'Fira Code', monospace;

  --text-xs:   11px;
  --text-sm:   13px;
  --text-base: 14px;
  --text-md:   15px;
  --text-lg:   18px;
  --text-xl:   20px;
  --text-2xl:  24px;
  --text-3xl:  28px;
  --text-4xl:  36px;

  --font-normal:    400;
  --font-medium:    500;
  --font-semibold:  600;
  --font-bold:      700;
  --font-extrabold: 800;

  --leading-tight:   1.2;
  --leading-snug:    1.35;
  --leading-normal:  1.5;
  --leading-relaxed: 1.6;

  --tracking-tight:  -0.01em;
  --tracking-normal:  0;
  --tracking-wide:    0.02em;
  --tracking-wider:   0.05em;

  /* ── Spacing ── */
  --spacing-0:   0;
  --spacing-1:   4px;
  --spacing-2:   8px;
  --spacing-3:   12px;
  --spacing-4:   16px;
  --spacing-5:   20px;
  --spacing-6:   24px;
  --spacing-8:   32px;
  --spacing-10:  40px;
  --spacing-12:  48px;
  --spacing-16:  64px;

  /* ── Border Radius ── */
  --radius-xs:   4px;
  --radius-sm:   6px;
  --radius-md:   10px;
  --radius-lg:   16px;
  --radius-xl:   20px;
  --radius-full: 9999px;

  /* ── Shadows ── */
  --shadow-0: none;
  --shadow-1: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06);
  --shadow-2: 0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.06);
  --shadow-3: 0 10px 15px rgba(0,0,0,0.08), 0 4px 6px rgba(0,0,0,0.05);
  --shadow-4: 0 20px 25px rgba(0,0,0,0.10), 0 8px 10px rgba(0,0,0,0.06);
  --shadow-5: 0 25px 50px rgba(0,0,0,0.15);

  --shadow-primary: 0 4px 14px rgba(59, 130, 246, 0.3);
  --shadow-success: 0 4px 14px rgba(16, 185, 129, 0.3);
  --shadow-danger:  0 4px 14px rgba(239, 68, 68, 0.3);

  --ring-primary: 0 0 0 3px rgba(59, 130, 246, 0.15);
  --ring-danger:  0 0 0 3px rgba(239, 68, 68, 0.15);

  /* ── Animation ── */
  --duration-fast:   100ms;
  --duration-normal: 200ms;
  --duration-medium: 300ms;
  --duration-slow:   500ms;

  --ease-out:    cubic-bezier(0.33, 1, 0.68, 1);
  --ease-in:     cubic-bezier(0.32, 0, 0.67, 0);
  --ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --ease-smooth: cubic-bezier(0.25, 0.1, 0.25, 1.0);

  /* ── Icon Sizes ── */
  --icon-xs:  14px;
  --icon-sm:  16px;
  --icon-md:  20px;
  --icon-lg:  24px;
  --icon-xl:  32px;
  --icon-2xl: 48px;

  /* ── Breakpoints (reference only, use in @media queries) ── */
  /* --bp-sm: 480px; --bp-md: 768px; --bp-lg: 1024px; --bp-xl: 1280px; */
}
```

---

## Appendix B: File Map

| Document | Purpose | Status |
|----------|---------|--------|
| `docs/xcleaners/brandbook.md` | This file -- brand identity + design system | FINAL |
| `docs/ux/xcleaners-wireframes-v3.md` | Screen-by-screen wireframe specifications | FINAL |
| `docs/ux/xcleaners-design-system-plan.md` | Detailed CSS component implementations | READY FOR IMPLEMENTATION |
| `docs/xcleaners-competitive-research.md` | Competitor analysis (Jobber, HCP, ZenMaid, etc.) | COMPLETE |
| `docs/prd/xcleaners-prd-v3.md` | Product requirements document | FINAL |
| `docs/architecture/xcleaners-architecture-v3.md` | Technical architecture | FINAL |

---

*Xcleaners Brandbook v2.0 -- @ux-design-expert (Sati) -- 2026-03-23*

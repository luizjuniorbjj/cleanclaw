/**
 * CleanClaw — Demo Data Provider
 * Provides realistic mock data when API is unavailable (demo mode).
 * Intercepts CleanAPI responses and returns mock data for empty responses.
 */

// Helper: generate dates without referencing DemoData
function _demoFuture(days) { const d = new Date(); d.setDate(d.getDate() + days); return d.toISOString().split('T')[0]; }
function _demoPast(days) { const d = new Date(); d.setDate(d.getDate() - days); return d.toISOString().split('T')[0]; }

window.DemoData = {
  // Persistence: save/load modified data to localStorage
  _persistKeys: ['_teams', '_clients', '_services'],

  _saveToStorage() {
    try {
      for (const key of this._persistKeys) {
        if (this[key]) localStorage.setItem('cc_demo' + key, JSON.stringify(this[key]));
      }
      if (this._bookings) localStorage.setItem('cc_demo_bookings', JSON.stringify(this._bookings));
    } catch { /* localStorage full or unavailable */ }
  },

  _loadFromStorage() {
    try {
      for (const key of this._persistKeys) {
        const saved = localStorage.getItem('cc_demo' + key);
        if (saved) {
          const parsed = JSON.parse(saved);
          if (Array.isArray(parsed) && parsed.length > 0) this[key] = parsed;
        }
      }
      const savedBookings = localStorage.getItem('cc_demo_bookings');
      if (savedBookings) {
        const parsed = JSON.parse(savedBookings);
        if (Array.isArray(parsed) && parsed.length > 0) this._bookings = parsed;
      }
    } catch { /* corrupted data, ignore */ }
  },

  // Event bus for cross-screen data synchronization
  _listeners: {},

  on(event, callback) {
    if (!this._listeners[event]) this._listeners[event] = [];
    this._listeners[event].push(callback);
  },

  off(event, callback) {
    if (!this._listeners[event]) return;
    this._listeners[event] = this._listeners[event].filter(cb => cb !== callback);
  },

  emit(event, data) {
    (this._listeners[event] || []).forEach(cb => {
      try { cb(data); } catch (e) { console.error('[DemoData] Event listener error:', e); }
    });
    if (event === 'dataChanged') this._saveToStorage();
  },

  _businesses: [
    { id: 'biz-1', name: 'Clean New Orleans', owner_email: 'admin@cleanneworleans.com', plan: 'pro', status: 'active', city: 'New Orleans', state: 'LA', created_at: '2026-03-01', teams: 3, clients: 5, cleaners: 7, mrr: 49 },
    { id: 'biz-2', name: 'Sparkle Miami', owner_email: 'owner@sparklemiami.com', plan: 'business', status: 'active', city: 'Miami', state: 'FL', created_at: '2026-02-15', teams: 5, clients: 45, cleaners: 12, mrr: 99 },
    { id: 'biz-3', name: 'Fresh Start Houston', owner_email: 'admin@freshstarthouston.com', plan: 'basic', status: 'trial', city: 'Houston', state: 'TX', created_at: '2026-03-20', teams: 1, clients: 8, cleaners: 3, mrr: 0 },
  ],

  _teams: [
    { id: 'team-1', name: 'Team Alpha', color: '#1A73E8', is_active: true, max_daily_jobs: 6, member_count: 3,
      members: [
        { id: 'm1', name: 'Maria Santos', role: 'team_lead', email: 'maria@xcleaners.app', phone: '(504) 555-0101', is_active: true },
        { id: 'm2', name: 'Ana Rodriguez', role: 'cleaner', email: 'ana@xcleaners.app', phone: '(504) 555-0102', is_active: true },
        { id: 'm3', name: 'Carlos Mendez', role: 'cleaner', email: 'carlos@xcleaners.app', phone: '(504) 555-0103', is_active: true },
      ]},
    { id: 'team-2', name: 'Team Beta', color: '#10B981', is_active: true, max_daily_jobs: 5, member_count: 2,
      members: [
        { id: 'm4', name: 'Rosa Martinez', role: 'team_lead', email: 'rosa@xcleaners.app', phone: '(504) 555-0201', is_active: true },
        { id: 'm5', name: 'Jorge Silva', role: 'cleaner', email: 'jorge@xcleaners.app', phone: '(504) 555-0202', is_active: true },
      ]},
    { id: 'team-3', name: 'Team Gamma', color: '#F59E0B', is_active: false, max_daily_jobs: 4, member_count: 2,
      members: [
        { id: 'm6', name: 'Luis Perez', role: 'team_lead', email: 'luis@xcleaners.app', phone: '(504) 555-0301', is_active: true },
        { id: 'm7', name: 'Diana Cruz', role: 'cleaner', email: 'diana@xcleaners.app', phone: '(504) 555-0302', is_active: false },
      ]},
  ],

  _clients: [
    { id: 'c1', first_name: 'Sarah', last_name: 'Johnson', email: 'sarah.j@email.com', phone: '(504) 555-1001',
      address: '1234 Magazine St', city: 'New Orleans', state: 'LA', zip: '70130',
      status: 'active', frequency: 'weekly', property_type: 'house', bedrooms: 3, bathrooms: 2, sqft: 1800,
      tags: ['recurring', 'premium'], notes: 'Has dog, use pet-safe products', next_booking: _demoFuture(2),
      created_at: '2026-01-15T10:00:00Z' },
    { id: 'c2', first_name: 'Michael', last_name: 'Williams', email: 'mwilliams@email.com', phone: '(504) 555-1002',
      address: '567 St Charles Ave', city: 'New Orleans', state: 'LA', zip: '70115',
      status: 'active', frequency: 'biweekly', property_type: 'condo', bedrooms: 2, bathrooms: 1, sqft: 1200,
      tags: ['recurring'], notes: '', next_booking: _demoFuture(5),
      created_at: '2026-02-01T10:00:00Z' },
    { id: 'c3', first_name: 'Emily', last_name: 'Davis', email: 'emily.d@email.com', phone: '(504) 555-1003',
      address: '890 Esplanade Ave', city: 'New Orleans', state: 'LA', zip: '70116',
      status: 'active', frequency: 'monthly', property_type: 'apartment', bedrooms: 1, bathrooms: 1, sqft: 800,
      tags: [], notes: 'Gate code: 4521', next_booking: _demoFuture(12),
      created_at: '2026-02-10T10:00:00Z' },
    { id: 'c4', first_name: 'James', last_name: 'Brown', email: 'jbrown@email.com', phone: '(504) 555-1004',
      address: '2345 Napoleon Ave', city: 'New Orleans', state: 'LA', zip: '70115',
      status: 'active', frequency: 'weekly', property_type: 'house', bedrooms: 4, bathrooms: 3, sqft: 2800,
      tags: ['recurring', 'premium', 'large-home'], notes: 'Deep clean kitchen every visit', next_booking: _demoFuture(1),
      created_at: '2026-01-20T10:00:00Z' },
    { id: 'c5', first_name: 'Lisa', last_name: 'Garcia', email: 'lisag@email.com', phone: '(504) 555-1005',
      address: '678 Frenchmen St', city: 'New Orleans', state: 'LA', zip: '70116',
      status: 'paused', frequency: 'biweekly', property_type: 'townhouse', bedrooms: 2, bathrooms: 2, sqft: 1500,
      tags: [], notes: 'On vacation until April', next_booking: null,
      created_at: '2026-03-01T10:00:00Z' },
  ],

  _services: [
    { id: 's1', name: 'Standard Cleaning', slug: 'standard', category: 'residential', base_price: 120.00, price_unit: 'flat', estimated_duration_minutes: 120, min_team_size: 2, is_active: true, sort_order: 1 },
    { id: 's2', name: 'Deep Cleaning', slug: 'deep', category: 'residential', base_price: 200.00, price_unit: 'flat', estimated_duration_minutes: 180, min_team_size: 2, is_active: true, sort_order: 2 },
    { id: 's3', name: 'Move In/Out', slug: 'move', category: 'residential', base_price: 250.00, price_unit: 'flat', estimated_duration_minutes: 240, min_team_size: 3, is_active: true, sort_order: 3 },
    { id: 's4', name: 'Post Construction', slug: 'post-construction', category: 'commercial', base_price: 300.00, price_unit: 'flat', estimated_duration_minutes: 300, min_team_size: 3, is_active: true, sort_order: 4 },
    { id: 's5', name: 'Window Cleaning', slug: 'windows', category: 'addon', base_price: 50.00, price_unit: 'per_unit', estimated_duration_minutes: 60, min_team_size: 1, is_active: true, sort_order: 5 },
  ],

  _bookings: null, // generated dynamically

  _invoices: null, // generated dynamically

  // ---- Helpers ----

  _futureDate(daysFromNow) {
    const d = new Date();
    d.setDate(d.getDate() + daysFromNow);
    return d.toISOString().split('T')[0];
  },

  _pastDate(daysAgo) {
    const d = new Date();
    d.setDate(d.getDate() - daysAgo);
    return d.toISOString().split('T')[0];
  },

  _todayStr() {
    return new Date().toISOString().split('T')[0];
  },

  _generateBookings() {
    if (this._bookings) return this._bookings;
    const today = this._todayStr();
    const bookings = [];
    let id = 1;

    // Realistic week schedule: 3 teams, ~4-5 jobs/day each, no conflicts
    const schedule = [
      // TODAY
      { day: 0, team: 1, client: 'c1', time: '08:00', end: '10:00', svc: 'Standard Cleaning', status: 'in_progress', checkin: true },
      { day: 0, team: 1, client: 'c4', time: '11:00', end: '14:00', svc: 'Deep Cleaning', status: 'scheduled' },
      { day: 0, team: 1, client: 'c2', time: '15:00', end: '17:00', svc: 'Standard Cleaning', status: 'scheduled' },
      { day: 0, team: 2, client: 'c3', time: '08:30', end: '10:30', svc: 'Standard Cleaning', status: 'completed', checkout: true },
      { day: 0, team: 2, client: 'c5', time: '11:00', end: '13:00', svc: 'Standard Cleaning', status: 'scheduled' },
      // TOMORROW
      { day: 1, team: 1, client: 'c4', time: '08:00', end: '10:00', svc: 'Standard Cleaning', status: 'scheduled' },
      { day: 1, team: 1, client: 'c1', time: '11:00', end: '13:00', svc: 'Standard Cleaning', status: 'scheduled' },
      { day: 1, team: 2, client: 'c2', time: '09:00', end: '11:00', svc: 'Standard Cleaning', status: 'scheduled' },
      { day: 1, team: 2, client: 'c3', time: '13:00', end: '15:00', svc: 'Deep Cleaning', status: 'scheduled' },
      // DAY +2
      { day: 2, team: 1, client: 'c1', time: '08:00', end: '10:00', svc: 'Standard Cleaning', status: 'scheduled' },
      { day: 2, team: 1, client: 'c5', time: '11:00', end: '13:00', svc: 'Standard Cleaning', status: 'scheduled' },
      { day: 2, team: 2, client: 'c4', time: '08:00', end: '11:00', svc: 'Deep Cleaning', status: 'scheduled' },
      { day: 2, team: 2, client: 'c2', time: '12:00', end: '14:00', svc: 'Standard Cleaning', status: 'scheduled' },
      // DAY +3
      { day: 3, team: 1, client: 'c3', time: '08:00', end: '10:00', svc: 'Standard Cleaning', status: 'scheduled' },
      { day: 3, team: 1, client: 'c4', time: '11:00', end: '14:00', svc: 'Move In/Out', status: 'scheduled' },
      { day: 3, team: 2, client: 'c1', time: '09:00', end: '11:00', svc: 'Standard Cleaning', status: 'scheduled' },
      // DAY +4
      { day: 4, team: 1, client: 'c2', time: '08:00', end: '10:00', svc: 'Standard Cleaning', status: 'scheduled' },
      { day: 4, team: 1, client: 'c5', time: '11:00', end: '13:30', svc: 'Deep Cleaning', status: 'scheduled' },
      { day: 4, team: 2, client: 'c4', time: '08:00', end: '10:00', svc: 'Standard Cleaning', status: 'scheduled' },
      { day: 4, team: 2, client: 'c1', time: '11:00', end: '13:00', svc: 'Standard Cleaning', status: 'scheduled' },
      // DAY +5
      { day: 5, team: 1, client: 'c1', time: '08:00', end: '10:00', svc: 'Standard Cleaning', status: 'scheduled' },
      { day: 5, team: 1, client: 'c3', time: '11:00', end: '13:00', svc: 'Standard Cleaning', status: 'scheduled' },
      { day: 5, team: 2, client: 'c2', time: '09:00', end: '11:00', svc: 'Standard Cleaning', status: 'scheduled' },
      // DAY +6
      { day: 6, team: 1, client: 'c4', time: '09:00', end: '12:00', svc: 'Deep Cleaning', status: 'scheduled' },
      { day: 6, team: 2, client: 'c5', time: '10:00', end: '12:00', svc: 'Standard Cleaning', status: 'scheduled' },
      // PAST DAYS (completed)
      { day: -1, team: 1, client: 'c1', time: '08:00', end: '10:00', svc: 'Standard Cleaning', status: 'completed', checkout: true },
      { day: -1, team: 1, client: 'c2', time: '11:00', end: '13:00', svc: 'Standard Cleaning', status: 'completed', checkout: true },
      { day: -1, team: 2, client: 'c4', time: '09:00', end: '12:00', svc: 'Deep Cleaning', status: 'completed', checkout: true },
      { day: -2, team: 1, client: 'c3', time: '08:00', end: '10:00', svc: 'Standard Cleaning', status: 'completed', checkout: true },
      { day: -2, team: 2, client: 'c1', time: '09:00', end: '11:00', svc: 'Standard Cleaning', status: 'completed', checkout: true },
      { day: -2, team: 2, client: 'c5', time: '12:00', end: '14:00', svc: 'Standard Cleaning', status: 'completed', checkout: true },
    ];

    const teams = { 1: this._teams[0], 2: this._teams[1] };

    for (const s of schedule) {
      const client = this._clients.find(c => c.id === s.client) || {};
      const team = teams[s.team];
      const d = new Date();
      d.setDate(d.getDate() + s.day);
      const dateStr = d.toISOString().split('T')[0];

      bookings.push({
        id: `b${id}`,
        client_id: s.client,
        client_name: `${client.first_name || ''} ${client.last_name || ''}`.trim() || 'Client',
        team_id: team.id,
        team_name: team.name,
        team_color: team.color,
        service: s.svc,
        scheduled_date: dateStr,
        scheduled_start: s.time,
        scheduled_end: s.end,
        status: s.status,
        address: `${client.address || '123 Main St'}, ${client.city || 'New Orleans'}, ${client.state || 'LA'} ${client.zip || '70130'}`,
        notes: client.notes || '',
        checkin_at: s.checkin ? new Date().toISOString() : null,
        checkout_at: s.checkout ? new Date().toISOString() : null,
      });
      id++;
    }

    this._bookings = bookings;
    return this._bookings;
  },

  _generateInvoices() {
    if (this._invoices) return this._invoices;
    this._invoices = [
      { id: 'inv-1', invoice_number: 'INV-001', client_id: 'c1', client_name: 'Sarah Johnson',
        total: 120.00, balance_due: 0, status: 'paid', due_date: this._pastDate(15), paid_at: this._pastDate(14),
        created_at: this._pastDate(20), items: [{ service: 'Standard Cleaning', amount: 120.00 }] },
      { id: 'inv-2', invoice_number: 'INV-002', client_id: 'c4', client_name: 'James Brown',
        total: 200.00, balance_due: 0, status: 'paid', due_date: this._pastDate(8), paid_at: this._pastDate(7),
        created_at: this._pastDate(15), items: [{ service: 'Deep Cleaning', amount: 200.00 }] },
      { id: 'inv-3', invoice_number: 'INV-003', client_id: 'c2', client_name: 'Michael Williams',
        total: 120.00, balance_due: 120.00, status: 'sent', due_date: this._futureDate(7),
        created_at: this._pastDate(3), items: [{ service: 'Standard Cleaning', amount: 120.00 }] },
      { id: 'inv-4', invoice_number: 'INV-004', client_id: 'c3', client_name: 'Emily Davis',
        total: 120.00, balance_due: 120.00, status: 'overdue', due_date: this._pastDate(5),
        created_at: this._pastDate(20), items: [{ service: 'Standard Cleaning', amount: 120.00 }] },
      { id: 'inv-5', invoice_number: 'INV-005', client_id: 'c1', client_name: 'Sarah Johnson',
        total: 120.00, balance_due: 120.00, status: 'draft', due_date: this._futureDate(15),
        created_at: this._pastDate(1), items: [{ service: 'Standard Cleaning', amount: 120.00 }] },
    ];
    return this._invoices;
  },

  // ---- Dashboard ----

  getDashboard() {
    const bookings = this._generateBookings();
    const todayBookings = bookings.filter(b => b.scheduled_date === this._todayStr());
    const invoices = this._generateInvoices();
    const paidThisMonth = invoices.filter(i => i.status === 'paid');
    const overdue = invoices.filter(i => i.status === 'overdue');

    return {
      today_bookings_count: todayBookings.length,
      bookings_today: {
        total: todayBookings.length,
        completed: todayBookings.filter(b => b.status === 'completed').length,
      },
      active_clients: this._clients.filter(c => c.status === 'active').length,
      active_teams: this._teams.filter(t => t.is_active).length,
      revenue_this_month: paidThisMonth.reduce((s, i) => s + i.total, 0),
      month_revenue: paidThisMonth.reduce((s, i) => s + i.total, 0),
      revenue_change_pct: 12.5,
      overdue_invoices: {
        count: overdue.length,
        total_amount: overdue.reduce((s, i) => s + i.balance_due, 0),
      },
      date: new Date().toISOString(),
    };
  },

  getDashboardTeams() {
    return this._teams.filter(t => t.is_active).map(t => {
      const bookings = this._generateBookings().filter(b => b.team_id === t.id && b.scheduled_date === this._todayStr());
      return {
        team_id: t.id, team_name: t.name, team_color: t.color,
        today: {
          total_jobs: bookings.length,
          completed: bookings.filter(b => b.status === 'completed').length,
          in_progress: bookings.filter(b => b.status === 'in_progress').length,
          total_hours: bookings.length * 2,
        },
      };
    });
  },

  getDashboardRevenue(period) {
    const days = period === 'week' ? 7 : period === 'quarter' ? 90 : 30;
    const data = [];
    for (let i = days - 1; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      data.push({
        date: d.toISOString().split('T')[0],
        revenue: Math.round(Math.random() * 300 + 50),
      });
    }
    return { data, total_revenue: data.reduce((s, d) => s + d.revenue, 0), period };
  },

  // ---- Teams ----

  getTeams() { return this._teams; },

  getTeamDetail(teamId) {
    const team = this._teams.find(t => t.id === teamId);
    if (!team) return { members: [], stats: {} };
    const bookings = this._generateBookings().filter(b => b.team_id === teamId);
    const todayBookings = bookings.filter(b => b.scheduled_date === this._todayStr());
    return {
      ...team,
      members: (team.members || []).map((m, i) => ({
        ...m, team_id: team.id, team_name: team.name,
        role_in_team: i === 0 ? 'lead' : 'member',
      })),
      stats: {
        jobs_today: todayBookings.length,
        jobs_this_week: bookings.length,
        hours_this_week: bookings.length * 2,
      },
    };
  },

  getMembers() { return this._teams.flatMap(t => t.members.map(m => ({ ...m, team_id: t.id, team_name: t.name }))); },

  // ---- Clients ----

  getClients(page = 1, perPage = 25) {
    // Map raw client fields to API-compatible names for client-manager
    const mapped = this._clients.map(c => ({
      ...c,
      address_line1: c.address_line1 || c.address || '',
      zip_code: c.zip_code || c.zip || '',
      square_feet: c.square_feet || c.sqft || 0,
      lifetime_value: c.lifetime_value || 0,
      total_bookings: c.total_bookings || 0,
      active_schedules_count: c.active_schedules_count || (c.frequency ? 1 : 0),
    }));
    return {
      clients: mapped,
      total: mapped.length,
      page, per_page: perPage,
      total_pages: 1,
    };
  },

  // ---- Services ----

  getServices() { return this._services; },

  // ---- Invoices ----

  getInvoices() {
    const inv = this._generateInvoices();
    return { invoices: inv, total: inv.length, page: 1, per_page: 50, total_pages: 1 };
  },

  getPaymentDashboard() {
    const inv = this._generateInvoices();
    const paid = inv.filter(i => i.status === 'paid');
    const outstanding = inv.filter(i => ['sent', 'draft'].includes(i.status));
    const overdue = inv.filter(i => i.status === 'overdue');
    return {
      revenue_this_month: paid.reduce((s, i) => s + i.total, 0),
      outstanding: outstanding.reduce((s, i) => s + i.balance_due, 0),
      overdue_amount: overdue.reduce((s, i) => s + i.balance_due, 0),
      overdue_count: overdue.length,
    };
  },

  // ---- Schedule ----

  getScheduleSummary() {
    const bookings = this._generateBookings();
    const today = bookings.filter(b => b.scheduled_date === this._todayStr());
    const teamsActive = this._teams.filter(t => t.is_active).length;
    return {
      today: {
        total: today.length,
        active_jobs: today.length,
        completed: today.filter(b => b.status === 'completed').length,
        in_progress: today.filter(b => b.status === 'in_progress').length,
        unassigned: 0,
        unassigned_jobs: 0,
        revenue: today.length * 120,
        teams_active: teamsActive,
      },
      teams_active: teamsActive,
    };
  },

  getCalendarEvents() {
    return this._generateBookings().map(b => ({
      id: b.id,
      title: `${b.client_name} - ${b.service}`,
      start: `${b.scheduled_date}T${b.scheduled_start}`,
      end: `${b.scheduled_date}T${b.scheduled_end}`,
      color: b.team_color,
      extendedProps: b,
    }));
  },

  // ---- Team/Cleaner views ----

  getTodayJobs() {
    const bookings = this._generateBookings().filter(b => b.scheduled_date === this._todayStr());
    return {
      jobs: bookings,
      summary: {
        total: bookings.length,
        completed: bookings.filter(b => b.status === 'completed').length,
        active: bookings.filter(b => b.status === 'in_progress').length,
      },
    };
  },

  getWeekSchedule() {
    const days = {};
    for (let i = 0; i < 7; i++) {
      const d = new Date();
      d.setDate(d.getDate() - d.getDay() + i); // Start from Sunday
      const dateStr = d.toISOString().split('T')[0];
      const bookings = this._generateBookings().filter(b => b.scheduled_date === dateStr);
      days[dateStr] = bookings;
    }
    return { days };
  },

  getEarnings(period) {
    const days = period === 'week' ? 7 : period === 'year' ? 365 : 30;
    const daily = [];
    let total = 0;
    for (let i = days - 1; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const jobs = Math.floor(Math.random() * 4);
      const amount = jobs * 45;
      total += amount;
      daily.push({
        date: d.toISOString().split('T')[0],
        jobs,
        hours: jobs * 2.5,
        amount,
      });
    }
    return {
      total,
      this_week: daily.slice(-7).reduce((s, d) => s + d.amount, 0),
      this_month: total,
      jobs_completed: daily.reduce((s, d) => s + d.jobs, 0),
      daily,
    };
  },

  // ---- Homeowner views ----

  getMyBookings() {
    const bookings = this._generateBookings();
    return {
      upcoming: bookings.filter(b => b.status !== 'completed').map(b => ({
        ...b, service_name: b.service, team: { name: b.team_name, color: b.team_color },
      })),
      past: bookings.filter(b => b.status === 'completed').map(b => ({
        ...b, service_name: b.service, team: { name: b.team_name, color: b.team_color },
      })),
    };
  },

  getMyInvoices() {
    const inv = this._generateInvoices();
    return {
      total_due: inv.filter(i => i.balance_due > 0).reduce((s, i) => s + i.balance_due, 0),
      invoices: inv,
    };
  },

  getPreferences() {
    return {
      name: 'John Smith',
      email: 'donocasa@xcleaners.app',
      phone: '(504) 555-9000',
      address: {
        line1: '1234 Magazine St',
        line2: 'Unit A',
        city: 'New Orleans',
        state: 'LA',
        zip: '70130',
      },
      property: {
        type: 'house',
        square_feet: 1800,
        bedrooms: 3,
        bathrooms: 2,
      },
      pets: {
        has_pets: true,
        details: '1 small dog (friendly)',
      },
      instructions: {
        access: 'Key under the mat. Gate code: 4521',
        special: 'Please use eco-friendly products. No shoes inside.',
      },
      scheduling: {
        preferred_day: 'monday',
        preferred_time: '09:00',
        communication_preference: 'email',
      },
    };
  },

  // ---- Onboarding ----

  getOnboardingTemplates() {
    return {
      templates: this._services.map(s => ({
        ...s,
        slug: s.slug,
        suggested_base_price: s.base_price,
      })),
    };
  },

  // ---- Settings ----

  getSettings() {
    // Check localStorage for persisted settings first
    try {
      const saved = localStorage.getItem('cc_demo_settings');
      if (saved) return JSON.parse(saved);
    } catch (e) { /* ok */ }
    return {
      business_profile: {
        name: 'Clean New Orleans',
        email: 'info@cleanneworleans.com',
        phone: '(504) 555-0000',
        address: '100 Poydras St, New Orleans, LA 70163',
      },
      settings: {
        business_hours_start: '07:00',
        business_hours_end: '18:00',
        cancellation_policy_hours: 24,
        default_payment_terms_days: 15,
        timezone: 'America/Chicago',
        auto_schedule: true,
        auto_invoice: false,
      },
    };
  },

  getClientDetail(clientId) {
    const client = this._clients.find(c => c.id === clientId);
    if (!client) return null;
    const bookings = this._generateBookings().filter(b => b.client_id === clientId);
    const invoices = this._generateInvoices().invoices.filter(i => i.client_id === clientId);
    return {
      ...client,
      // Map fields to what client-detail.js expects (handle both old and new field names)
      address_line1: client.address_line1 || client.address || '',
      address_line2: client.address_line2 || '',
      zip_code: client.zip_code || client.zip || '',
      square_feet: client.square_feet || client.sqft || 0,
      preferred_contact: client.preferred_contact || (client.email ? 'email' : 'phone'),
      has_pets: client.has_pets || false,
      pet_details: client.pet_details || '',
      access_instructions: client.access_instructions || '',
      internal_notes: client.internal_notes || client.notes || '',
      lifetime_value: client.lifetime_value || 0,
      total_bookings: client.total_bookings || bookings.length,
      last_service_date: client.last_service_date || null,
      schedules: [{ id: 'sched1', frequency: client.frequency || 'weekly', day_of_week: 'monday', preferred_time: '09:00', service_name: 'Standard Cleaning', is_active: true }],
      upcoming_bookings: bookings.filter(b => b.status !== 'completed').slice(0, 5),
      past_bookings: bookings.filter(b => b.status === 'completed').slice(0, 10),
      invoices: invoices,
      financial_summary: {
        total_invoiced: invoices.reduce((s, i) => s + i.total, 0),
        total_paid: invoices.filter(i => i.status === 'paid').reduce((s, i) => s + i.total, 0),
        balance_due: invoices.reduce((s, i) => s + (i.balance_due || 0), 0),
        lifetime_value: invoices.filter(i => i.status === 'paid').reduce((s, i) => s + i.total, 0),
      },
    };
  },

  getAreas() {
    // Check localStorage for persisted areas first
    if (this._demoAreas) return this._demoAreas;
    try {
      const saved = localStorage.getItem('cc_demo_areas');
      if (saved) { this._demoAreas = JSON.parse(saved); return this._demoAreas; }
    } catch (e) { /* ok */ }
    return [
      { id: 'a1', name: 'French Quarter / CBD', zip_codes: ['70112', '70116', '70130'], city: 'New Orleans', state: 'LA', is_active: true },
      { id: 'a2', name: 'Uptown / Garden District', zip_codes: ['70115', '70118'], city: 'New Orleans', state: 'LA', is_active: true },
      { id: 'a3', name: 'Mid-City / Gentilly', zip_codes: ['70119', '70122', '70125'], city: 'New Orleans', state: 'LA', is_active: true },
      { id: 'a4', name: 'Lakeview / Metairie', zip_codes: ['70124', '70001', '70002'], city: 'New Orleans', state: 'LA', is_active: false },
    ];
  },

  // ---- Job Detail ----

  getJobDetail(jobId) {
    const bookings = this._generateBookings();
    const job = bookings.find(b => b.id === jobId);
    if (!job) return null;

    const client = this._clients.find(c => c.id === job.client_id) || {};
    const svc = this._services.find(s => s.name === job.service) || {};
    return {
      ...job,
      id: job.id,
      client: {
        id: client.id,
        name: `${client.first_name || ''} ${client.last_name || ''}`.trim() || job.client_name,
        phone: client.phone || '(504) 555-0000',
        address: job.address,
        access_instructions: client.notes || '',
        has_pets: !!client.notes?.includes('dog'),
        pet_details: client.notes?.includes('dog') ? 'Small dog (friendly)' : null,
      },
      location: {
        address: job.address,
        access_instructions: client.notes || '',
      },
      service: {
        name: job.service,
        estimated_duration: svc.estimated_duration_minutes || 120,
      },
      service_name: job.service,
      team: { name: job.team_name, color: job.team_color },
      checklist: [
        { id: 'cl1', room: 'Kitchen', task: 'Clean countertops', completed: job.status === 'completed' },
        { id: 'cl2', room: 'Kitchen', task: 'Mop floor', completed: job.status === 'completed' },
        { id: 'cl3', room: 'Kitchen', task: 'Clean appliances', completed: false },
        { id: 'cl4', room: 'Bathroom', task: 'Scrub tub/shower', completed: job.status === 'completed' },
        { id: 'cl5', room: 'Bathroom', task: 'Clean toilet', completed: job.status === 'completed' },
        { id: 'cl6', room: 'Bathroom', task: 'Mop floor', completed: false },
        { id: 'cl7', room: 'Living Room', task: 'Vacuum carpet', completed: false },
        { id: 'cl8', room: 'Living Room', task: 'Dust furniture', completed: false },
        { id: 'cl9', room: 'Bedrooms', task: 'Change linens', completed: false },
        { id: 'cl10', room: 'Bedrooms', task: 'Vacuum', completed: false },
      ],
      logs: job.status !== 'scheduled' ? [
        { id: 'log1', log_type: 'note', note: 'Arrived on time. Client left key under mat.', created_at: new Date().toISOString() },
      ] : [],
      special_instructions: client.notes || 'No special instructions',
      estimated_duration: 120,
      checkin_at: job.checkin_at || null,
      checkout_at: job.checkout_at || null,
    };
  },

  // ---- Write Handler ----
  // Handles POST/PATCH/PUT/DELETE in demo mode by mutating in-memory data.
  // Returns the result object, or null if the path is not handled.

  handleWrite(method, path, body) {
    const result = this._doHandleWrite(method, path, body);
    if (result !== null) this._saveToStorage();
    return result;
  },

  _doHandleWrite(method, path, body) {
    const p = path.replace(/\?.*$/, ''); // strip query params
    body = body || {};

    // ============================
    // CLIENTS
    // ============================

    // POST /clients — create new client
    if (method === 'POST' && /\/clients\/?$/.test(p) && !p.includes('/schedules') && !p.includes('/invite')) {
      const newClient = {
        id: 'c-' + Date.now(),
        first_name: body.first_name || '',
        last_name: body.last_name || '',
        email: body.email || '',
        phone: body.phone || '',
        address: body.address || body.address_line1 || '',
        city: body.city || 'New Orleans',
        state: body.state || 'LA',
        zip: body.zip || body.zip_code || '',
        status: 'active',
        frequency: body.frequency || 'weekly',
        property_type: body.property_type || 'house',
        bedrooms: body.bedrooms || 0,
        bathrooms: body.bathrooms || 0,
        sqft: body.sqft || body.square_feet || 0,
        tags: body.tags || [],
        notes: body.notes || '',
        next_booking: null,
        created_at: new Date().toISOString(),
        ...body,
      };
      // Ensure id is ours, not from body
      newClient.id = 'c-' + Date.now();
      this._clients.push(newClient);
      console.log('[DemoData] Created client:', newClient.id);
      this.emit('dataChanged', { type: 'client', action: 'create', data: newClient });
      return newClient;
    }

    // PATCH /clients/{id} — update client
    if (method === 'PATCH' && /\/clients\/[\w-]+$/.test(p) && !p.includes('/schedules') && !p.includes('/cancel') && !p.includes('/reschedule')) {
      const id = p.split('/clients/')[1];
      const idx = this._clients.findIndex(c => c.id === id);
      if (idx >= 0) {
        this._clients[idx] = { ...this._clients[idx], ...body, updated_at: new Date().toISOString() };
        console.log('[DemoData] Updated client:', id);
        return this._clients[idx];
      }
      return { id, ...body };
    }

    // DELETE /clients/{id} — remove client
    if (method === 'DELETE' && /\/clients\/[\w-]+$/.test(p) && !p.includes('/schedules') && !p.includes('/members')) {
      const id = p.split('/clients/')[1];
      this._clients = this._clients.filter(c => c.id !== id);
      console.log('[DemoData] Deleted client:', id);
      return { success: true };
    }

    // POST /clients/{id}/schedules — add schedule
    if (method === 'POST' && /\/clients\/[\w-]+\/schedules$/.test(p)) {
      const cid = p.split('/clients/')[1].split('/')[0];
      const schedule = {
        id: 'sched-' + Date.now(),
        client_id: cid,
        frequency: body.frequency || 'weekly',
        day_of_week: body.day_of_week || 'monday',
        preferred_time: body.preferred_time || '09:00',
        service_name: body.service_name || 'Standard Cleaning',
        service_id: body.service_id || null,
        is_active: true,
        created_at: new Date().toISOString(),
        ...body,
      };
      schedule.id = 'sched-' + Date.now();
      console.log('[DemoData] Created schedule for client:', cid);
      return schedule;
    }

    // PATCH /clients/{id}/schedules/{sid} — update schedule
    if (method === 'PATCH' && /\/clients\/[\w-]+\/schedules\/[\w-]+$/.test(p)) {
      console.log('[DemoData] Updated schedule');
      return { ...body, updated_at: new Date().toISOString() };
    }

    // DELETE /clients/{id}/schedules/{sid} — remove schedule
    if (method === 'DELETE' && /\/clients\/[\w-]+\/schedules\/[\w-]+$/.test(p)) {
      console.log('[DemoData] Deleted schedule');
      return { success: true };
    }

    // POST /clients/{id}/schedules/{sid}/pause
    if (method === 'POST' && /\/clients\/[\w-]+\/schedules\/[\w-]+\/pause$/.test(p)) {
      console.log('[DemoData] Paused schedule');
      return { success: true, is_active: false };
    }

    // POST /clients/{id}/schedules/{sid}/resume
    if (method === 'POST' && /\/clients\/[\w-]+\/schedules\/[\w-]+\/resume$/.test(p)) {
      console.log('[DemoData] Resumed schedule');
      return { success: true, is_active: true };
    }

    // POST /clients/{id}/invite — send client invite
    if (method === 'POST' && /\/clients\/[\w-]+\/invite$/.test(p)) {
      console.log('[DemoData] Sent client invite');
      return { success: true, message: 'Invitation sent' };
    }

    // ============================
    // TEAMS
    // ============================

    // POST /teams — create team
    if (method === 'POST' && /\/teams\/?$/.test(p) && !p.includes('/members') && !p.includes('/lead') && !p.includes('/invite')) {
      const newTeam = {
        id: 'team-' + Date.now(),
        name: body.name || 'New Team',
        color: body.color || '#6366F1',
        is_active: true,
        max_daily_jobs: body.max_daily_jobs || 5,
        member_count: 0,
        members: [],
        ...body,
      };
      newTeam.id = 'team-' + Date.now();
      this._teams.push(newTeam);
      console.log('[DemoData] Created team:', newTeam.id);
      this.emit('dataChanged', { type: 'team', action: 'create', data: newTeam });
      return newTeam;
    }

    // PATCH /teams/{id} — update team
    if (method === 'PATCH' && /\/teams\/[\w-]+$/.test(p) && !p.includes('/members') && !p.includes('/lead')) {
      const id = p.split('/teams/')[1];
      const idx = this._teams.findIndex(t => t.id === id);
      if (idx >= 0) {
        this._teams[idx] = { ...this._teams[idx], ...body };
        console.log('[DemoData] Updated team:', id);
        return this._teams[idx];
      }
      return { id, ...body };
    }

    // DELETE /teams/{id} — remove team
    if (method === 'DELETE' && /\/teams\/[\w-]+$/.test(p) && !p.includes('/members')) {
      const id = p.split('/teams/')[1];
      this._teams = this._teams.filter(t => t.id !== id);
      console.log('[DemoData] Deleted team:', id);
      return { success: true };
    }

    // POST /teams/{id}/members — add member to team
    if (method === 'POST' && /\/teams\/[\w-]+\/members$/.test(p)) {
      const tid = p.split('/teams/')[1].split('/')[0];
      const team = this._teams.find(t => t.id === tid);
      if (team) {
        if (!team.members) team.members = [];

        // If member_id provided, find existing member and assign
        if (body.member_id) {
          // Find in other teams or unassigned
          let existingMember = null;
          for (const t of this._teams) {
            if (t.members) {
              const idx = t.members.findIndex(m => m.id === body.member_id);
              if (idx >= 0) {
                existingMember = t.members.splice(idx, 1)[0];
                t.member_count = t.members.length;
                break;
              }
            }
          }
          // Also check pending members (just created via POST /members)
          if (!existingMember && this._pendingMembers) {
            const pidx = this._pendingMembers.findIndex(m => m.id === body.member_id);
            if (pidx >= 0) {
              existingMember = this._pendingMembers.splice(pidx, 1)[0];
            }
          }
          if (existingMember) {
            existingMember.team_id = tid;
            existingMember.team_name = team.name;
            existingMember.role_in_team = body.role_in_team || 'member';
            team.members.push(existingMember);
            team.member_count = team.members.length;
            console.log('[DemoData] Assigned member to team:', tid, existingMember.name);
            this.emit('dataChanged', { type: 'team', action: 'update', data: team });
            return existingMember;
          }
        }

        // Create new member and add to team
        const firstName = body.first_name || body.name || 'New';
        const lastName = body.last_name || 'Member';
        const newMember = {
          id: 'm-' + Date.now(),
          first_name: firstName,
          last_name: lastName,
          name: `${firstName} ${lastName}`.trim(),
          role: body.role || 'cleaner',
          role_in_team: body.role_in_team || 'member',
          email: body.email || '',
          phone: body.phone || '',
          is_active: true,
          team_id: tid,
          team_name: team.name,
          photo_url: null,
        };
        team.members.push(newMember);
        team.member_count = team.members.length;
        console.log('[DemoData] Added new member to team:', tid, newMember.name);
        this.emit('dataChanged', { type: 'team', action: 'update', data: team });
        return newMember;
      }
      return { id: 'm-' + Date.now(), ...body };
    }

    // DELETE /teams/{id}/members/{mid} — remove member from team
    if (method === 'DELETE' && /\/teams\/[\w-]+\/members\/[\w-]+$/.test(p)) {
      const parts = p.split('/teams/')[1].split('/members/');
      const tid = parts[0];
      const mid = parts[1];
      const team = this._teams.find(t => t.id === tid);
      if (team && team.members) {
        team.members = team.members.filter(m => m.id !== mid);
        team.member_count = team.members.length;
        console.log('[DemoData] Removed member', mid, 'from team:', tid);
      }
      return { success: true };
    }

    // POST /teams/{id}/lead/{mid} — set team lead
    if (method === 'POST' && /\/teams\/[\w-]+\/lead\/[\w-]+$/.test(p)) {
      const parts = p.split('/teams/')[1].split('/lead/');
      const tid = parts[0];
      const mid = parts[1];
      const team = this._teams.find(t => t.id === tid);
      if (team && team.members) {
        team.members.forEach(m => { m.role = m.id === mid ? 'team_lead' : 'cleaner'; });
        console.log('[DemoData] Set team lead:', mid, 'for team:', tid);
      }
      return { success: true };
    }

    // POST /team/invite — invite member
    if (method === 'POST' && p.includes('/team/invite')) {
      const newMember = {
        id: 'm-' + Date.now(),
        name: body.name || body.email || 'Invited Member',
        email: body.email || '',
        phone: body.phone || '',
        role: body.role || 'cleaner',
        is_active: false,
        status: 'pending',
        ...body,
      };
      // Add to first active team if team_id provided
      if (body.team_id) {
        const team = this._teams.find(t => t.id === body.team_id);
        if (team) {
          if (!team.members) team.members = [];
          team.members.push(newMember);
          team.member_count = team.members.length;
        }
      }
      console.log('[DemoData] Invited member:', newMember.email);
      return { success: true, member: newMember };
    }

    // POST /members — create standalone member
    if (method === 'POST' && /\/members\/?$/.test(p)) {
      const id = 'm-' + Date.now();
      const firstName = body.first_name || body.name || 'New';
      const lastName = body.last_name || 'Member';
      const newMember = {
        id,
        first_name: firstName,
        last_name: lastName,
        name: `${firstName} ${lastName}`.trim(),
        email: body.email || '',
        phone: body.phone || '',
        role: body.role || 'cleaner',
        role_in_team: 'member',
        is_active: true,
        team_id: null,
        team_name: null,
        hourly_rate: body.hourly_rate || 0,
        photo_url: null,
      };
      // Store in pending pool so POST /teams/{id}/members can find it
      if (!this._pendingMembers) this._pendingMembers = [];
      this._pendingMembers.push(newMember);
      console.log('[DemoData] Created member:', id, newMember.name);
      this.emit('dataChanged', { type: 'member', action: 'create', data: newMember });
      return newMember;
    }

    // ============================
    // SERVICES
    // ============================

    // POST /services — create service
    if (method === 'POST' && /\/services\/?$/.test(p) && !p.includes('/checklists')) {
      const newSvc = {
        id: 's-' + Date.now(),
        name: body.name || 'New Service',
        slug: (body.name || 'new-service').toLowerCase().replace(/\s+/g, '-'),
        category: body.category || 'residential',
        base_price: body.base_price || 0,
        price_unit: body.price_unit || 'flat',
        estimated_duration_minutes: body.estimated_duration_minutes || 120,
        min_team_size: body.min_team_size || 2,
        is_active: true,
        sort_order: this._services.length + 1,
        ...body,
      };
      newSvc.id = 's-' + Date.now();
      this._services.push(newSvc);
      console.log('[DemoData] Created service:', newSvc.id);
      this.emit('dataChanged', { type: 'service', action: 'create', data: newSvc });
      return newSvc;
    }

    // PATCH /services/{id} — update service
    if (method === 'PATCH' && /\/services\/[\w-]+$/.test(p) && !p.includes('/checklists')) {
      const id = p.split('/services/')[1];
      const idx = this._services.findIndex(s => s.id === id);
      if (idx >= 0) {
        this._services[idx] = { ...this._services[idx], ...body };
        console.log('[DemoData] Updated service:', id);
        return this._services[idx];
      }
      return { id, ...body };
    }

    // DELETE /services/{id} — remove service
    if (method === 'DELETE' && /\/services\/[\w-]+$/.test(p)) {
      const id = p.split('/services/')[1];
      this._services = this._services.filter(s => s.id !== id);
      console.log('[DemoData] Deleted service:', id);
      return { success: true };
    }

    // POST /services/{id}/checklists — add checklist to service
    if (method === 'POST' && /\/services\/[\w-]+\/checklists$/.test(p)) {
      console.log('[DemoData] Added checklist to service');
      return { id: 'cl-' + Date.now(), ...body, created_at: new Date().toISOString() };
    }

    // ============================
    // BOOKINGS / SCHEDULE
    // ============================

    // POST /schedule/generate — generate schedule
    if (method === 'POST' && p.includes('/schedule/generate')) {
      console.log('[DemoData] Generated schedule');
      return { success: true, message: 'Schedule generated', bookings_created: 8, conflicts: 0 };
    }

    // POST /bookings — create new booking
    if (method === 'POST' && /\/bookings\/?$/.test(p)) {
      const bookings = this._generateBookings();
      const client = this._clients.find(c => c.id === body.client_id) || {};
      const team = this._teams.find(t => t.id === body.team_id) || {};
      const service = this._services.find(s => s.id === body.service_id) || {};
      const newBooking = {
        id: 'b-' + Date.now(),
        client_id: body.client_id || null,
        client_name: `${client.first_name || ''} ${client.last_name || ''}`.trim() || 'Client',
        team_id: body.team_id || null,
        team_name: team.name || 'Unassigned',
        team_color: team.color || '#F59E0B',
        service: service.name || body.service_id || 'Standard Cleaning',
        scheduled_date: body.scheduled_date || this._todayStr(),
        scheduled_start: (body.scheduled_start || '09:00').substring(0, 5),
        scheduled_end: (body.scheduled_end || '11:00').substring(0, 5),
        status: 'scheduled',
        address: `${client.address || ''}, ${client.city || 'New Orleans'}, ${client.state || 'LA'} ${client.zip || ''}`.replace(/^, /, ''),
        notes: body.notes || '',
        checkin_at: null,
        checkout_at: null,
      };
      bookings.push(newBooking);
      console.log('[DemoData] Created booking:', newBooking.id);
      this.emit('dataChanged', { type: 'booking', action: 'create', data: newBooking });
      return newBooking;
    }

    // PATCH /bookings/{id} — update booking
    if (method === 'PATCH' && /\/bookings\/[\w-]+$/.test(p)) {
      const id = p.split('/bookings/')[1];
      const bookings = this._generateBookings();
      const idx = bookings.findIndex(b => b.id === id);
      if (idx >= 0) {
        this._bookings[idx] = { ...this._bookings[idx], ...body };
        console.log('[DemoData] Updated booking:', id);
        return this._bookings[idx];
      }
      return { id, ...body };
    }

    // ============================
    // MY-JOBS (Team/Cleaner operations)
    // ============================

    // POST /my-jobs/{id}/checkin
    if (method === 'POST' && /\/my-jobs\/[\w-]+\/checkin$/.test(p)) {
      const id = p.split('/my-jobs/')[1].split('/')[0];
      const bookings = this._generateBookings();
      const idx = bookings.findIndex(b => b.id === id);
      if (idx >= 0) {
        this._bookings[idx].status = 'in_progress';
        this._bookings[idx].checkin_at = new Date().toISOString();
        console.log('[DemoData] Checked in job:', id);
        return this._bookings[idx];
      }
      return { id, status: 'in_progress', checkin_at: new Date().toISOString() };
    }

    // POST /my-jobs/{id}/checkout
    if (method === 'POST' && /\/my-jobs\/[\w-]+\/checkout$/.test(p)) {
      const id = p.split('/my-jobs/')[1].split('/')[0];
      const bookings = this._generateBookings();
      const idx = bookings.findIndex(b => b.id === id);
      if (idx >= 0) {
        this._bookings[idx].status = 'completed';
        this._bookings[idx].checkout_at = new Date().toISOString();
        console.log('[DemoData] Checked out job:', id);
        return this._bookings[idx];
      }
      return { id, status: 'completed', checkout_at: new Date().toISOString() };
    }

    // POST /my-jobs/{id}/note
    if (method === 'POST' && /\/my-jobs\/[\w-]+\/note$/.test(p)) {
      const id = p.split('/my-jobs/')[1].split('/')[0];
      console.log('[DemoData] Added note to job:', id);
      return { id: 'log-' + Date.now(), booking_id: id, log_type: 'note', note: body.note || body.photo_url || '', created_at: new Date().toISOString() };
    }

    // POST /my-jobs/{id}/issue
    if (method === 'POST' && /\/my-jobs\/[\w-]+\/issue$/.test(p)) {
      const id = p.split('/my-jobs/')[1].split('/')[0];
      console.log('[DemoData] Reported issue for job:', id);
      return { id: 'log-' + Date.now(), booking_id: id, log_type: 'issue', severity: body.severity || 'medium', description: body.description || '', created_at: new Date().toISOString() };
    }

    // POST /my-jobs/{id}/checklist/{itemId}/complete
    if (method === 'POST' && /\/my-jobs\/[\w-]+\/checklist\/[\w-]+\/complete$/.test(p)) {
      console.log('[DemoData] Completed checklist item');
      return { success: true, completed: true, completed_at: new Date().toISOString() };
    }

    // ============================
    // MEMBER AVAILABILITY
    // ============================

    // PATCH /members/{id}/availability — update member availability
    if (method === 'PATCH' && /\/members\/[\w-]+\/availability$/.test(p)) {
      const id = p.split('/members/')[1].split('/')[0];
      console.log('[DemoData] Updated availability for member:', id);
      return { success: true, member_id: id, availability: body };
    }

    // ============================
    // INVOICES
    // ============================

    // POST /invoices/send-reminders
    if (method === 'POST' && p.includes('/invoices/send-reminders')) {
      const invoices = this._generateInvoices();
      const overdue = invoices.filter(i => i.status === 'overdue' || i.status === 'sent');
      console.log('[DemoData] Sent invoice reminders');
      return { success: true, reminders_sent: overdue.length };
    }

    // POST /invoices/{id}/mark-paid — mark invoice as paid
    if (method === 'POST' && /\/invoices\/[\w-]+\/mark-paid$/.test(p)) {
      const id = p.split('/invoices/')[1].split('/')[0];
      const invoices = this._generateInvoices();
      const idx = invoices.findIndex(i => i.id === id);
      if (idx >= 0) {
        this._invoices[idx].status = 'paid';
        this._invoices[idx].paid_at = new Date().toISOString();
        this._invoices[idx].balance_due = 0;
        this._invoices[idx].payment_method = body.method || 'cash';
        console.log('[DemoData] Marked invoice as paid:', id);
        this.emit('dataChanged', { type: 'invoice', action: 'paid', data: this._invoices[idx] });
        return this._invoices[idx];
      }
      return { id, status: 'paid', paid_at: new Date().toISOString() };
    }

    // PATCH /invoices/{id} — update invoice
    if (method === 'PATCH' && /\/invoices\/[\w-]+$/.test(p)) {
      const id = p.split('/invoices/')[1];
      const invoices = this._generateInvoices();
      const idx = invoices.findIndex(i => i.id === id);
      if (idx >= 0) {
        this._invoices[idx] = { ...this._invoices[idx], ...body };
        if (body.status === 'paid') {
          this._invoices[idx].paid_at = new Date().toISOString();
          this._invoices[idx].balance_due = 0;
        }
        console.log('[DemoData] Updated invoice:', id);
        this.emit('dataChanged', { type: 'invoice', action: 'update', data: this._invoices[idx] });
        return this._invoices[idx];
      }
      return { id, ...body };
    }

    // ============================
    // SETTINGS
    // ============================

    // PUT /settings — update general settings
    if (method === 'PUT' && /\/settings\/?$/.test(p) && !p.includes('/areas') && !p.includes('/pricing')) {
      // Merge into stored settings and persist to localStorage
      const existing = this.getSettings();
      const merged = {
        business_profile: { ...existing.business_profile, ...(body.business_profile || {}) },
        settings: { ...existing.settings, ...(body.settings || {}) },
        ...body,
      };
      // Persist across refresh
      try { localStorage.setItem('cc_demo_settings', JSON.stringify(merged)); } catch (e) { /* ok */ }
      console.log('[DemoData] Saved general settings');
      this.emit('dataChanged', { type: 'settings', action: 'update', data: merged });
      return merged;
    }

    // PUT /settings/areas/{id} — update area
    if (method === 'PUT' && /\/settings\/areas\/[\w-]+$/.test(p)) {
      const id = p.split('/settings/areas/')[1];
      const areas = this.getAreas();
      const idx = areas.findIndex(a => a.id === id);
      if (idx >= 0) {
        areas[idx] = { ...areas[idx], ...body };
      }
      this._demoAreas = areas;
      try { localStorage.setItem('cc_demo_areas', JSON.stringify(areas)); } catch (e) { /* ok */ }
      console.log('[DemoData] Updated area:', id);
      return idx >= 0 ? areas[idx] : { id, ...body };
    }

    // POST /settings/areas — create area
    if (method === 'POST' && /\/settings\/areas\/?$/.test(p)) {
      const areas = this.getAreas();
      const newArea = {
        id: 'a-' + Date.now(),
        name: body.name || 'New Area',
        zip_codes: body.zip_codes || [],
        city: body.city || 'New Orleans',
        state: body.state || 'LA',
        is_active: true,
        ...body,
      };
      newArea.id = 'a-' + Date.now();
      areas.push(newArea);
      this._demoAreas = areas;
      try { localStorage.setItem('cc_demo_areas', JSON.stringify(areas)); } catch (e) { /* ok */ }
      console.log('[DemoData] Created area:', newArea.id);
      return newArea;
    }

    // DELETE /settings/areas/{id} — remove area
    if (method === 'DELETE' && /\/settings\/areas\/[\w-]+$/.test(p)) {
      const id = p.split('/settings/areas/')[1];
      let areas = this.getAreas();
      areas = areas.filter(a => a.id !== id);
      this._demoAreas = areas;
      try { localStorage.setItem('cc_demo_areas', JSON.stringify(areas)); } catch (e) { /* ok */ }
      console.log('[DemoData] Deleted area:', id);
      return { success: true };
    }

    // PUT /settings/pricing/{id} — update pricing rule
    if (method === 'PUT' && /\/settings\/pricing\/[\w-]+$/.test(p)) {
      const id = p.split('/settings/pricing/')[1];
      let rules = this._demoPricingRules || [];
      const idx = rules.findIndex(r => r.id === id);
      if (idx >= 0) {
        rules[idx] = { ...rules[idx], ...body };
      }
      this._demoPricingRules = rules;
      try { localStorage.setItem('cc_demo_pricing', JSON.stringify(rules)); } catch (e) { /* ok */ }
      console.log('[DemoData] Updated pricing rule:', id);
      return idx >= 0 ? rules[idx] : { id, ...body };
    }

    // POST /settings/pricing — create pricing rule
    if (method === 'POST' && /\/settings\/pricing\/?$/.test(p)) {
      const rules = this._demoPricingRules || [];
      const newRule = {
        id: 'pr-' + Date.now(),
        ...body,
      };
      rules.push(newRule);
      this._demoPricingRules = rules;
      try { localStorage.setItem('cc_demo_pricing', JSON.stringify(rules)); } catch (e) { /* ok */ }
      console.log('[DemoData] Created pricing rule:', newRule.id);
      return newRule;
    }

    // DELETE /settings/pricing/{id} — remove pricing rule
    if (method === 'DELETE' && /\/settings\/pricing\/[\w-]+$/.test(p)) {
      const id = p.split('/settings/pricing/')[1];
      this._demoPricingRules = (this._demoPricingRules || []).filter(r => r.id !== id);
      try { localStorage.setItem('cc_demo_pricing', JSON.stringify(this._demoPricingRules)); } catch (e) { /* ok */ }
      console.log('[DemoData] Deleted pricing rule:', id);
      return { success: true };
    }

    // ============================
    // HOMEOWNER OPERATIONS
    // ============================

    // POST /my-bookings/request — request a booking
    if (method === 'POST' && p.includes('/my-bookings/request')) {
      const bookings = this._generateBookings();
      const newBooking = {
        id: 'b-' + Date.now(),
        client_id: 'homeowner',
        client_name: 'John Smith',
        team_id: this._teams[0]?.id || 'team-1',
        team_name: this._teams[0]?.name || 'Team Alpha',
        team_color: this._teams[0]?.color || '#1A73E8',
        service: body.service_id || 'Standard Cleaning',
        scheduled_date: body.date || this._futureDate(3),
        scheduled_start: body.time || '09:00',
        scheduled_end: '11:00',
        status: 'pending',
        address: '1234 Magazine St, New Orleans, LA 70130',
        notes: body.notes || '',
        checkin_at: null,
        checkout_at: null,
      };
      bookings.push(newBooking);
      console.log('[DemoData] Homeowner requested booking:', newBooking.id);
      return newBooking;
    }

    // PATCH /my-bookings/{id}/reschedule
    if (method === 'PATCH' && /\/my-bookings\/[\w-]+\/reschedule$/.test(p)) {
      const id = p.split('/my-bookings/')[1].split('/')[0];
      const bookings = this._generateBookings();
      const idx = bookings.findIndex(b => b.id === id);
      if (idx >= 0) {
        if (body.date) this._bookings[idx].scheduled_date = body.date;
        if (body.time) this._bookings[idx].scheduled_start = body.time;
        console.log('[DemoData] Rescheduled booking:', id);
        return this._bookings[idx];
      }
      return { id, ...body, status: 'rescheduled' };
    }

    // POST /my-bookings/{id}/reschedule (some modules use POST)
    if (method === 'POST' && /\/my-bookings\/[\w-]+\/reschedule$/.test(p)) {
      const id = p.split('/my-bookings/')[1].split('/')[0];
      const bookings = this._generateBookings();
      const idx = bookings.findIndex(b => b.id === id);
      if (idx >= 0) {
        if (body.date) this._bookings[idx].scheduled_date = body.date;
        if (body.time) this._bookings[idx].scheduled_start = body.time;
        console.log('[DemoData] Rescheduled booking (POST):', id);
        return this._bookings[idx];
      }
      return { id, ...body, status: 'rescheduled' };
    }

    // PATCH /my-bookings/{id}/cancel
    if (method === 'PATCH' && /\/my-bookings\/[\w-]+\/cancel$/.test(p)) {
      const id = p.split('/my-bookings/')[1].split('/')[0];
      const bookings = this._generateBookings();
      const idx = bookings.findIndex(b => b.id === id);
      if (idx >= 0) {
        this._bookings[idx].status = 'cancelled';
        console.log('[DemoData] Cancelled booking:', id);
        return this._bookings[idx];
      }
      return { id, status: 'cancelled' };
    }

    // POST /my-bookings/{id}/cancel (some modules use POST)
    if (method === 'POST' && /\/my-bookings\/[\w-]+\/cancel$/.test(p)) {
      const id = p.split('/my-bookings/')[1].split('/')[0];
      const bookings = this._generateBookings();
      const idx = bookings.findIndex(b => b.id === id);
      if (idx >= 0) {
        this._bookings[idx].status = 'cancelled';
        console.log('[DemoData] Cancelled booking (POST):', id);
        return this._bookings[idx];
      }
      return { id, status: 'cancelled' };
    }

    // POST /my-bookings/{id}/review — submit review
    if (method === 'POST' && /\/my-bookings\/[\w-]+\/review$/.test(p)) {
      console.log('[DemoData] Submitted review');
      return { success: true, rating: body.rating || 5, comment: body.comment || '' };
    }

    // ============================
    // AUTH / PROFILE
    // ============================

    // PATCH /me — update user profile
    if (method === 'PATCH' && p.endsWith('/me')) {
      try {
        const existing = JSON.parse(localStorage.getItem('cc_demo_user') || '{}');
        const updated = { ...existing, ...body };
        localStorage.setItem('cc_demo_user', JSON.stringify(updated));
      } catch (e) { /* ok */ }
      console.log('[DemoData] Updated user profile');
      return { ...body, updated_at: new Date().toISOString() };
    }

    // PUT /my-preferences — save homeowner preferences
    if (method === 'PUT' && p.includes('/my-preferences')) {
      try { localStorage.setItem('cc_demo_preferences', JSON.stringify(body)); } catch (e) { /* ok */ }
      console.log('[DemoData] Saved preferences');
      return body;
    }

    // ============================
    // ONBOARDING
    // ============================

    // POST /onboarding/step/{n}
    if (method === 'POST' && /\/onboarding\/step\/\d+$/.test(p)) {
      const step = parseInt(p.split('/step/')[1]);
      console.log('[DemoData] Completed onboarding step:', step);
      return { success: true, step, completed: true };
    }

    // POST /onboarding/complete
    if (method === 'POST' && p.includes('/onboarding/complete')) {
      console.log('[DemoData] Completed onboarding');
      return { success: true, completed: true };
    }

    // POST /onboarding/skip
    if (method === 'POST' && p.includes('/onboarding/skip')) {
      console.log('[DemoData] Skipped onboarding');
      return { success: true, skipped: true };
    }

    // ============================
    // BILLING
    // ============================

    // POST /billing/checkout
    if (method === 'POST' && p.includes('/billing/checkout')) {
      console.log('[DemoData] Demo billing checkout');
      return { url: '#', message: 'Demo mode — billing not available' };
    }

    // POST /billing/portal
    if (method === 'POST' && p.includes('/billing/portal')) {
      console.log('[DemoData] Demo billing portal');
      return { url: '#', message: 'Demo mode — billing portal not available' };
    }

    // ============================
    // NOTIFICATIONS
    // ============================

    if (method === 'PUT' && p.includes('/notifications')) {
      console.log('[DemoData] Updated notification settings');
      return body;
    }

    // ============================
    // AUTH — accept invite
    // ============================

    if (method === 'POST' && p.includes('/accept-invite')) {
      console.log('[DemoData] Accepted invite');
      return { success: true };
    }

    // ============================
    // CATCH-ALL for unknown POST/PATCH/PUT/DELETE
    // ============================
    // Return null — let the caller handle it (will return {})
    console.log('[DemoData] No write handler for', method, p);
    return null;
  },

  // ---- Route Matcher ----
  // Returns demo data for a given API path, or null if no match

  match(path) {
    // Normalize path
    const p = path.replace(/\?.*$/, ''); // strip query params
    const qs = path.includes('?') ? Object.fromEntries(new URLSearchParams(path.split('?')[1])) : {};

    if (p.endsWith('/dashboard')) return this.getDashboard();
    if (p.endsWith('/dashboard/teams')) return this.getDashboardTeams();
    if (p.endsWith('/dashboard/revenue')) return this.getDashboardRevenue(qs.period || 'month');
    if (p.endsWith('/teams')) return this.getTeams();
    if (/\/teams\/[\w-]+$/.test(p)) return this.getTeamDetail(p.split('/teams/')[1]);
    if (p.includes('/members')) return this.getMembers();
    if (/\/clients\/[\w-]+\/schedules$/.test(p)) { const cid = p.split('/clients/')[1].split('/')[0]; const client = this._clients.find(c => c.id === cid); return client ? [{ id: 'sched1', frequency: client.frequency || 'weekly', day_of_week: 'monday', preferred_time: '09:00', service_name: 'Standard Cleaning', is_active: true }] : []; }
    if (/\/clients\/[\w-]+$/.test(p)) { const cid = p.split('/clients/')[1]; return this.getClientDetail(cid); }
    if (p.includes('/clients') && !p.includes('/clients/')) return this.getClients(parseInt(qs.page) || 1);
    if (p.endsWith('/services')) return this.getServices();
    if (p.includes('/checklists')) return { items: [] };
    if (/\/bookings\/?$/.test(p)) return { bookings: this._generateBookings() };
    if (p.includes('/invoices')) return this.getInvoices();
    if (p.includes('/payments/dashboard')) return this.getPaymentDashboard();
    if (p.includes('/schedule/summary')) return this.getScheduleSummary();
    if (p.includes('/schedule/calendar')) return this.getCalendarEvents();
    if (p.includes('/my-jobs/today')) return this.getTodayJobs();
    if (/\/my-jobs\/[\w-]+$/.test(p)) { const jobId = p.split('/my-jobs/')[1]; return this.getJobDetail(jobId); }
    if (p.includes('/my-bookings')) return this.getMyBookings();
    if (p.includes('/my-invoices')) return this.getMyInvoices();
    if (p.includes('/my-preferences')) {
      try { const saved = localStorage.getItem('cc_demo_preferences'); if (saved) return JSON.parse(saved); } catch (e) { /* ok */ }
      return this.getPreferences();
    }
    if (p.includes('/settings') && !p.includes('/areas') && !p.includes('/pricing')) return this.getSettings();
    if (p.includes('/settings/areas')) return this.getAreas();
    if (p.includes('/settings/pricing')) {
      if (this._demoPricingRules) return this._demoPricingRules;
      try { const saved = localStorage.getItem('cc_demo_pricing'); if (saved) { this._demoPricingRules = JSON.parse(saved); return this._demoPricingRules; } } catch (e) { /* ok */ }
      return [];
    }
    if (p.includes('/onboarding/status')) return { completed_steps: [], current_step: 1 };
    if (p.includes('/onboarding/templates')) return this.getOnboardingTemplates();
    if (p.includes('/plan')) return { plan: 'maximum', limits: {} };
    if (p.includes('/notifications')) return [];
    if (p.includes('/schedule/stream')) return null; // SSE, skip
    if (p.endsWith('/me')) return { email: CleanClaw._user?.email, name: CleanClaw._user?.name };
    if (p.includes('/earnings')) return this.getEarnings(qs.period || 'month');
    if (p.includes('/schedule/weekly') || p.includes('/schedule/daily')) return this.getWeekSchedule();

    return null; // No match — let original empty response through
  },
};

// Auto-load persisted data on script load
DemoData._loadFromStorage();

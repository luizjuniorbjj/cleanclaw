/**
 * CleanClaw — Super Admin Dashboard
 *
 * Platform-level admin panel for managing ALL businesses.
 * Role: super_admin
 * Route: #/admin/dashboard
 */

window.AdminSuperAdmin = {
  _businesses: [],
  _expandedBiz: null,

  async render(container) {
    this._businesses = DemoData._businesses || [];

    const stats = this._calcStats();

    container.innerHTML = `
      <div class="cc-super-admin">
        <!-- KPI Cards -->
        <div class="cc-sa-kpis">
          <div class="cc-sa-kpi-card">
            <div class="cc-sa-kpi-value">${stats.totalBusinesses}</div>
            <div class="cc-sa-kpi-label">Total Businesses</div>
          </div>
          <div class="cc-sa-kpi-card">
            <div class="cc-sa-kpi-value">${stats.activeUsers}</div>
            <div class="cc-sa-kpi-label">Active Users</div>
          </div>
          <div class="cc-sa-kpi-card">
            <div class="cc-sa-kpi-value">$${stats.mrr}</div>
            <div class="cc-sa-kpi-label">MRR</div>
          </div>
          <div class="cc-sa-kpi-card">
            <div class="cc-sa-kpi-value">${stats.activeCleaners}</div>
            <div class="cc-sa-kpi-label">Active Cleaners</div>
          </div>
        </div>

        <!-- Actions Bar -->
        <div class="cc-sa-actions-bar">
          <h2 class="cc-text-xl" style="margin:0;">Businesses</h2>
          <button class="cc-btn cc-btn-primary" onclick="AdminSuperAdmin._showCreateModal()">
            + Create Business
          </button>
        </div>

        <!-- Businesses Table -->
        <div class="cc-card" style="overflow-x:auto;">
          <table class="cc-sa-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Owner Email</th>
                <th>Plan</th>
                <th>Status</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody id="sa-businesses-tbody">
              ${this._renderRows()}
            </tbody>
          </table>
        </div>
      </div>

      <!-- Create Business Modal -->
      <div class="cc-sa-modal-overlay" id="sa-create-modal" style="display:none;" onclick="AdminSuperAdmin._closeCreateModal(event)">
        <div class="cc-sa-modal" onclick="event.stopPropagation()">
          <div class="cc-sa-modal-header">
            <h3 style="margin:0;">Create Business</h3>
            <button class="cc-sa-modal-close" onclick="AdminSuperAdmin._hideCreateModal()">&times;</button>
          </div>
          <form onsubmit="return AdminSuperAdmin._handleCreateBusiness(event)">
            <div class="cc-form-group">
              <label class="cc-label">Business Name</label>
              <input type="text" class="cc-input" id="sa-biz-name" required placeholder="e.g. Sparkle Miami">
            </div>
            <div class="cc-form-group">
              <label class="cc-label">Owner Email</label>
              <input type="email" class="cc-input" id="sa-biz-email" required placeholder="owner@example.com">
            </div>
            <div class="cc-form-group">
              <label class="cc-label">Owner Password</label>
              <input type="password" class="cc-input" id="sa-biz-password" required placeholder="Min 6 characters" minlength="6">
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--cc-space-3);">
              <div class="cc-form-group">
                <label class="cc-label">Plan</label>
                <select class="cc-input" id="sa-biz-plan">
                  <option value="basic">Basic</option>
                  <option value="pro" selected>Pro</option>
                  <option value="business">Business</option>
                </select>
              </div>
              <div class="cc-form-group">
                <label class="cc-label">Status</label>
                <select class="cc-input" id="sa-biz-status">
                  <option value="trial">Trial</option>
                  <option value="active" selected>Active</option>
                </select>
              </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--cc-space-3);">
              <div class="cc-form-group">
                <label class="cc-label">City</label>
                <input type="text" class="cc-input" id="sa-biz-city" required placeholder="New Orleans">
              </div>
              <div class="cc-form-group">
                <label class="cc-label">State</label>
                <input type="text" class="cc-input" id="sa-biz-state" required placeholder="LA" maxlength="2" style="text-transform:uppercase;">
              </div>
            </div>
            <div style="display:flex;gap:var(--cc-space-3);justify-content:flex-end;margin-top:var(--cc-space-4);">
              <button type="button" class="cc-btn cc-btn-secondary" onclick="AdminSuperAdmin._hideCreateModal()">Cancel</button>
              <button type="submit" class="cc-btn cc-btn-primary">Create Business</button>
            </div>
          </form>
        </div>
      </div>
    `;
  },

  // --- Stats ---

  _calcStats() {
    const biz = this._businesses;
    return {
      totalBusinesses: biz.length,
      activeUsers: biz.reduce((sum, b) => sum + (b.clients || 0) + 1, 0),
      mrr: biz.reduce((sum, b) => sum + (b.mrr || 0), 0),
      activeCleaners: biz.reduce((sum, b) => sum + (b.cleaners || 0), 0),
    };
  },

  // --- Table Rendering ---

  _renderRows() {
    if (!this._businesses.length) {
      return '<tr><td colspan="6" style="text-align:center;padding:var(--cc-space-8);color:var(--cc-neutral-400);">No businesses yet. Create one to get started.</td></tr>';
    }

    return this._businesses.map(b => `
      <tr class="cc-sa-row" data-biz-id="${b.id}">
        <td>
          <button class="cc-sa-expand-btn" onclick="AdminSuperAdmin._toggleExpand('${b.id}')" title="Expand">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="transition:transform 0.2s;${this._expandedBiz === b.id ? 'transform:rotate(90deg);' : ''}"><path d="M9 18l6-6-6-6"/></svg>
          </button>
          <strong>${this._esc(b.name)}</strong>
          <span class="cc-text-xs cc-text-muted" style="display:block;margin-left:22px;">${this._esc(b.city)}, ${this._esc(b.state)}</span>
        </td>
        <td>${this._esc(b.owner_email)}</td>
        <td><span class="cc-sa-plan-badge cc-sa-plan-${b.plan}">${b.plan}</span></td>
        <td><span class="cc-sa-status-badge cc-sa-status-${b.status}">${b.status}</span></td>
        <td>${this._fmtDate(b.created_at)}</td>
        <td>
          <div class="cc-sa-row-actions">
            <button class="cc-btn cc-btn-sm cc-btn-ghost" onclick="AdminSuperAdmin._editBusiness('${b.id}')" title="Edit">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            </button>
            <button class="cc-btn cc-btn-sm cc-btn-ghost" onclick="AdminSuperAdmin._toggleSuspend('${b.id}')" title="${b.status === 'suspended' ? 'Activate' : 'Suspend'}">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="${b.status === 'suspended' ? 'var(--cc-success-500)' : 'var(--cc-warning-500)'}" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>
            </button>
            <button class="cc-btn cc-btn-sm cc-btn-ghost" onclick="AdminSuperAdmin._deleteBusiness('${b.id}')" title="Delete">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--cc-danger-500)" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
            </button>
          </div>
        </td>
      </tr>
      ${this._expandedBiz === b.id ? this._renderExpandedRow(b) : ''}
    `).join('');
  },

  _renderExpandedRow(b) {
    const bookingsMonth = Math.floor(Math.random() * 40) + 10;
    const revenue = (b.mrr || 0) + Math.floor(Math.random() * 500);
    return `
      <tr class="cc-sa-expanded-row">
        <td colspan="6">
          <div class="cc-sa-expanded-grid">
            <div class="cc-sa-expanded-stat">
              <span class="cc-sa-expanded-stat-value">${b.teams || 0}</span>
              <span class="cc-sa-expanded-stat-label">Teams</span>
            </div>
            <div class="cc-sa-expanded-stat">
              <span class="cc-sa-expanded-stat-value">${b.clients || 0}</span>
              <span class="cc-sa-expanded-stat-label">Clients</span>
            </div>
            <div class="cc-sa-expanded-stat">
              <span class="cc-sa-expanded-stat-value">${bookingsMonth}</span>
              <span class="cc-sa-expanded-stat-label">Bookings (month)</span>
            </div>
            <div class="cc-sa-expanded-stat">
              <span class="cc-sa-expanded-stat-value">$${revenue}</span>
              <span class="cc-sa-expanded-stat-label">Revenue (month)</span>
            </div>
          </div>
        </td>
      </tr>
    `;
  },

  // --- Actions ---

  _toggleExpand(bizId) {
    this._expandedBiz = this._expandedBiz === bizId ? null : bizId;
    const tbody = document.getElementById('sa-businesses-tbody');
    if (tbody) tbody.innerHTML = this._renderRows();
  },

  _showCreateModal() {
    document.getElementById('sa-create-modal').style.display = 'flex';
  },

  _hideCreateModal() {
    document.getElementById('sa-create-modal').style.display = 'none';
  },

  _closeCreateModal(event) {
    if (event.target.id === 'sa-create-modal') this._hideCreateModal();
  },

  _handleCreateBusiness(event) {
    event.preventDefault();
    const name = document.getElementById('sa-biz-name').value.trim();
    const email = document.getElementById('sa-biz-email').value.trim();
    const plan = document.getElementById('sa-biz-plan').value;
    const status = document.getElementById('sa-biz-status').value;
    const city = document.getElementById('sa-biz-city').value.trim();
    const state = document.getElementById('sa-biz-state').value.trim().toUpperCase();

    const newBiz = {
      id: 'biz-' + Date.now(),
      name,
      owner_email: email,
      plan,
      status,
      city,
      state,
      created_at: new Date().toISOString().split('T')[0],
      teams: 0,
      clients: 0,
      cleaners: 0,
      mrr: status === 'trial' ? 0 : (plan === 'basic' ? 29 : plan === 'pro' ? 49 : 99),
    };

    this._businesses.push(newBiz);
    DemoData._businesses = this._businesses;

    this._hideCreateModal();
    // Re-render
    const contentView = document.getElementById('content-view');
    if (contentView) this.render(contentView);

    if (typeof CleanClaw !== 'undefined' && CleanClaw.toast) {
      CleanClaw.toast(`Business "${name}" created`, 'success');
    }
    return false;
  },

  _editBusiness(bizId) {
    if (typeof CleanClaw !== 'undefined' && CleanClaw.toast) {
      CleanClaw.toast('Edit business — coming soon', 'info');
    }
  },

  _toggleSuspend(bizId) {
    const biz = this._businesses.find(b => b.id === bizId);
    if (!biz) return;

    if (biz.status === 'suspended') {
      biz.status = 'active';
    } else {
      biz.status = 'suspended';
    }
    DemoData._businesses = this._businesses;

    const tbody = document.getElementById('sa-businesses-tbody');
    if (tbody) tbody.innerHTML = this._renderRows();

    if (typeof CleanClaw !== 'undefined' && CleanClaw.toast) {
      CleanClaw.toast(`${biz.name} ${biz.status === 'suspended' ? 'suspended' : 'activated'}`, biz.status === 'suspended' ? 'warning' : 'success');
    }
  },

  _deleteBusiness(bizId) {
    const biz = this._businesses.find(b => b.id === bizId);
    if (!biz) return;

    if (!confirm(`Delete "${biz.name}"? This cannot be undone.`)) return;

    this._businesses = this._businesses.filter(b => b.id !== bizId);
    DemoData._businesses = this._businesses;

    if (this._expandedBiz === bizId) this._expandedBiz = null;

    // Re-render
    const contentView = document.getElementById('content-view');
    if (contentView) this.render(contentView);

    if (typeof CleanClaw !== 'undefined' && CleanClaw.toast) {
      CleanClaw.toast(`${biz.name} deleted`, 'success');
    }
  },

  // --- Helpers ---

  _esc(str) {
    if (!str) return '';
    const el = document.createElement('span');
    el.textContent = str;
    return el.innerHTML;
  },

  _fmtDate(dateStr) {
    if (!dateStr) return '-';
    try {
      return new Date(dateStr + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch { return dateStr; }
  },
};

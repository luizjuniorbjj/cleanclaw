/**
 * CleanClaw Router
 *
 * Hash-based SPA router with role guards, lazy loading, page transitions, and 404 handling.
 */

window.CleanRouter = {
  // Route definitions: hash -> { module, roles, plan, title }
  _routes: {
    // Public routes
    '#/login':                    { module: null, roles: ['*'], title: 'Sign In' },
    '#/register':                 { module: null, roles: ['*'], title: 'Register' },
    '#/register/invite':          { module: null, roles: ['*'], title: 'Accept Invitation' },

    // Owner routes
    '#/owner/dashboard':          { module: 'owner/dashboard.js', roles: ['owner'], title: 'Dashboard' },
    '#/owner/schedule':           { module: 'owner/schedule-builder.js', roles: ['owner'], title: 'Schedule' },
    '#/owner/calendar':           { module: 'owner/schedule-builder.js', roles: ['owner'], title: 'Calendar' },
    '#/owner/bookings':           { module: 'owner/bookings.js', roles: ['owner'], title: 'All Bookings' },
    '#/owner/teams':              { module: 'owner/team-manager.js', roles: ['owner'], title: 'Teams' },
    '#/owner/clients':            { module: 'owner/client-manager.js', roles: ['owner'], title: 'Clients' },
    '#/owner/clients/:id':        { module: 'owner/client-detail.js', roles: ['owner'], title: 'Client Detail' },
    '#/owner/crm':                { module: 'owner/crm.js', roles: ['owner'], plan: 'maximum', title: 'CRM' },
    '#/owner/invoices':           { module: 'owner/invoice-manager.js', roles: ['owner'], title: 'Invoices' },
    '#/owner/chat-monitor':       { module: 'owner/chat-monitor.js', roles: ['owner'], plan: 'intermediate', title: 'AI Chat' },
    '#/owner/onboarding':         { module: 'owner/onboarding.js', roles: ['owner'], title: 'Setup Wizard' },
    '#/owner/services':           { module: 'owner/services.js', roles: ['owner'], title: 'Services' },
    '#/owner/reports':             { module: 'owner/reports.js', roles: ['owner'], title: 'Reports' },
    '#/owner/settings':           { module: 'owner/settings.js', roles: ['owner'], title: 'Settings' },

    // Homeowner routes
    '#/homeowner/bookings':       { module: 'homeowner/my-bookings.js', roles: ['homeowner'], title: 'My Bookings' },
    '#/homeowner/bookings/:id':   { module: 'homeowner/booking-detail.js', roles: ['homeowner'], title: 'Booking Detail' },
    '#/homeowner/invoices':       { module: 'homeowner/my-invoices.js', roles: ['homeowner'], title: 'My Invoices' },
    '#/homeowner/preferences':    { module: 'homeowner/preferences.js', roles: ['homeowner'], title: 'My Preferences' },

    // Super Admin routes
    '#/admin/dashboard':          { module: 'admin/super-admin.js', roles: ['super_admin'], title: 'Admin Dashboard' },

    // Team routes
    '#/team/today':               { module: 'team/today.js', roles: ['team_lead', 'cleaner'], title: 'Today' },
    '#/team/job/:id':             { module: 'team/job-detail.js', roles: ['team_lead', 'cleaner'], title: 'Job Detail' },
    '#/team/schedule':            { module: 'team/my-schedule.js', roles: ['team_lead', 'cleaner'], title: 'Schedule' },
    '#/team/earnings':            { module: 'team/earnings.js', roles: ['team_lead', 'cleaner'], title: 'Earnings' },
    '#/team/route':               { module: 'team/today.js', roles: ['team_lead', 'cleaner'], title: 'Route' },
    '#/team/profile':             { module: 'team/profile.js', roles: ['team_lead', 'cleaner'], title: 'Profile' },
  },

  // Default home routes per role
  _defaults: {
    super_admin: '#/admin/dashboard',
    owner:      '#/owner/dashboard',
    homeowner:  '#/homeowner/bookings',
    team_lead:  '#/team/today',
    cleaner:    '#/team/today',
  },

  // Current state
  _currentHash: null,
  _currentModule: null,
  _loadedModules: {},
  _userRole: null,
  _userPlan: null,
  _transitioning: false,

  // Transition timing (matches design-system cc-duration-normal: 250ms)
  _transitionDuration: 250,

  /**
   * Initialize router
   */
  init(role, plan) {
    this._userRole = role;
    this._userPlan = plan || 'basic';

    window.addEventListener('hashchange', () => this._onHashChange());
    // Handle initial route
    this._onHashChange();
  },

  /**
   * Navigate to a route
   */
  navigate(hash) {
    window.location.hash = hash;
  },

  /**
   * Get default route for current role
   */
  getDefaultRoute() {
    return this._defaults[this._userRole] || '#/login';
  },

  /**
   * Match a hash against route patterns (supports :id params)
   */
  _matchRoute(hash) {
    // Exact match first
    if (this._routes[hash]) {
      return { route: this._routes[hash], params: {} };
    }

    // Pattern matching for :id params
    const hashParts = hash.split('/');
    for (const [pattern, route] of Object.entries(this._routes)) {
      const patternParts = pattern.split('/');
      if (patternParts.length !== hashParts.length) continue;

      const params = {};
      let match = true;
      for (let i = 0; i < patternParts.length; i++) {
        if (patternParts[i].startsWith(':')) {
          params[patternParts[i].substring(1)] = hashParts[i];
        } else if (patternParts[i] !== hashParts[i]) {
          match = false;
          break;
        }
      }

      if (match) return { route, params };
    }

    return null;
  },

  /**
   * Handle hash change with page transitions
   */
  async _onHashChange() {
    const hash = window.location.hash || '#/login';

    // Don't re-render same route
    if (hash === this._currentHash) return;

    // Prevent concurrent transitions
    if (this._transitioning) return;

    // Handle invite token in URL (e.g., #/register/invite/abc123)
    let effectiveHash = hash;
    let inviteToken = null;
    if (hash.startsWith('#/register/invite/')) {
      inviteToken = hash.split('#/register/invite/')[1];
      effectiveHash = '#/register/invite';
    }

    const matched = this._matchRoute(effectiveHash);

    // 404 - route not found
    if (!matched) {
      this._render404();
      return;
    }

    const { route, params } = matched;

    // Auth routes (login/register) - no role guard
    if (route.roles.includes('*')) {
      // If user is already authenticated (role set), skip login screen and go to default
      if (this._userRole) {
        this._currentHash = null;
        this.navigate(this.getDefaultRoute());
        return;
      }
      this._currentHash = hash;
      this._renderAuthRoute(effectiveHash, inviteToken);
      return;
    }

    // Role guard
    if (!route.roles.includes(this._userRole)) {
      console.warn(`[Router] Role guard: ${this._userRole} cannot access ${hash}`);
      this.navigate(this.getDefaultRoute());
      return;
    }

    // Plan guard
    if (route.plan) {
      const planRank = { basic: 0, intermediate: 1, maximum: 2 };
      if ((planRank[this._userPlan] || 0) < (planRank[route.plan] || 0)) {
        this._renderPlanGate(route.plan, route.title);
        this._currentHash = hash;
        return;
      }
    }

    // Perform page transition: exit current -> load new -> enter new
    const previousHash = this._currentHash;
    this._currentHash = hash;

    await this._transitionAndRender(route, params, previousHash);
  },

  /**
   * Perform exit transition, load new content, perform enter transition
   */
  async _transitionAndRender(route, params, previousHash) {
    const contentView = document.getElementById('content-view');

    // Exit transition (only if there was previous content)
    if (previousHash && contentView && contentView.innerHTML.trim()) {
      this._transitioning = true;
      contentView.classList.add('cc-page-exit');

      await this._wait(this._transitionDuration);

      contentView.classList.remove('cc-page-exit');
      this._transitioning = false;
    }

    // Scroll to top
    const contentArea = document.getElementById('content-area');
    if (contentArea) {
      contentArea.scrollTo({ top: 0, behavior: 'instant' });
    }

    // Load and render the new view
    await this._loadAndRender(route, params);

    // Enter transition
    if (contentView) {
      contentView.classList.add('cc-page-enter');

      // Clean up enter class after animation completes
      const cleanup = () => {
        contentView.classList.remove('cc-page-enter');
        contentView.removeEventListener('animationend', cleanup);
      };
      contentView.addEventListener('animationend', cleanup);
    }
  },

  /**
   * Promise-based wait utility
   */
  _wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  },

  /**
   * Render auth routes (login/register)
   */
  _renderAuthRoute(hash, inviteToken) {
    const container = document.getElementById('auth-container');
    const mainLayout = document.getElementById('main-layout');
    const loadingScreen = document.getElementById('loading-screen');

    loadingScreen.style.display = 'none';
    mainLayout.style.display = 'none';
    container.style.display = 'flex';

    if (hash === '#/register' || hash === '#/register/invite') {
      AuthUI.renderRegister(container, inviteToken);
    } else {
      AuthUI.renderLogin(container);
    }
  },

  /**
   * Load module JS and render with skeleton loading state
   */
  async _loadAndRender(route, params) {
    const contentView = document.getElementById('content-view');
    const contentLoading = document.getElementById('content-loading');

    if (!route.module) return;

    // Show skeleton loading state instead of spinner
    if (typeof CleanClaw !== 'undefined' && CleanClaw.showContentSkeleton) {
      CleanClaw.showContentSkeleton();
    } else {
      contentLoading.style.display = 'flex';
      contentView.innerHTML = '';
    }

    // Update nav active state
    this._updateNavActive();

    // Update page title
    document.title = `${route.title} - CleanClaw`;

    try {
      // Lazy load module if not already loaded
      if (!this._loadedModules[route.module]) {
        await this._loadScript(`/cleaning/static/js/${route.module}?v=8`);
        this._loadedModules[route.module] = true;
      }

      // Find render function: moduleName.render(container, params)
      // Module name convention: owner/dashboard.js -> OwnerDashboard
      const moduleName = this._getModuleName(route.module);
      if (window[moduleName] && typeof window[moduleName].render === 'function') {
        contentView.innerHTML = '';
        await window[moduleName].render(contentView, params);
      } else {
        // Module loaded but no render function - show placeholder
        contentView.innerHTML = `
          <div class="cc-placeholder">
            <h2>${route.title}</h2>
            <p>This module is coming soon.</p>
          </div>
        `;
      }
    } catch (err) {
      console.error(`[Router] Failed to load module: ${route.module}`, err);
      contentView.innerHTML = `
        <div class="cc-placeholder cc-placeholder-error">
          <h2>Failed to load ${route.title}</h2>
          <p>Please try refreshing the page.</p>
          <button class="cc-btn cc-btn-primary" onclick="location.reload()">Refresh</button>
        </div>
      `;
    } finally {
      contentLoading.style.display = 'none';
    }
  },

  /**
   * Load a script dynamically
   */
  _loadScript(src) {
    return new Promise((resolve, reject) => {
      // Check if already loaded
      if (document.querySelector(`script[src="${src}"]`)) {
        resolve();
        return;
      }
      const script = document.createElement('script');
      script.src = src;
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
  },

  /**
   * Convert module path to global variable name
   * e.g., "owner/dashboard.js" -> "OwnerDashboard"
   */
  _getModuleName(path) {
    return path
      .replace('.js', '')
      .split('/')
      .map(part => part.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(''))
      .join('');
  },

  /**
   * Update active nav item
   */
  _updateNavActive() {
    // Sidebar nav
    document.querySelectorAll('.cc-nav-item').forEach(item => {
      item.classList.toggle('active', item.dataset.route === this._currentHash);
    });
    // Bottom tabs
    document.querySelectorAll('.cc-tab-item').forEach(item => {
      item.classList.toggle('active', item.dataset.route === this._currentHash);
    });
    // Top nav links
    document.querySelectorAll('.cc-top-nav-link').forEach(item => {
      item.classList.toggle('active', item.dataset.route === this._currentHash);
    });
  },

  /**
   * Render plan gate (upgrade prompt)
   */
  _renderPlanGate(requiredPlan, featureName) {
    const contentView = document.getElementById('content-view');
    const contentLoading = document.getElementById('content-loading');
    contentLoading.style.display = 'none';

    const planNames = { intermediate: 'Intermediate', maximum: 'Maximum' };
    contentView.innerHTML = `
      <div class="cc-plan-gate cc-animate-fade-in">
        <div class="cc-plan-gate-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--cc-neutral-400)" stroke-width="2">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
          </svg>
        </div>
        <h2>${featureName}</h2>
        <p>Available on the <strong>${planNames[requiredPlan] || requiredPlan}</strong> plan.</p>
        <button class="cc-btn cc-btn-primary" onclick="CleanRouter.navigate('#/owner/settings')">Upgrade Now</button>
      </div>
    `;
  },

  /**
   * Render 404 page
   */
  _render404() {
    const contentView = document.getElementById('content-view');
    const contentLoading = document.getElementById('content-loading');
    if (contentLoading) contentLoading.style.display = 'none';
    if (contentView) {
      contentView.innerHTML = `
        <div class="cc-placeholder cc-animate-fade-in">
          <h2>Page Not Found</h2>
          <p>The page you're looking for doesn't exist.</p>
          <button class="cc-btn cc-btn-primary" onclick="CleanRouter.navigate(CleanRouter.getDefaultRoute())">Go Home</button>
        </div>
      `;
    }
  },
};

(() => {
  // ../ethiotel_pos/ethiotel_pos/ethio_telecom_pos_app/page/ethiotel_pos/js/etv2_template.js
  erpnext.POSV2 = erpnext.POSV2 || {};
  erpnext.POSV2.SHELL_TEMPLATE = `
<div class="etv2-shell">

	<!-- ===================== TOP BAR ===================== -->
	<header class="etv2-topbar">
		<div class="etv2-topbar-left">
			<button class="etv2-icon-btn etv2-sidebar-toggle" title="Toggle menu">
				<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
			</button>
			<div class="etv2-brand">
				<img src="/assets/ethiotel_pos/images/tele.jpg" alt="logo" />
				<span class="etv2-brand-name">Ethiotel POS</span>
			</div>
			<div class="etv2-shift-chip etv2-shift-chip-hidden">
				<span class="etv2-shift-dot"></span>
				<span class="etv2-shift-chip-text">Shift open</span>
			</div>
		</div>
		<div class="etv2-topbar-right">
	<div class="fk-menu-wrap fk-actions-menu-wrap">
		<button class="etv2-icon-btn fk-actions-trigger" title="${__("Actions")}">
			<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="5" r="1"></circle><circle cx="12" cy="12" r="1"></circle><circle cx="12" cy="19" r="1"></circle></svg>
		</button>
		<div class="fk-dropdown-menu fk-actions-menu">
			<div class="fk-menu-item" data-action="return_invoice">
				<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"></polyline><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path></svg>
				<span>${__("Return Invoice")}</span>
			</div>
			<div class="fk-menu-item" data-action="resync">
				<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
				<span>${__("Resync")}</span>
			</div>
			<div class="fk-menu-item" data-action="print_last_invoice">
				<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9V2h12v7"></path><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path><rect x="6" y="14" width="12" height="8"></rect></svg>
				<span>${__("Print Last Invoice")}</span>
			</div>
			<div class="fk-menu-item" data-action="send_to_mor">
				<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
				<span>${__("MoR Tasks")}</span>
				<span class="fk-menu-badge">${__("!!")}</span>
			</div>
		</div>
	</div>

	<button class="etv2-icon-btn etv2-home-btn" title="${__("Exit POS")}">
		<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
	</button>

	<div class="etv2-network etv2-online">
		<span class="etv2-network-dot"></span><span class="etv2-network-label">${__("Online")}</span>
	</div>

	<div class="fk-menu-wrap fk-profile-menu-wrap">
		<button class="fk-profile-btn fk-profile-trigger">
			<span class="etv2-avatar"></span>
			<span class="fk-profile-name">${frappe.utils.escape_html(frappe.session.user_fullname || frappe.session.user)}</span>
			<svg class="fk-caret" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
		</button>
		<div class="fk-dropdown-menu fk-profile-menu">
			<div class="fk-menu-header">
				<div class="fk-menu-header-name">${frappe.utils.escape_html(frappe.session.user_fullname || frappe.session.user)}</div>
				<div class="fk-menu-header-shift">${__("Shift")}: <span class="fk-shift-time">${__("Not opened")}</span></div>
			</div>
			<div class="fk-menu-divider"></div>
			<div class="fk-menu-item" data-profile-action="my_profile"><span>${__("My Profile")}</span></div>
			<div class="fk-menu-item" data-profile-action="apps"><span>${__("Apps")}</span></div>
			<div class="fk-menu-item" data-profile-action="fullscreen"><span>${__("Toggle Full Screen")}</span></div>
			<div class="fk-menu-divider"></div>
			<div class="fk-menu-item fk-menu-item-danger" data-profile-action="sign_out"><span>${__("Sign Out")}</span></div>
		</div>
	</div>

	<button class="etv2-icon-btn etv2-settings-btn" data-ws="settings" title="${__("Settings")}">
		<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
	</button>
</div>
	</header>

	<!-- ===================== SIDEBAR (direct grid child) ===================== -->
	<aside class="etv2-sidebar">
		<nav class="etv2-sidebar-nav">
				<button class="etv2-nav-item etv2-nav-sale" data-ws="sale">
					<span class="etv2-nav-icon">
						<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path><line x1="3" y1="6" x2="21" y2="6"></line><path d="M16 10a4 4 0 0 1-8 0"></path></svg>
					</span>
					<span class="etv2-nav-label">Sale</span>
				</button>
				
				<button class="etv2-nav-item etv2-nav-held" data-ws="held">
					<span class="etv2-nav-icon">
						<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"></path><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>
					</span>
					<span class="etv2-nav-label">Held Orders</span>
				</button>
				<button class="etv2-nav-item etv2-nav-dashboard" data-ws="dashboard">
					<span class="etv2-nav-icon">
						<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9" rx="1"></rect><rect x="14" y="3" width="7" height="5" rx="1"></rect><rect x="14" y="12" width="7" height="9" rx="1"></rect><rect x="3" y="16" width="7" height="5" rx="1"></rect></svg>
					</span>
					<span class="etv2-nav-label">Shift Dashboard</span>
				</button>
				<button class="etv2-nav-item etv2-nav-customers" data-ws="customers">
					<span class="etv2-nav-icon">
						<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
					</span>
					<span class="etv2-nav-label">Customers</span>
				</button>
				<button class="etv2-nav-item etv2-nav-returns" data-ws="returns">
					<span class="etv2-nav-icon">
						<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"></polyline><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path></svg>
					</span>
					<span class="etv2-nav-label">Returns</span>
				</button>
				<button class="etv2-nav-item etv2-nav-reports" data-ws="reports">
					<span class="etv2-nav-icon">
						<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 20V10"></path><path d="M12 20V4"></path><path d="M6 20v-6"></path></svg>
					</span>
					<span class="etv2-nav-label">Reports</span>
				</button>
				<button class="etv2-nav-item etv2-nav-mor" data-ws="mor">
					<span class="etv2-nav-icon">
						<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<path d="M4 4h16v12H5.17L4 19.17V4z"></path><polyline points="8 8 16 8 16 10 8 10 8 8">
						</polyline><line x1="8" y1="13" x2="16" y2="13"></line></svg>
					</span>
					<span class="etv2-nav-label">MoR Invoices</span>
				</button>
				<button class="etv2-nav-item etv2-nav-settings" data-ws="settings">
					<span class="etv2-nav-icon">
						<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
					</span>
					<span class="etv2-nav-label">Settings</span>
				</button>
			</nav>
		</aside>
<div class="etv2-drawer-scrim"></div>
		<!-- ===================== WORKSPACE ===================== -->
		<main class="etv2-workspace" id="etv2-workspace">
			<div class="etv2-workspace-empty">
				<div class="etv2-spinner"></div>
				<p>Loading workspace\u2026</p>
			</div>
		</main>

	<!-- ===================== STATUS BAR ===================== -->
	<footer class="etv2-statusbar">
		<div class="etv2-status-left">
			<span class="etv2-status-profile">Profile: \u2014</span>
			<span class="etv2-status-warehouse">Warehouse: \u2014</span>
		</div>
		<div class="etv2-status-right">
			<span class="etv2-status-clock"></span>
		</div>
	</footer>

	<!-- ===================== MOBILE BOTTOM NAV ===================== -->
	<nav class="etv2-bottomnav">
		<button class="etv2-bottomnav-item etv2-nav-sale" data-ws="sale">
			<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path><line x1="3" y1="6" x2="21" y2="6"></line><path d="M16 10a4 4 0 0 1-8 0"></path></svg>
			<span>Sale</span>
		</button>
		<button class="etv2-bottomnav-item etv2-nav-checkin" data-ws="checkin">
			<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line><polyline points="9 16 11 18 15 14"></polyline></svg>
			<span>Check-In</span>
		</button>
		<button class="etv2-bottomnav-item etv2-nav-held" data-ws="held">
			<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"></path><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>
			<span>Held</span>
		</button>
		<button class="etv2-bottomnav-item etv2-nav-dashboard" data-ws="dashboard">
			<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9" rx="1"></rect><rect x="14" y="3" width="7" height="5" rx="1"></rect><rect x="14" y="12" width="7" height="9" rx="1"></rect><rect x="3" y="16" width="7" height="5" rx="1"></rect></svg>
			<span>Dashboard</span>
		</button>
		<button class="etv2-bottomnav-item etv2-nav-customers" data-ws="customers">
			<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
			<span>Customers</span>
		</button>
		<button class="etv2-bottomnav-item etv2-nav-returns" data-ws="returns">
			<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"></polyline><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path></svg>
			<span>Returns</span>
		</button>
		<button class="etv2-bottomnav-item etv2-nav-reports" data-ws="reports">
			<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 20V10"></path><path d="M12 20V4"></path><path d="M6 20v-6"></path></svg>
			<span>Reports</span>
		</button>
		<button class="etv2-bottomnav-item etv2-nav-mor" data-ws="mor">
			<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16v12H5.17L4 19.17V4z"></path><polyline points="8 8 16 8 16 10 8 10 8 8"></polyline><line x1="8" y1="13" x2="16" y2="13"></line></svg>
			<span>MoR</span>
		</button>
		<button class="etv2-bottomnav-item etv2-nav-settings" data-ws="settings">
			<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
			<span>Settings</span>
		</button>
	</nav>
</div>
`;

  // ../ethiotel_pos/ethiotel_pos/ethio_telecom_pos_app/page/ethiotel_pos/js/etv2_offline.js
  erpnext.POSV2 = erpnext.POSV2 || {};
  erpnext.POSV2.Offline = {
    OFFLINE_KEY: "et_offline_queue",
    CATALOG_KEY: "et_catalog_cache",
    CATALOG_TTL: 1e3 * 60 * 60 * 24,
    is_online() {
      return navigator.onLine !== false;
    },
    get_catalog() {
      try {
        return JSON.parse(localStorage.getItem(this.CATALOG_KEY) || "{}");
      } catch (e) {
        return {};
      }
    },
    cache_catalog(page_key, data) {
      if (!data)
        return;
      try {
        const cache = this.get_catalog();
        cache[page_key] = { data, ts: Date.now() };
        const keys = Object.keys(cache);
        if (keys.length > 40) {
          keys.sort((a, b) => (cache[a].ts || 0) - (cache[b].ts || 0));
          keys.slice(0, keys.length - 40).forEach((k) => delete cache[k]);
        }
        localStorage.setItem(this.CATALOG_KEY, JSON.stringify(cache));
      } catch (e) {
      }
    },
    load_cached_catalog(page_key) {
      try {
        const cache = this.get_catalog();
        const entry = cache[page_key];
        if (!entry)
          return null;
        if (Date.now() - (entry.ts || 0) > this.CATALOG_TTL)
          return null;
        return entry.data;
      } catch (e) {
        return null;
      }
    },
    find_cached_item(code) {
      const cache = this.get_catalog();
      for (const key of Object.keys(cache)) {
        const items = cache[key].data && cache[key].data.items;
        if (!items)
          continue;
        const hit = items.find(
          (i) => i.item_code === code || i.barcode && i.barcode === code
        );
        if (hit)
          return hit;
      }
      return null;
    },
    get_queue() {
      try {
        return JSON.parse(localStorage.getItem(this.OFFLINE_KEY) || "[]");
      } catch (e) {
        return [];
      }
    },
    set_queue(queue) {
      try {
        localStorage.setItem(this.OFFLINE_KEY, JSON.stringify(queue));
      } catch (e) {
      }
    },
    queue_order(doc) {
      const queue = this.get_queue();
      queue.push({ doc, ts: Date.now(), ref: `offline-${Date.now()}-${queue.length + 1}` });
      this.set_queue(queue);
    },
    sync_queue() {
      if (!this.is_online())
        return Promise.resolve({ synced: 0 });
      const queue = this.get_queue();
      if (!queue.length)
        return Promise.resolve({ synced: 0 });
      const pv = "ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos";
      const refs = queue.map((q) => q.ref);
      return frappe.call({
        method: `${pv}.save_offline_order`,
        args: { order: queue[queue.length - 1].doc, ref: refs[refs.length - 1] },
        freeze: true,
        freeze_message: __("Syncing offline orders\u2026")
      }).then((r) => {
        if (r.message && r.message.status === "ok") {
          const remaining = queue.slice(0, -1);
          this.set_queue(remaining);
          return { synced: 1, invoice_name: r.message.invoice_name };
        }
        return { synced: 0 };
      }).catch(() => ({ synced: 0 }));
    },
    start_sync_watcher() {
      $(window).on("online.etv2", () => {
        this.sync_queue().then((res) => {
          if (res.synced) {
            frappe.show_alert({
              message: __("Offline order {0} synced.", [res.invoice_name || ""]),
              indicator: "green"
            });
          }
        });
      });
    }
  };
  $(function() {
    erpnext.POSV2.Offline.start_sync_watcher();
  });

  // ../ethiotel_pos/ethiotel_pos/ethio_telecom_pos_app/page/ethiotel_pos/js/etv2_workspace_manager.js
  erpnext.POSV2 = erpnext.POSV2 || {};
  erpnext.POSV2.WorkspaceManager = class {
    constructor({ shell }) {
      this.shell = shell;
      this.registry = {};
      this.instances = {};
      this.current = null;
      this.$container = shell.$workspace;
    }
    register(name, Ctor) {
      this.registry[name] = Ctor;
      return this;
    }
    async show(name, opts = {}) {
      const needs_shift = ["sale", "held", "dashboard", "customers", "returns", "reports", "mor"];
      if (needs_shift.includes(name) && !this.shell.pos_profile) {
        if (this.current !== "checkin") {
          this.shell.sidebar.set_active("checkin");
          return this.show("checkin", opts);
        }
        return;
      }
      if (name === this.current) {
        if (this.instances[name] && this.instances[name].refresh) {
          this.instances[name].refresh(opts);
        }
        return;
      }
      if (this.current && this.instances[this.current]) {
        this.instances[this.current].$el && this.instances[this.current].$el.removeClass("etv2-active");
        this.instances[this.current].hide && this.instances[this.current].hide();
      }
      if (!this.real_mounted) {
        this.$container.find(".etv2-workspace-empty").remove();
        this.real_mounted = true;
      }
      let ws = this.instances[name];
      if (!ws) {
        const Ctor = this.registry[name];
        if (!Ctor) {
          frappe.show_alert({ message: __(`Unknown workspace: ${name}`), indicator: "red" });
          return;
        }
        ws = new Ctor({ shell: this.shell, workspace: this, container: this.$container, name });
        this.instances[name] = ws;
        ws.$el && this.$container.append(ws.$el);
      }
      ws.$el.addClass("etv2-active");
      ws.show && ws.show(opts);
      this.current = name;
      this.shell.sidebar.set_active(name);
      setTimeout(() => $(window).trigger("resize"), 60);
    }
  };

  // ../ethiotel_pos/ethiotel_pos/ethio_telecom_pos_app/page/ethiotel_pos/js/etv2_sidebar.js
  erpnext.POSV2 = erpnext.POSV2 || {};
  erpnext.POSV2.Sidebar = class {
    constructor({ shell }) {
      this.shell = shell;
      this.$sidebar = shell.$sidebar;
      this.$layout = shell.$shell;
      const expanded = localStorage.getItem("ethiotel_pos.sidebar_expanded") === "1";
      this.$layout.toggleClass("etv2-nav-expanded", expanded);
      this.bind();
    }
    bind() {
      this.shell.$shell.on("click", ".etv2-nav-item, .etv2-bottomnav-item", (e) => {
        const name = $(e.currentTarget).attr("data-ws");
        this.shell.workspaces.show(name);
        this.close_drawer();
      });
      this.shell.$shell.on("click", ".etv2-sidebar-toggle", () => {
        const isTablet = window.matchMedia("(max-width: 1023px)").matches;
        if (isTablet) {
          this.$layout.toggleClass("etv2-drawer-open");
          return;
        }
        this.$layout.toggleClass("etv2-nav-expanded");
        localStorage.setItem(
          "ethiotel_pos.sidebar_expanded",
          this.$layout.hasClass("etv2-nav-expanded") ? "1" : "0"
        );
      });
      this.shell.$shell.on("click", ".etv2-drawer-scrim", () => {
        this.close_drawer();
        this.close_all_menus();
      });
      this.shell.$shell.on("click", ".fk-actions-trigger", (e) => {
        e.stopPropagation();
        this.toggle_menu(".fk-actions-menu");
      });
      this.shell.$shell.on("click", ".fk-actions-menu .fk-menu-item", (e) => {
        const action = $(e.currentTarget).attr("data-action");
        this.close_all_menus();
        this.handle_action(action);
      });
      this.shell.$shell.on("click", ".fk-profile-trigger", (e) => {
        e.stopPropagation();
        this.toggle_menu(".fk-profile-menu");
      });
      this.shell.$shell.on("click", ".fk-profile-menu .fk-menu-item", (e) => {
        const action = $(e.currentTarget).attr("data-profile-action");
        this.close_all_menus();
        this.handle_profile_action(action);
      });
      $(document).on("click.etv2-menus", () => this.close_all_menus());
      $(document).on("fullscreenchange", () => this.sync_fullscreen_label());
    }
    close_drawer() {
      this.$layout.removeClass("etv2-drawer-open");
    }
    set_active(name) {
      this.$layout.find(".etv2-nav-item, .etv2-bottomnav-item").removeClass("active");
      this.$layout.find(`.etv2-nav-item[data-ws="${name}"], .etv2-bottomnav-item[data-ws="${name}"]`).addClass("active");
    }
    toggle_menu(selector) {
      const $menu = this.shell.$shell.find(selector);
      const is_open = $menu.hasClass("fk-menu-open");
      this.close_all_menus();
      if (!is_open)
        $menu.addClass("fk-menu-open");
    }
    close_all_menus() {
      this.shell.$shell.find(".fk-dropdown-menu").removeClass("fk-menu-open");
    }
    handle_action(action) {
      switch (action) {
        case "return_invoice":
          this.shell.workspaces.show("returns");
          break;
        case "resync":
          frappe.show_alert({ message: __("Resyncing\u2026"), indicator: "blue" });
          frappe.call({ method: `${this.shell.get_pv()}.resync_pos_data` }).then(() => frappe.show_alert({ message: __("Resync complete."), indicator: "green" })).catch(() => frappe.show_alert({ message: __("Resync failed."), indicator: "red" }));
          break;
        case "print_last_invoice": {
          if (!this.shell.last_invoice_name) {
            frappe.show_alert({ message: __("No invoice has been created in this session yet."), indicator: "orange" });
            return;
          }
          ethiotel_print("POS Invoice", this.shell.last_invoice_name, "EIMS Invoice");
          break;
        }
        case "send_to_mor":
          this.shell.workspaces.show("mor");
          break;
      }
    }
    handle_profile_action(action) {
      switch (action) {
        case "my_profile":
          frappe.set_route("app", "user-profile", frappe.session.user);
          break;
        case "apps":
          window.open("/apps", "_blank");
          break;
        case "fullscreen":
          this.toggle_fullscreen();
          break;
        case "sign_out":
          frappe.app.logout();
          break;
      }
    }
    toggle_fullscreen() {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(() => {
        });
      } else {
        document.exitFullscreen().catch(() => {
        });
      }
    }
    sync_fullscreen_label() {
      const is_full = Boolean(document.fullscreenElement);
      this.shell.$shell.find('[data-profile-action="fullscreen"] span').text(is_full ? __("Exit Full Screen") : __("Toggle Full Screen"));
    }
    set_shift_time(text) {
      this.$sidebar.closest(".etv2-shell").find(".fk-shift-time").text(text || __("Not opened"));
    }
  };

  // ../ethiotel_pos/ethiotel_pos/ethio_telecom_pos_app/page/ethiotel_pos/js/etv2_shell.js
  erpnext.POSV2 = erpnext.POSV2 || {};
  erpnext.POSV2.Shell = class {
    constructor(wrapper) {
      this.wrapper = wrapper;
      this.page = wrapper.page;
      this.$main = $(wrapper).find(".layout-main-section");
      this.pos_profile = null;
      this.settings = {};
      this.price_list = null;
      this.warehouse = null;
      this.parent_item_group = null;
      this.customer_groups = [];
      this.render();
      this.boot();
    }
    render() {
      this.$main.html(erpnext.POSV2.SHELL_TEMPLATE);
      this.$shell = this.$main.find(".etv2-shell");
      this.$workspace = this.$main.find("#etv2-workspace");
      this.$sidebar = this.$main.find(".etv2-sidebar");
      this.$statusProfile = this.$main.find(".etv2-status-profile");
      this.$statusWarehouse = this.$main.find(".etv2-status-warehouse");
      const initials = (frappe.session.user_fullname || frappe.session.user || "U").slice(0, 1).toUpperCase();
      this.$main.find(".etv2-avatar").text(initials);
      this.$main.find(".fk-profile-name").text(frappe.session.user_fullname || frappe.session.user);
    }
    boot() {
      this.sidebar = new erpnext.POSV2.Sidebar({ shell: this });
      this.workspaces = new erpnext.POSV2.WorkspaceManager({ shell: this });
      this.workspaces.register("sale", erpnext.POSV2.SaleWorkspace);
      this.workspaces.register("checkin", erpnext.POSV2.CheckinWorkspace);
      this.workspaces.register("held", erpnext.POSV2.HeldOrdersWorkspace);
      this.workspaces.register("dashboard", erpnext.POSV2.ShiftDashboardWorkspace);
      this.workspaces.register("customers", erpnext.POSV2.CustomerWorkspace);
      this.workspaces.register("returns", erpnext.POSV2.ReturnsWorkspace);
      this.workspaces.register("reports", erpnext.POSV2.ReportsWorkspace);
      this.workspaces.register("mor", erpnext.POSV2.MoRWorkspace);
      this.workspaces.register("settings", erpnext.POSV2.SettingsWorkspace);
      this.bind_topbar();
      this.start_clock();
      this.watch_network();
      this.check_opening_entry().then(() => {
        if (this.pos_profile) {
          this.workspaces.show("sale");
        }
      });
    }
    bind_topbar() {
      this.$main.find(".etv2-home-btn").on("click", () => {
        window.location.href = "/app";
      });
      this.$main.find(".etv2-settings-btn").on("click", () => {
        this.workspaces.show("settings");
      });
    }
    check_opening_entry() {
      const pv = "ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos";
      return frappe.call({
        method: `${pv}.check_opening_entry`,
        args: { user: frappe.session.user }
      }).then((r) => {
        if (r.message && r.message.length) {
          const entry = r.message[0];
          this.pos_opening = entry.name;
          this.pos_profile = entry.pos_profile;
          this.company = entry.company;
          this.pos_opening_time = entry.period_start_date;
          this.tax_template = entry.taxes_and_charges || null;
          this.show_shift_chip();
          return this.load_profile();
        }
        return this.open_shift_dialog();
      });
    }
    show_shift_chip() {
      const $chip = this.$main.find(".etv2-shift-chip");
      $chip.removeClass("etv2-shift-chip-hidden");
      $chip.find(".etv2-shift-chip-text").text(`${__("Shift open")} \xB7 ${frappe.datetime.str_to_user(this.pos_opening_time)}`);
      if (this.sidebar) {
        this.sidebar.set_shift_time(`${__("Open")} \xB7 ${frappe.datetime.str_to_user(this.pos_opening_time)}`);
      }
    }
    load_profile() {
      const pv = "ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos";
      return frappe.call({
        method: `${pv}.get_pos_profile_data`,
        args: { pos_profile: this.pos_profile }
      }).then((r) => {
        const profile = r.message;
        this.settings = profile;
        this.price_list = profile.selling_price_list;
        this.warehouse = profile.warehouse || profile.set_warehouse;
        this.customer_groups = (profile.customer_groups || []).map((g) => g.name);
        if (!this.tax_template) {
          this.tax_template = profile.taxes_and_charges || null;
        }
        this.set_status_bar();
        return frappe.call({ method: `${pv}.get_root_item_group` }).then((r2) => {
          this.parent_item_group = r2.message && r2.message[0] && r2.message[0].name || "All Item Groups";
        });
      });
    }
    set_status_bar() {
      this.$statusProfile.text(`${__("Profile")}: ${this.pos_profile}`);
      this.$statusWarehouse.text(`${__("Warehouse")}: ${this.warehouse || "\u2014"}`);
    }
    open_shift_dialog() {
      const pv = "ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos";
      const me = this;
      const dialog = new frappe.ui.Dialog({
        title: __("Open Shift"),
        static: true,
        fields: [
          { fieldname: "company", fieldtype: "Link", label: __("Company"), options: "Company", default: frappe.defaults.get_default("company"), reqd: 1 },
          {
            fieldname: "pos_profile",
            fieldtype: "Link",
            label: __("POS Profile"),
            options: "POS Profile",
            reqd: 1,
            get_query: () => ({
              query: "erpnext.accounts.doctype.pos_profile.pos_profile.pos_profile_query",
              filters: { company: dialog.fields_dict.company.get_value() }
            }),
            onchange: () => fetch_payments()
          },
          {
            fieldname: "taxes_and_charges",
            fieldtype: "Link",
            label: __("Tax Template"),
            options: "Sales Taxes and Charges Template",
            description: __("Sales Taxes and Charges Template for this shift's invoices. Defaults to the POS Profile; overrides the EIMS Setting default.")
          },
          {
            fieldname: "balance_details",
            fieldtype: "Table",
            label: __("Opening Balance"),
            cannot_add_rows: false,
            in_place_edit: true,
            reqd: 1,
            data: [],
            fields: [
              { fieldname: "mode_of_payment", fieldtype: "Select", in_list_view: 1, label: __("Mode of Payment"), options: [], reqd: 1 },
              { fieldname: "opening_amount", fieldtype: "Currency", in_list_view: 1, label: __("Opening Amount"), default: 0 }
            ]
          }
        ],
        primary_action_label: __("Open"),
        primary_action: function(values) {
          const balance = (values.balance_details || []).filter((d) => d.mode_of_payment);
          if (!balance.length) {
            frappe.show_alert({ message: __("Add at least one mode of payment."), indicator: "orange" });
            return;
          }
          frappe.call({
            method: "ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos.create_opening_voucher",
            args: { pos_profile: values.pos_profile, company: values.company, balance_details: balance, taxes_and_charges: values.taxes_and_charges },
            freeze: true
          }).then((r) => {
            if (!r.exc) {
              const doc = r.message;
              me.pos_opening = doc.name;
              me.pos_profile = doc.pos_profile;
              me.company = doc.company;
              me.pos_opening_time = doc.period_start_date;
              me.tax_template = values.taxes_and_charges || null;
              dialog.hide();
              me.show_shift_chip();
              me.load_profile().then(() => {
                me.workspaces.show("sale");
              });
            }
          });
        }
      });
      function fetch_payments() {
        const profile = dialog.fields_dict.pos_profile.get_value();
        if (!profile)
          return;
        frappe.call({
          method: "ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos.get_opening_payment_modes",
          args: { pos_profile: profile },
          silent: true
        }).then((r) => {
          const modes = r.message || [];
          const mode_field = dialog.fields_dict.balance_details.df.fields.find((f) => f.fieldname === "mode_of_payment");
          if (mode_field) {
            mode_field.options = modes;
          }
          dialog.fields_dict.balance_details.df.data = modes.map((mode) => ({
            mode_of_payment: mode,
            opening_amount: 0
          }));
          dialog.fields_dict.balance_details.grid.refresh();
          frappe.db.get_doc("POS Profile", profile).then((doc) => {
            if (!dialog.fields_dict.taxes_and_charges.get_value() && doc.taxes_and_charges) {
              dialog.set_value("taxes_and_charges", doc.taxes_and_charges);
            }
          });
        });
      }
      dialog.show();
    }
    close_shift() {
      const me = this;
      if (!this.pos_opening) {
        frappe.show_alert({ message: __("No active shift to close."), indicator: "orange" });
        return;
      }
      frappe.confirm(
        __("Are you sure you want to close this shift? <br><br> The POS Closing Entry will be created and submitted. You won't be able to process sales until a new shift is opened."),
        () => {
          const pv = this.get_pv();
          frappe.call({
            method: `${pv}.close_shift`,
            args: { pos_opening: this.pos_opening },
            freeze: true,
            freeze_message: __("Closing Shift...")
          }).then((r) => {
            if (r.message && r.message.status === "ok") {
              frappe.show_alert({ message: __("Shift successfully closed (Entry: {0})", [r.message.closing_entry]), indicator: "green" });
              this.pos_opening = null;
              this.pos_profile = null;
              this.$main.find(".etv2-shift-chip").addClass("etv2-shift-chip-hidden");
              if (this.sidebar)
                this.sidebar.set_shift_time(null);
              this.check_opening_entry();
            } else {
              frappe.show_alert({ message: __("Failed to close shift: {0}", [r.exc]), indicator: "red" });
            }
          });
        }
      );
    }
    start_clock() {
      const $clock = this.$main.find(".etv2-status-clock");
      const tick = () => $clock.text(moment().format("DD-MM-YYYY hh:mm:ss A").toUpperCase());
      tick();
      setInterval(tick, 1e3);
    }
    watch_network() {
      const $net = this.$main.find(".etv2-network");
      const update = () => {
        const online = navigator.onLine;
        $net.toggleClass("etv2-online", online).toggleClass("etv2-offline", !online);
        $net.find(".etv2-network-label").text(online ? __("Online") : __("Offline"));
      };
      window.addEventListener("online", update);
      window.addEventListener("offline", update);
      update();
    }
    get_pv() {
      return "ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos";
    }
  };

  // ../ethiotel_pos/ethiotel_pos/ethio_telecom_pos_app/page/ethiotel_pos/js/etv2_sale_workspace.js
  erpnext.POSV2 = erpnext.POSV2 || {};
  erpnext.POSV2.SaleWorkspace = class {
    constructor({ shell, workspace, container, name }) {
      this.shell = shell;
      this.workspace = workspace;
      this.container = container;
      this.name = name;
      this.cart = {};
      this.customer = null;
      this.walk_in_customer = null;
      this.payment_mode = null;
      this.items = [];
      this.item_groups = [];
      this.discount_mode = "percentage";
      this.discount_value = 0;
      this.tax_template = this.shell.tax_template || null;
      this.tax_rate = null;
      this.view_mode = "grid";
      this.render();
      this.load_item_groups();
      this.load_products();
      this.load_tax_template();
      this.load_walk_in_customer();
    }
    load_walk_in_customer() {
      const me = this;
      const pv = this.shell.get_pv();
      frappe.call({
        method: `${pv}.get_walk_in_customer`
      }).then((r) => {
        if (r.message && r.message.customer) {
          me.walk_in_customer = r.message.customer;
          if (!me.customer) {
            me.$el.find(".etv2-sale-customer-btn span").html(`${__("Customer")}: <b>${__("Walk-In Customer")}</b>`);
          }
        }
      });
    }
    render() {
      const me = this;
      this.$el = $(`
			<section class="etv2-ws fk-sale">
				<div class="etv2-ws-toolbar fk-sale-toolbar">
					<div class="fk-toolbar-row">
						<div class="fk-search-box etv2-sale-search">
							<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
							<input type="text" placeholder="${__("Search products\u2026")}" />
						
							<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5V3h4v2H3zM9 5h2v14H9zM17 5h4v2h-4zM21 12h-2v5h2zM13 5h2v14h-2zM3 12h2v5H3zM17 17h4v2h-4zM7 17h2v2H7z"></path></svg>
							<input type="text" placeholder="${__("Scan barcode")}" autocomplete="off" />
							<button type="button" class="etv2-barcode-camera-btn" title="${__("Scan with camera")}">
								<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>
							</button>
						
							<button type="button" class="fk-view-btn active" data-view="grid" title="${__("Grid view")}">
								<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
							</button>
							<button type="button" class="fk-view-btn" data-view="list" title="${__("List view")}">
								<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
							</button>
						</div>
					</div>

				</div>
				<div class="fk-sale-body">
					<div class="fk-panel fk-products">
						<div class="fk-panel-body">
						<div class="fk-cats-bar">
		<button type="button" class="fk-cats-nav fk-cats-nav-prev" aria-label="${__("Scroll left")}">
			<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
		</button>
		<div class="fk-cats etv2-cats"></div>
		<button type="button" class="fk-cats-nav fk-cats-nav-next" aria-label="${__("Scroll right")}">
			<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
		</button>
	</div>
							<div class="fk-products-scroll">
								<div class="fk-products-grid etv2-products"></div>
							</div>
						</div>
					</div>
			<div class="fk-panel fk-order">
    <div class="fk-panel-body fk-order-body">
        <div class="fk-order-section fk-cart-section">
            <div class="fk-customer-section">
                <button class="fk-customer-btn etv2-sale-customer-btn" type="button">
                    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                    <span>${__("Customer")}: <b>${__("Choose customer")}</b></span>
                </button>
					<div class="fk-customer-divider"></div>
<button class="fk-customer-btn etv2-sale-payment-btn" type="button">
		<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="4" width="22" height="16" rx="2"></rect><line x1="1" y1="10" x2="23" y2="10"></line></svg>
		<span>${__("Payment")}: <b class="fk-payment-label">${__("Select")}</b></span>
	</button>
	<div class="fk-customer-divider"></div>
	<button class="fk-customer-btn etv2-sale-tax-btn" type="button">
		<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="2" x2="12" y2="22"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
		<span>${__("Tax")}: <b class="fk-tax-label">${__("Select")}</b></span>
	</button>
            </div>
            <div class="fk-cart-head">
                <div class="fk-cart-title-row">
                    <span class="fk-cart-title">${__("Current Sale")}</span>
                    <span class="fk-cart-count">0</span>
                </div>
            </div>
            <div class="fk-cart-list">
                <div class="fk-cart-items"></div>
                <div class="fk-empty">
                    <svg class="fk-empty-icon" viewBox="0 0 24 24" width="40" height="40" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="21" r="1"></circle><circle cx="20" cy="21" r="1"></circle><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path></svg>
                    <p class="fk-empty-title">${__("Cart is empty")}</p>
                    <span>${__("Tap a product to add it.")}</span>
                </div>
            </div>
            <div class="fk-invoice">
                <div class="fk-row-line"><span>${__("Subtotal")}</span><span class="fk-subtotal">0.00</span></div>
                <div class="fk-row-line fk-discount-row"><span>${__("Discount")}</span><span class="fk-discount-value fk-row-discount">- 0.00</span></div>
                <div class="fk-row-line fk-tax-row"><span>${__("Tax")} (<span class="fk-tax-rate-label">0%</span>)</span><span class="fk-tax-value">0.00</span></div>
                <div class="fk-divider"></div>
                <div class="fk-row-line fk-row-total"><span>${__("Total")}</span><span class="fk-grand">0.00</span></div>
            </div>
            <div class="fk-discount">
                <div class="fk-discount-mode-row">
                    <button type="button" class="fk-discount-type-card active" data-mode="percentage">
                        <span class="fk-dt-info"><span class="fk-dt-name">${__("Percentage")}</span></span>
                        <span class="fk-dt-check"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"></path></svg></span>
                    </button>
                    <button type="button" class="fk-discount-type-card" data-mode="value">
                        <span class="fk-dt-info"><span class="fk-dt-name">${__("Amount")}</span></span>
                        <span class="fk-dt-check"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"></path></svg></span>
                    </button>
                </div>
                <div class="fk-discount-input-row">
                    <input type="number" class="fk-discount-input" placeholder="0" min="0" />
                    <span class="fk-discount-value">- 0.00</span>
                </div>
            </div>
            
        </div>
        <div class="fk-order-section fk-checkin-section">
			<button type="button" class="fk-btn-secondary fk-hold-btn">${__("Hold")}</button>
	<button type="button" class="fk-btn-secondary fk-print-receipt-btn">${__("Print Receipt")}</button>

            <button type="button" class="fk-checkin-btn etv2-checkin-btn">
                ${__("Checkin")}<span class="fk-checkin-total fk-grand" id="fk-checkin-total">0.00</span>
            </button>
        </div>
    </div>
</div>
				</div>
			</section>
		`);
      let searchTimer;
      this.$el.find(".etv2-sale-search input").on("input", (e) => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => this.load_products($(e.currentTarget).val()), 250);
      });
      this.$el.find(".etv2-sale-barcode input").on("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          const code = $(e.currentTarget).val().trim();
          if (code)
            this.scan_barcode(code);
        }
      });
      this.$el.find(".etv2-barcode-camera-btn").on("click", () => this.open_camera_scanner());
      this.$el.on("click", ".fk-view-btn", (e) => {
        const mode = $(e.currentTarget).attr("data-view");
        if (!mode || mode === this.view_mode)
          return;
        this.view_mode = mode;
        this.$el.find(".fk-view-btn").removeClass("active");
        $(e.currentTarget).addClass("active");
        this.render_products();
      });
      this.$el.on("click", ".fk-cats-nav-prev", () => {
        this.$el.find(".etv2-cats")[0].scrollBy({ left: -160, behavior: "smooth" });
      });
      this.$el.on("click", ".fk-cats-nav-next", () => {
        this.$el.find(".etv2-cats")[0].scrollBy({ left: 160, behavior: "smooth" });
      });
      this.$el.on("click", ".fk-cat-chip", (e) => {
        const $chip = $(e.currentTarget);
        this.$el.find(".fk-cat-chip").removeClass("active");
        $chip.addClass("active");
        this.active_item_group = $chip.attr("data-group");
        this.load_products(this.$el.find(".etv2-sale-search input").val());
      });
      this.$el.on("click", ".fk-product-card, .fk-product-row", (e) => {
        const item = this.items.find((i) => i.item_code === $(e.currentTarget).attr("data-code"));
        if (item) {
          this.add_to_cart(item);
          frappe.utils.play_sound("submit");
        }
      });
      this.$el.on("click", ".fk-qty-btn-plus", (e) => this.change_qty($(e.currentTarget).attr("data-code"), 1));
      this.$el.on("click", ".fk-qty-btn-minus", (e) => this.change_qty($(e.currentTarget).attr("data-code"), -1));
      this.$el.on("click", ".fk-ci-eye", (e) => {
        const code = $(e.currentTarget).attr("data-code");
        const item = this.items.find((i) => i.item_code === code) || this.cart[code];
        if (!item) {
          frappe.show_alert({ message: __("Item not found."), indicator: "orange" });
          return;
        }
        try {
          this.open_item_details(item, { mode: "update" });
        } catch (err) {
          console.error("open_item_details failed:", err);
          frappe.show_alert({ message: __("Could not open item details. See console for error."), indicator: "red" });
        }
      });
      this.$el.on("click", ".fk-ci-remove", (e) => {
        e.stopPropagation();
        const code = $(e.currentTarget).attr("data-code");
        if (this.cart[code]) {
          delete this.cart[code];
          this.render_cart();
        }
      });
      this.$el.find(".etv2-sale-customer-btn").on("click", () => this.select_customer());
      this.$el.find(".etv2-sale-payment-btn").on("click", () => this.select_payment_mode());
      this.$el.find(".etv2-sale-tax-btn").on("click", () => this.select_tax_template());
      this.$el.find(".fk-hold-btn").on("click", () => this.hold_order());
      this.$el.find(".etv2-checkin-btn").on("click", () => this.checkout());
      this.$el.find(".fk-print-invoice-btn").on("click", () => this.save_and_print("EIMS Invoice"));
      this.$el.find(".fk-print-receipt-btn").on("click", () => this.save_and_print("Forkiva Sales Receipt"));
      this.$el.on("click", ".fk-discount-type-card", (e) => {
        const $card = $(e.currentTarget);
        this.discount_mode = $card.attr("data-mode");
        this.discount_value = 0;
        this.$el.find(".fk-discount-type-card").removeClass("active");
        $card.addClass("active");
        this.$el.find(".fk-discount-input").val("");
        this.render_cart();
      });
      let discountTimer;
      this.$el.find(".fk-discount-input").on("input", (e) => {
        clearTimeout(discountTimer);
        discountTimer = setTimeout(() => {
          let value = flt($(e.currentTarget).val()) || 0;
          if (this.discount_mode === "percentage" && value > 100) {
            frappe.msgprint({
              title: __("Invalid Discount"),
              indicator: "red",
              message: __("Discount cannot be greater than 100%.")
            });
            value = 0;
            $(e.currentTarget).val("");
          }
          this.discount_value = Math.max(0, value);
          this.render_cart();
        }, 200);
      });
      return this.$el;
    }
    load_item_groups() {
      const pv = this.shell.get_pv();
      frappe.call({
        method: `${pv}.item_group_query`,
        args: {
          doctype: "Item Group",
          txt: "",
          searchfield: "name",
          start: 0,
          page_len: 200,
          filters: { pos_profile: this.shell.pos_profile }
        }
      }).then((r) => {
        this.item_groups = (r.message || []).map((row) => row[0]);
        const $cats = this.$el.find(".etv2-cats");
        $cats.html(
          `<button class="fk-cat-chip active" data-group="">${__("All")}</button>` + this.item_groups.map((g) => `<button class="fk-cat-chip" data-group="${frappe.utils.escape_html(g)}">${frappe.utils.escape_html(g)}</button>`).join("")
        );
      });
    }
    load_products(search_term = "") {
      const pv = this.shell.get_pv();
      const page_key = `items:${this.active_item_group || this.shell.parent_item_group}:${search_term}`;
      const Offline = erpnext.POSV2.Offline;
      frappe.call({
        method: `${pv}.get_items`,
        args: {
          start: 0,
          page_length: 200,
          price_list: this.shell.price_list,
          item_group: this.active_item_group || this.shell.parent_item_group,
          pos_profile: this.shell.pos_profile,
          search_term
        }
      }).then((r) => {
        const data = r.message || { items: [] };
        Offline.cache_catalog(page_key, data);
        this.apply_products(data);
      }).catch(() => {
        const cached = Offline.load_cached_catalog(page_key);
        if (cached) {
          this.apply_products(cached);
          frappe.show_alert({ message: __("Offline mode \u2014 showing cached catalog."), indicator: "orange" });
        } else {
          frappe.show_alert({ message: __("No cached catalog for this view."), indicator: "red" });
        }
      });
    }
    apply_products(data) {
      this.items = data && data.items || [];
      this.warehouse = data && data.warehouse;
      this.render_products();
    }
    render_products() {
      const $grid = this.$el.find(".etv2-products");
      const is_list = this.view_mode === "list";
      $grid.toggleClass("fk-products-grid", !is_list);
      $grid.toggleClass("fk-products-list", is_list);
      if (!this.items.length) {
        $grid.html(
          `<div class="fk-empty" style="grid-column:1/-1;"><p class="fk-empty-title">${__("No products found.")}</p><span>${__("Try a different search or category.")}</span></div>`
        );
        return;
      }
      $grid.html(
        is_list ? this.items.map((i) => this.render_list_row(i)).join("") : this.items.map((i) => this.render_grid_card(i)).join("")
      );
    }
    render_grid_card(i) {
      const img = i.item_image ? `<img src="${i.item_image}" onerror="this.outerHTML = etv2_ph(${JSON.stringify(i.item_name)})" />` : `<div class="fk-product-img-ph">${frappe.utils.escape_html((i.item_name || i.item_code || "?").slice(0, 1).toUpperCase())}</div>`;
      const is_new = i.is_new;
      const has_original = flt(i.price_list_rate || 0) > 0 && flt(i.standard_rate || 0) > flt(i.price_list_rate || 0);
      return `
			<div class="fk-product-card" data-code="${frappe.utils.escape_html(i.item_code)}">
				<div class="fk-product-media">
					${img}
					${is_new ? `<span class="fk-product-badge-new">${__("NEW")}</span>` : ""}
				</div>
				<div class="fk-product-name">${frappe.utils.escape_html(i.item_name || i.item_code)}</div>
				<div class="fk-product-price">
					<span class="selling-price">${format_currency(i.price_list_rate || 0, i.currency)}</span>
					${has_original ? `<span class="original-price">${format_currency(i.standard_rate, i.currency)}</span>` : ""}
				</div>
				<div class="fk-product-stock">${__("Stock")}: ${flt(i.actual_qty || 0)}</div>
			</div>`;
    }
    render_list_row(i) {
      const img = i.item_image ? `<img src="${i.item_image}" onerror="this.outerHTML = etv2_ph_row(${JSON.stringify(i.item_name)})" />` : `<div class="fk-row-img-ph">${frappe.utils.escape_html((i.item_name || i.item_code || "?").slice(0, 1).toUpperCase())}</div>`;
      const has_original = flt(i.price_list_rate || 0) > 0 && flt(i.standard_rate || 0) > flt(i.price_list_rate || 0);
      const out_of_stock = flt(i.actual_qty || 0) <= 0;
      return `
			<div class="fk-product-row" data-code="${frappe.utils.escape_html(i.item_code)}">
				<div class="fk-row-media">${img}</div>
				<div class="fk-row-main">
					<div class="fk-row-name" title="${frappe.utils.escape_html(i.item_name || i.item_code)}">${frappe.utils.escape_html(i.item_name || i.item_code)}</div>
					<div class="fk-row-sub">${frappe.utils.escape_html(i.item_group || i.item_code)}</div>
				</div>
				<div class="fk-row-stock ${out_of_stock ? "fk-row-stock-out" : ""}">${__("Stock")}: ${flt(i.actual_qty || 0)}</div>
				<div class="fk-row-price">
					<span class="selling-price">${format_currency(i.price_list_rate || 0, i.currency)}</span>
					${has_original ? `<span class="original-price">${format_currency(i.standard_rate, i.currency)}</span>` : ""}
				</div>
				<button type="button" class="fk-row-add-btn" title="${__("Add to cart")}" tabindex="-1">
					<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
				</button>
			</div>`;
    }
    open_item_details(item, opts = {}) {
      var _a, _b;
      const me = this;
      const key = item.item_code;
      const in_cart = this.cart[key];
      const is_update = Boolean(in_cart);
      const full = this.items.find((i) => i.item_code === key) || item;
      if (!full || !full.item_code) {
        frappe.show_alert({ message: __("Item details unavailable."), indicator: "orange" });
        return;
      }
      const currency = full.currency || frappe.boot.sysdefaults.currency;
      const allow_rate_change = parseInt((_a = this.shell.settings.allow_rate_change) != null ? _a : 1, 10) !== 0;
      const allow_discount_change = parseInt((_b = this.shell.settings.allow_discount_change) != null ? _b : 1, 10) !== 0;
      const default_qty = is_update ? in_cart.qty : 1;
      const default_uom = is_update ? in_cart.uom : full.uom || full.stock_uom || full.sales_uom;
      const default_cf = is_update ? in_cart.conversion_factor : 1;
      const default_rate = is_update ? in_cart.rate : full.price_list_rate || 0;
      const default_discount = is_update ? in_cart.discount_percentage || 0 : 0;
      const default_wh = is_update ? in_cart.warehouse : this.warehouse;
      const dialog = new frappe.ui.Dialog({
        title: __("Item Details"),
        fields: [{ fieldtype: "HTML", fieldname: "body" }],
        primary_action_label: is_update ? __("Update Cart") : __("Add to Cart"),
        primary_action: async () => {
          const $w = dialog.fields_dict.body.$wrapper;
          const qty = flt($w.find(".fk-id-qty").val()) || 0;
          const wh = $w.find(".fk-id-warehouse").val() || this.warehouse;
          const row = this.cart[key] || this.cart_item_from(full);
          if (qty > 0 && !await this.check_stock(row, qty, wh))
            return;
          if (qty <= 0) {
            delete this.cart[key];
          } else {
            row.qty = qty;
            row.uom = $w.find(".fk-id-uom").val() || row.uom;
            row.conversion_factor = flt($w.find(".fk-id-conversion_factor").val()) || 1;
            row.rate = flt($w.find(".fk-id-rate").val()) || 0;
            row.discount_percentage = flt($w.find(".fk-id-discount").val()) || 0;
            row.price_list_rate = flt($w.find(".fk-id-price_list_rate").val()) || row.price_list_rate || 0;
            row.warehouse = wh;
            this.cart[key] = row;
          }
          dialog.hide();
          this.render_cart();
          frappe.show_alert({
            message: __("Cart updated \xB7 {0} \xD7 {1}", [qty, full.item_name]),
            indicator: "green"
          });
        }
      });
      dialog.$wrapper.addClass("fk-item-dialog");
      const img = full.item_image ? `<img class="etv2-id-img" src="${full.item_image}" onerror="this.outerHTML = etv2_ph_big(${JSON.stringify(full.item_name)})" />` : etv2_ph_big(full.item_name || full.item_code || "?");
      dialog.fields_dict.body.$wrapper.html(`
			<div class="etv2-item-dialog">
				<div class="etv2-id-media">${img}</div>
				<div class="etv2-id-name">${frappe.utils.escape_html(full.item_name || full.item_code)}</div>
				<div class="etv2-id-code">${frappe.utils.escape_html(full.item_code)}</div>
				<div class="etv2-id-stock ${flt(in_cart ? in_cart.actual_qty : full.actual_qty || 0) <= 0 ? "etv2-id-stock-out" : ""}">
					${__("Stock")}: ${flt(in_cart ? in_cart.actual_qty : full.actual_qty || 0)}
				</div>
				<div class="etv2-id-price">${format_currency(full.price_list_rate || 0, currency)}</div>
				${in_cart ? `<div class="etv2-id-in-cart">${__("In cart")}: ${in_cart.qty}</div>` : ""}
				<div class="fk-item-detail-form"></div>
			</div>
		`);
      const $form = dialog.fields_dict.body.$wrapper.find(".fk-item-detail-form");
      const uoms = full.uoms && full.uoms.length ? full.uoms : [{ uom: full.stock_uom || default_uom, conversion_factor: 1 }];
      let uom_options = "";
      uoms.forEach((u) => {
        const uom = u.uom || u;
        const cf = u.conversion_factor || 1;
        uom_options += `<option value="${frappe.utils.escape_html(uom)}" data-cf="${cf}">${frappe.utils.escape_html(uom)}</option>`;
      });
      $form.html(`
			<div class="fk-idf fk-idf-qty"><label>${__("Quantity")}</label><input type="number" min="0" step="1" class="fk-id-qty" value="${default_qty}"></div>
			<div class="fk-idf fk-idf-uom"><label>${__("UOM")}</label><select class="fk-id-uom">${uom_options}</select></div>
			<div class="fk-idf fk-idf-conversion_factor"><label>${__("Conversion Factor")}</label><input type="number" min="0" step="0.01" class="fk-id-conversion_factor" value="${default_cf}" ${default_uom === full.stock_uom ? "readonly" : ""}></div>
			<div class="fk-idf fk-idf-rate"><label>${__("Rate")}</label><input type="number" min="0" step="0.01" class="fk-id-rate" value="${default_rate}" ${allow_rate_change ? "" : "readonly"}></div>
			<div class="fk-idf fk-idf-discount"><label>${__("Discount (%)")}</label><input type="number" min="0" max="100" step="1" class="fk-id-discount" value="${default_discount}" ${allow_discount_change ? "" : "readonly"}></div>
			<div class="fk-idf fk-idf-warehouse"><label>${__("Warehouse")}</label><input type="text" class="fk-id-warehouse" value="${frappe.utils.escape_html(default_wh || "")}"></div>
			<div class="fk-idf fk-idf-actual_qty"><label>${__("Available Qty")}</label><input type="number" class="fk-id-actual_qty" value="${flt(in_cart ? in_cart.actual_qty : full.actual_qty || 0)}" readonly></div>
			<div class="fk-idf fk-idf-price_list_rate"><label>${__("Price List Rate")}</label><input type="number" class="fk-id-price_list_rate" value="${full.price_list_rate || 0}" readonly></div>
		`);
      $form.find(".fk-id-uom").val(default_uom);
      $form.find(".fk-id-discount").on("input", function() {
        let v = flt($(this).val()) || 0;
        if (v < 0)
          v = 0;
        if (v > 100)
          v = 100;
        const base = flt($form.find(".fk-id-price_list_rate").val()) || 0;
        $form.find(".fk-id-rate").val(flt(base * (1 - v / 100), 2));
      });
      $form.find(".fk-id-uom").on("change", function() {
        const $opt = $(this).find("option:selected");
        const cf = flt($opt.attr("data-cf")) || 1;
        const cfInput = $form.find(".fk-id-conversion_factor");
        cfInput.val(cf);
        cfInput.prop("readonly", $(this).val() === full.stock_uom);
      });
      $form.find(".fk-id-warehouse").on("change", function() {
        const warehouse = $(this).val();
        if (!warehouse)
          return;
        const pv = me.shell.get_pv();
        frappe.call({
          method: `${pv}.get_warehouse_stock`,
          args: { item_code: full.item_code, warehouse }
        }).then((r) => {
          const d = r.message || {};
          const available = flt(d.actual_qty);
          $form.find(".fk-id-actual_qty").val(available);
          if (available === 0 && d.is_stock_item) {
            $(this).val("");
            frappe.show_alert({ message: __("No stock in {0}", [warehouse]), indicator: "orange" });
          }
        });
      });
      dialog.show();
    }
    form_updated(fieldname, ctrl, controls, item) {
      if (this._suppress_onchange)
        return;
      const pv = this.shell.get_pv();
      if (fieldname === "discount_percentage") {
        let value = flt(ctrl.get_value()) || 0;
        if (value < 0)
          value = 0;
        if (value > 100)
          value = 100;
        ctrl.set_value(value);
        const base = flt(controls.price_list_rate.get_value()) || 0;
        controls.rate.set_value(flt(base * (1 - value / 100), 2));
      }
      if (fieldname === "uom") {
        frappe.call({
          method: `${pv}.get_uom_conversion_factor`,
          args: { item_code: item.item_code, uom: ctrl.get_value() }
        }).then((r) => {
          const cf = r.message && r.message.conversion_factor || 1;
          controls.conversion_factor.set_value(cf);
          controls.conversion_factor.df.read_only = ctrl.get_value() === item.stock_uom;
          controls.conversion_factor.refresh();
        });
      }
      if (fieldname === "warehouse") {
        const warehouse = ctrl.get_value();
        if (!warehouse)
          return;
        frappe.call({
          method: `${pv}.get_warehouse_stock`,
          args: { item_code: item.item_code, warehouse }
        }).then((r) => {
          const d = r.message || {};
          const available_qty = flt(d.actual_qty);
          controls.actual_qty.set_value(available_qty);
          if (available_qty === 0 && d.is_stock_item) {
            ctrl.set_value("");
            frappe.show_alert({
              message: __("Item {0} is not available under warehouse {1}.", [
                item.item_code.bold(),
                warehouse.bold()
              ]),
              indicator: "orange"
            });
          }
        });
      }
    }
    cart_item_from(item) {
      return {
        item_code: item.item_code,
        item_name: item.item_name || item.item_code,
        rate: item.price_list_rate || 0,
        price_list_rate: item.price_list_rate || 0,
        discount_percentage: 0,
        uom: item.uom || item.stock_uom || item.sales_uom,
        conversion_factor: 1,
        currency: item.currency,
        qty: 1,
        warehouse: this.warehouse,
        actual_qty: item.actual_qty || 0,
        is_stock_item: item.is_stock_item,
        stock_uom: item.stock_uom
      };
    }
    scan_barcode(code) {
      const me = this;
      const pv = this.shell.get_pv();
      frappe.call({
        method: `${pv}.get_item_by_barcode`,
        args: { barcode: code, price_list: this.shell.price_list, pos_profile: this.shell.pos_profile }
      }).then((r) => {
        const item = r.message || {};
        if (!item.item_code) {
          frappe.show_alert({ message: __("No product found for barcode: {0}", [code]), indicator: "orange" });
          return;
        }
        this.add_to_cart(item);
        this.$el.find(".etv2-sale-barcode input").val("");
        frappe.show_alert({ message: __("Scanned {0}", [item.item_name]), indicator: "green" });
      }).catch(() => {
        const cached = erpnext.POSV2.Offline.find_cached_item(code);
        if (cached) {
          this.add_to_cart(cached);
          this.$el.find(".etv2-sale-barcode input").val("");
          frappe.show_alert({ message: __("Scanned from cache: {0}", [cached.item_name]), indicator: "green" });
        } else {
          frappe.show_alert({ message: __("No product found for barcode: {0}", [code]), indicator: "orange" });
        }
      });
    }
    open_camera_scanner() {
      const me = this;
      if (!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)) {
        frappe.show_alert({ message: __("Camera access is not available on this device or browser."), indicator: "orange" });
        return;
      }
      const dialog = new frappe.ui.Dialog({
        title: __("Scan Barcode / QR"),
        fields: [{ fieldtype: "HTML", fieldname: "body" }]
      });
      dialog.$wrapper.addClass("fk-scanner-dialog");
      dialog.fields_dict.body.$wrapper.html(`
			<div class="fk-scanner-wrap">
				<video class="fk-scanner-video" autoplay playsinline muted></video>
				<div class="fk-scanner-frame"></div>
				<canvas class="fk-scanner-canvas" style="display:none;"></canvas>
			</div>
			<div class="fk-scanner-hint">${__("Point the camera at a barcode or QR code")}</div>
			<div class="fk-scanner-actions">
				<button type="button" class="fk-scanner-cancel-btn">${__("Cancel")}</button>
			</div>
		`);
      const $wrapper = dialog.fields_dict.body.$wrapper;
      const video = $wrapper.find(".fk-scanner-video")[0];
      const canvas = $wrapper.find(".fk-scanner-canvas")[0];
      const ctx = canvas.getContext("2d");
      let stream = null;
      let rafId = null;
      let stopped = false;
      let detector = null;
      let use_jsqr = false;
      const cleanup = () => {
        if (stopped)
          return;
        stopped = true;
        if (rafId)
          cancelAnimationFrame(rafId);
        if (stream) {
          stream.getTracks().forEach((t) => t.stop());
          stream = null;
        }
      };
      dialog.$wrapper.on("hidden.bs.modal", cleanup);
      $wrapper.on("click", ".fk-scanner-cancel-btn", () => dialog.hide());
      const on_detected = (value) => {
        if (stopped || !value)
          return;
        cleanup();
        dialog.hide();
        this.$el.find(".etv2-sale-barcode input").val(value);
        this.scan_barcode(value);
      };
      const tick = async () => {
        if (stopped)
          return;
        if (video.readyState === video.HAVE_ENOUGH_DATA) {
          try {
            if (detector) {
              const codes = await detector.detect(video);
              if (codes && codes.length) {
                on_detected(codes[0].rawValue);
                return;
              }
            } else if (use_jsqr && window.jsQR) {
              canvas.width = video.videoWidth;
              canvas.height = video.videoHeight;
              ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
              const frame = ctx.getImageData(0, 0, canvas.width, canvas.height);
              const result = window.jsQR(frame.data, frame.width, frame.height);
              if (result && result.data) {
                on_detected(result.data);
                return;
              }
            }
          } catch (err) {
          }
        }
        rafId = requestAnimationFrame(tick);
      };
      const start = async () => {
        try {
          stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
          if (stopped) {
            stream.getTracks().forEach((t) => t.stop());
            return;
          }
          video.srcObject = stream;
          await video.play();
          if ("BarcodeDetector" in window) {
            try {
              const formats = await window.BarcodeDetector.getSupportedFormats();
              detector = new window.BarcodeDetector({ formats });
            } catch (e) {
              detector = null;
            }
          }
          if (!detector) {
            use_jsqr = true;
            if (!window.jsQR) {
              await me.load_script("https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.js");
            }
          }
          tick();
        } catch (err) {
          frappe.show_alert({
            message: __("Could not access the camera: {0}", [err && err.message || err]),
            indicator: "red"
          });
          dialog.hide();
        }
      };
      dialog.show();
      start();
    }
    load_script(src) {
      return new Promise((resolve, reject) => {
        if (document.querySelector(`script[src="${src}"]`)) {
          resolve();
          return;
        }
        const s = document.createElement("script");
        s.src = src;
        s.onload = () => resolve();
        s.onerror = () => reject(new Error("Failed to load script: " + src));
        document.head.appendChild(s);
      });
    }
    async add_to_cart(item, qty) {
      const key = item.item_code;
      qty = flt(qty) || 1;
      const row = this.cart[key];
      if (row) {
        row.qty = flt(row.qty || 0) + qty;
      } else {
        const new_row = this.cart_item_from(item);
        new_row.qty = qty;
        this.cart[key] = new_row;
      }
      this.render_cart();
    }
    async change_qty(item_code, delta) {
      if (!this.cart[item_code])
        return;
      const row = this.cart[item_code];
      const next = flt(row.qty || 0) + flt(delta);
      const wh = row.warehouse || this.warehouse;
      if (next > row.qty && !await this.check_stock(row, next - row.qty, wh))
        return;
      row.qty = Math.max(0, next);
      if (row.qty <= 0)
        delete this.cart[item_code];
      this.render_cart();
    }
    async check_stock(item, qty_needed, warehouse) {
      if (!item || !item.item_code)
        return true;
      const r = await frappe.call({
        method: "erpnext.accounts.doctype.pos_invoice.pos_invoice.get_stock_availability",
        args: { item_code: item.item_code, warehouse }
      });
      const resp = r.message || [0, 1, 0];
      const available = flt(resp[0]);
      const is_stock_item = resp[1];
      const allow_negative = flt(resp[2]);
      if (allow_negative || !is_stock_item)
        return true;
      if (available <= 0) {
        frappe.show_alert({
          message: __("Item {0} is not available under warehouse {1}.", [
            item.item_code.bold(),
            (warehouse || "\u2014").bold()
          ]),
          indicator: "orange"
        });
        frappe.utils.play_sound("error");
        return false;
      }
      if (available < qty_needed) {
        frappe.show_alert({
          message: __(
            "Stock quantity not enough for Item Code: {0} under warehouse {1}. Available quantity {2} {3}.",
            [
              item.item_code.bold(),
              (warehouse || "\u2014").bold(),
              available,
              (item.stock_uom || "").bold()
            ]
          ),
          indicator: "orange"
        });
        frappe.utils.play_sound("error");
        return false;
      }
      return true;
    }
    cart_subtotal() {
      return Object.keys(this.cart).reduce((s, k) => s + this.cart[k].rate * this.cart[k].qty, 0);
    }
    cart_net_subtotal() {
      const gross = this.cart_subtotal();
      const rate = flt(this.tax_rate || 0);
      if (this.is_tax_inclusive() && rate > 0) {
        return gross / (1 + rate / 100);
      }
      return gross;
    }
    is_tax_inclusive() {
      return !!(this.shell.settings && this.shell.settings.posa_tax_inclusive);
    }
    cart_discount() {
      const net = this.cart_net_subtotal();
      if (this.discount_mode === "percentage") {
        return net * flt(this.discount_value || 0) / 100;
      }
      return Math.min(flt(this.discount_value || 0), net);
    }
    cart_tax() {
      const taxable = this.cart_net_subtotal() - this.cart_discount();
      return taxable * flt(this.tax_rate || 0) / 100;
    }
    cart_total() {
      return this.cart_net_subtotal() - this.cart_discount() + this.cart_tax();
    }
    render_cart() {
      const $list = this.$el.find(".fk-cart-list");
      const keys = Object.keys(this.cart);
      const count = keys.reduce((sum, k) => sum + this.cart[k].qty, 0);
      this.$el.find(".fk-cart-count").text(count);
      const $items = this.$el.find(".fk-cart-items");
      const $empty = this.$el.find(".fk-cart-list > .fk-empty");
      if (!keys.length) {
        $items.empty();
        $empty.show();
      } else {
        $empty.hide();
        $items.html(
          keys.map((k) => {
            const c = this.cart[k];
            return `
            <div class="fk-cart-item">
                <div class="fk-cart-item-row">
                    <div class="fk-cart-item-name" title="${frappe.utils.escape_html(c.item_name)}">
                        ${frappe.utils.escape_html(c.item_name)}
                        <button class="fk-ci-eye" data-code="${frappe.utils.escape_html(k)}" type="button" title="${__("View item details")}">
                            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                        </button>
                        <button class="fk-ci-remove" data-code="${frappe.utils.escape_html(k)}" type="button" title="${__("Remove item")}">
                            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"></path><path d="M10 11v6"></path><path d="M14 11v6"></path></svg>
                        </button>
                    </div>
                    <div class="fk-qty-box">
                        <button class="fk-qty-btn fk-qty-btn-minus" data-code="${frappe.utils.escape_html(k)}" type="button">\u2212</button>
                        <span class="fk-qty-value">${c.qty}</span>
                        <button class="fk-qty-btn fk-qty-btn-plus" data-code="${frappe.utils.escape_html(k)}" type="button">+</button>
                    </div>
                    <div class="fk-cart-item-price">${format_currency(c.rate * c.qty, c.currency)}</div>
                </div>
            </div>`;
          }).join("")
        );
      }
      const subtotal = this.cart_net_subtotal();
      const discount = this.cart_discount();
      const tax = this.cart_tax();
      const grand_total = subtotal - discount + tax;
      this.$el.find(".fk-subtotal").text(format_currency(subtotal));
      this.$el.find(".fk-row-discount").text(`- ${format_currency(discount)}`);
      this.$el.find(".fk-discount-input-row .fk-discount-value").text(`- ${format_currency(discount)}`);
      this.$el.find(".fk-tax-value").text(format_currency(tax));
      this.$el.find(".fk-tax-rate-label").text(`${flt(this.tax_rate || 0)}%`);
      this.$el.find(".fk-tax-row").toggle(this.tax_template && flt(this.tax_rate || 0) > 0);
      this.$el.find(".fk-grand").text(format_currency(grand_total));
      this.$el.find(".fk-checkin-total").text(format_currency(grand_total));
      this.$el.find(".fk-discount-input-row").show();
    }
    select_customer() {
      const me = this;
      const dialog = new frappe.ui.Dialog({
        title: __("Select Customer"),
        fields: [{ fieldtype: "HTML", fieldname: "body" }],
        primary_action_label: __("Choose Customer"),
        primary_action: () => {
          me.customer = me.walk_in_customer || null;
          me.$el.find(".etv2-sale-customer-btn span").html(`${__("Customer")}: <b>${me.walk_in_customer ? __("Walk-In Customer") : __("Choose Customer")}</b>`);
          dialog.hide();
        }
      });
      dialog.$wrapper.addClass("fk-customer-picker");
      const $body = dialog.fields_dict.body.$wrapper;
      $body.addClass("etv2-customer-picker");
      $body.html(`
			<div class="fk-search-box etv2-customer-picker-search">
				<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
				<input type="text" placeholder="${__("Search customers\u2026")}" />
			</div>
			<div class="etv2-customer-picker-list"></div>
		`);
      const load = (term = "") => {
        const pv = this.shell.get_pv();
        frappe.call({
          method: `${pv}.get_customers`,
          args: { search_term: term, limit: 50 }
        }).then((r) => {
          let rows = r.message || [];
          if (this.shell.customer_groups.length) {
            rows = rows.filter((c) => this.shell.customer_groups.includes(c.customer_group));
          }
          const $list = $body.find(".etv2-customer-picker-list");
          if (!rows.length) {
            $list.html(`<div class="etv2-empty">${__("No customers found.")}</div>`);
            return;
          }
          $list.html(
            rows.map((c) => `
						<div class="etv2-customer-picker-row" data-name="${frappe.utils.escape_html(c.name)}">
							<div class="etv2-customer-avatar">
								${c.image ? `<img src="${c.image}" onerror="this.remove()" />` : frappe.utils.escape_html((c.customer_name || c.name).slice(0, 1).toUpperCase())}
							</div>
							<div class="etv2-customer-picker-info">
								<div class="etv2-customer-picker-name">${frappe.utils.escape_html(c.customer_name || c.name)}</div>
								<div class="etv2-customer-picker-sub">${frappe.utils.escape_html(c.mobile_no || c.customer_group || "")}</div>
							</div>
						</div>`).join("")
          );
        });
      };
      let timer;
      $body.on("input", ".etv2-customer-picker-search input", (e) => {
        clearTimeout(timer);
        timer = setTimeout(() => load($(e.currentTarget).val()), 250);
      });
      $body.on("click", ".etv2-customer-picker-row", (e) => {
        const name = $(e.currentTarget).attr("data-name");
        frappe.db.get_value("Customer", name, ["customer_name"]).then(({ message }) => {
          me.customer = name;
          me.$el.find(".etv2-sale-customer-btn span").html(`${__("Customer")}: <b>${frappe.utils.escape_html(message && message.customer_name || name)}</b>`);
          dialog.hide();
        });
      });
      load();
      dialog.show();
    }
    select_payment_mode() {
      const modes = (this.shell.settings.payments || []).map((p) => p.mode_of_payment);
      if (!modes.length) {
        frappe.show_alert({ message: __("No payment modes configured on this POS Profile."), indicator: "orange" });
        return;
      }
      const dialog = new frappe.ui.Dialog({
        title: __("Select Payment Method"),
        fields: [{ fieldtype: "HTML", fieldname: "body" }]
      });
      dialog.fields_dict.body.$wrapper.html(
        `<div class="fk-pay-modes">` + modes.map((m) => `
			<div class="fk-pay-mode ${m === this.payment_mode ? "active" : ""}" data-mode="${frappe.utils.escape_html(m)}">
				<span class="fk-pm-info"><span class="fk-pm-name">${frappe.utils.escape_html(m)}</span></span>
				<span class="fk-pm-check"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"></path></svg></span>
			</div>`).join("") + `</div>`
      );
      dialog.fields_dict.body.$wrapper.on("click", ".fk-pay-mode", (e) => {
        this.payment_mode = $(e.currentTarget).attr("data-mode");
        this.$el.find(".fk-payment-label").text(this.payment_mode);
        dialog.hide();
      });
      dialog.show();
    }
    load_tax_template() {
      const me = this;
      const pv = this.shell.get_pv();
      frappe.call({
        method: `${pv}.get_tax_templates`
      }).then((r) => {
        const data = r.message || {};
        const templates = data.templates || [];
        if (!this.tax_template) {
          this.tax_template = data.current || null;
        }
        const match = templates.find((t) => t.name === this.tax_template);
        this.tax_rate = match ? match.rate : null;
        this.update_tax_ui();
      });
    }
    select_tax_template() {
      const me = this;
      const pv = this.shell.get_pv();
      frappe.call({
        method: `${pv}.get_tax_templates`
      }).then((r) => {
        const data = r.message || {};
        const templates = data.templates || [];
        const dialog = new frappe.ui.Dialog({
          title: __("Select Tax Template"),
          fields: [{ fieldtype: "HTML", fieldname: "body" }]
        });
        dialog.fields_dict.body.$wrapper.html(
          `<div class="fk-pay-modes">` + templates.map((t) => `
					<div class="fk-pay-mode ${t.name === this.tax_template ? "active" : ""}" data-tax="${frappe.utils.escape_html(t.name)}">
						<span class="fk-pm-info">
							<span class="fk-pm-name">${frappe.utils.escape_html(t.name)}</span>
							<span class="fk-pm-sub">${__("Tax")} ${flt(t.rate)}%</span>
						</span>
						<span class="fk-pm-check"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"></path></svg></span>
					</div>`).join("") + `</div>`
        );
        dialog.fields_dict.body.$wrapper.on("click", ".fk-pay-mode", (e) => {
          const name = $(e.currentTarget).attr("data-tax");
          const match = templates.find((t) => t.name === name);
          me.tax_template = name;
          me.tax_rate = match ? match.rate : null;
          me.shell.tax_template = name;
          me.update_tax_ui();
          me.render_cart();
          dialog.hide();
          frappe.call({
            method: `${pv}.set_default_tax_template`,
            args: { tax_template: name }
          }).then((res) => {
            if (!res.exc) {
              frappe.show_alert({ message: __("Default tax template set to {0}.", [name]), indicator: "green" });
            }
          });
        });
        dialog.show();
      });
    }
    update_tax_ui() {
      const label = this.tax_template || __("Select");
      this.$el.find(".fk-tax-label").text(label);
      this.$el.find(".fk-tax-rate-label").text(`${flt(this.tax_rate || 0)}%`);
    }
    build_order_doc() {
      const default_customer = this.customer || this.walk_in_customer || this.shell.settings && this.shell.settings.customer || null;
      if (!default_customer) {
        frappe.show_alert({ message: __("Select a customer before checkout."), indicator: "orange" });
        return null;
      }
      if (!Object.keys(this.cart).length) {
        frappe.show_alert({ message: __("Cart is empty."), indicator: "orange" });
        return null;
      }
      const doc = {
        doctype: "POS Invoice",
        is_pos: 1,
        docstatus: 0,
        company: this.shell.company,
        pos_profile: this.shell.pos_profile,
        customer: default_customer,
        set_warehouse: this.shell.warehouse,
        currency: frappe.boot.sysdefaults.currency,
        posting_date: frappe.datetime.now_date(),
        posting_time: frappe.datetime.now_time(),
        items: Object.keys(this.cart).map((k) => {
          const c = this.cart[k];
          return {
            item_code: c.item_code,
            qty: c.qty,
            rate: c.rate,
            uom: c.uom,
            conversion_factor: c.conversion_factor || 1,
            discount_percentage: c.discount_percentage || 0,
            price_list_rate: c.price_list_rate || c.rate,
            warehouse: c.warehouse || this.shell.warehouse
          };
        })
      };
      if (this.tax_template) {
        doc.taxes_and_charges = this.tax_template;
      }
      if (this.discount_value > 0) {
        doc.apply_discount_on = "Net Total";
        if (this.discount_mode === "percentage") {
          doc.additional_discount_percentage = flt(this.discount_value);
        } else {
          doc.discount_amount = flt(this.discount_value);
        }
      }
      if (this.payment_mode) {
        doc.payments = [{ mode_of_payment: this.payment_mode, amount: this.cart_total() }];
      }
      return doc;
    }
    hold_order() {
      const doc = this.build_order_doc();
      if (!doc)
        return;
      const pv = this.shell.get_pv();
      frappe.call({
        method: `${pv}.save_held_order`,
        args: { doc },
        freeze: true
      }).then((r) => {
        if (r.message && r.message.status === "ok") {
          frappe.show_alert({ message: __("Order held: {0}", [r.message.invoice_name]), indicator: "blue" });
          this.cart = {};
          this.discount_value = 0;
          this.render_cart();
        }
      });
    }
    save_and_print(print_format) {
      if (!Object.keys(this.cart).length) {
        frappe.show_alert({ message: __("You must add at least one item to print."), indicator: "orange" });
        frappe.utils.play_sound("error");
        return;
      }
      const doc = this.build_order_doc();
      if (!doc)
        return;
      const pv = this.shell.get_pv();
      const win = ethiotel_print_placeholder();
      frappe.call({
        method: `${pv}.save_held_order`,
        args: { doc },
        freeze: true
      }).then((r) => {
        if (r.message && r.message.status === "ok" && win) {
          win.location = ethiotel_print_url("POS Invoice", r.message.invoice_name, print_format);
        } else if (win) {
          win.close();
        }
      });
    }
    checkout() {
      const doc = this.build_order_doc();
      if (!doc)
        return;
      const me = this;
      const total = this.cart_total();
      const pay_rows = this.shell.settings.payments || [];
      const modes = pay_rows.map((p) => p.mode_of_payment);
      const def_row = pay_rows.find((p) => p.default) || {};
      const default_mode = def_row.mode_of_payment || modes[0] || "Cash";
      let quick_pay = this.quick_pay_amounts(total);
      let selected_mode = this.payment_mode || default_mode;
      const dialog = new frappe.ui.Dialog({
        title: __("Checkout"),
        fields: [{ fieldtype: "HTML", fieldname: "body" }],
        primary_action: null
      });
      dialog.$wrapper.addClass("fk-pay-dialog");
      const $body = dialog.fields_dict.body.$wrapper;
      $body.html(`
			<div class="fk-pay-layout">
				<div class="fk-pay-finalize">
					<div class="fk-pay-title">${__("Finalize Payment")}</div>
					<div>
						<div class="fk-pay-section-title">${__("Customer TIN (optional)")}</div>
						<div class="fk-pay-amount-row">
							<input type="text" class="fk-buyer-tin-input" placeholder="${__("Buyer TIN")}" autocomplete="off" />
						</div>
					</div>
					<div>
						<div class="fk-pay-section-title">${__("Payment Mode")}</div>
						<div class="fk-pay-modes">
							${(modes.length ? modes : [default_mode]).map((m) => `
									<div class="fk-pay-mode ${m === selected_mode ? "active" : ""}" data-mode="${frappe.utils.escape_html(m)}">
										<span class="fk-pm-info"><span class="fk-pm-name">${frappe.utils.escape_html(m)}</span></span>
										<span class="fk-pm-check"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"></path></svg></span>
									</div>`).join("")}
						</div>
					</div>
					<div>
						<div class="fk-pay-section-title">${__("Amount Received")}</div>
						<div class="fk-pay-amount-row">
							<div class="fk-pay-input">
								<span>ETB</span>
								<input type="number" class="fk-amount-input" value="${total}" min="0" />
							</div>
						</div>
					</div>
					<div>
						<div class="fk-pay-section-title">${__("Numeric Keypad")}</div>
						<div class="fk-keypad-grid fk-keypad"></div>
						<button type="button" class="fk-calculator-open-btn fk-calculator-btn">
							<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2"></rect><line x1="8" y1="6" x2="16" y2="6"></line><line x1="8" y1="11" x2="8" y2="11"></line><line x1="12" y1="11" x2="12" y2="11"></line><line x1="16" y1="11" x2="16" y2="11"></line><line x1="8" y1="15" x2="8" y2="15"></line><line x1="12" y1="15" x2="12" y2="15"></line><line x1="16" y1="15" x2="16" y2="15"></line><line x1="8" y1="19" x2="8" y2="19"></line><line x1="12" y1="19" x2="12" y2="19"></line><line x1="16" y1="19" x2="16" y2="19"></line></svg>
							${__("Calculator")}
						</button>
					</div>
					<div>
						<div class="fk-pay-section-title">${__("Quick Pay")}</div>
						<div class="fk-quick-pay-grid fk-quick-pay"></div>
					</div>
				</div>
				<div class="fk-pay-summary">
					<div class="fk-summary-rows">
						<div class="fk-summary-row"><span class="fk-sr-title">${__("Total Products")}</span><span class="fk-sr-value fk-sum-count">0</span></div>
						<div class="fk-summary-row"><span class="fk-sr-title">${__("Sub Total")}</span><span class="fk-sr-value fk-sum-subtotal">0.00</span></div>
						<div class="fk-summary-row"><span class="fk-sr-title">${__("Discount")}</span><span class="fk-sr-value fk-sum-discount">0.00</span></div>
						<div class="fk-summary-row fk-sr-grand"><span class="fk-sr-title">${__("Grand Total")}</span><span class="fk-sr-value fk-sum-grand">0.00</span></div>
						<div class="fk-summary-row"><span class="fk-sr-title">${__("Amount Received")}</span><span class="fk-sr-value fk-sum-received">0.00</span></div>
						<div class="fk-summary-row fk-sr-change"><span class="fk-sr-title">${__("Change Return")}</span><span class="fk-sr-value fk-sum-change">0.00</span></div>
					</div>
					<div class="fk-pay-footer">
						
						<div class="fk-pay-footer-btns">
	<button type="button" class="fk-btn-cancel fk-pay-cancel-btn">${__("Cancel")}</button>
	<button type="button" class="fk-btn-charge fk-charge-btn">${__("Charge")}</button>
</div>
<div class="fk-pay-secondary-btns">
	<button type="button" class="fk-btn-secondary fk-checkout-hold-btn">${__("Hold")}</button>
</div>
					</div>
				</div>
			</div>
		`);
      $body.on("click", ".fk-pay-mode", (e) => {
        selected_mode = $(e.currentTarget).attr("data-mode");
        $body.find(".fk-pay-mode").removeClass("active");
        $(e.currentTarget).addClass("active");
      });
      $body.on("click", ".fk-checkout-hold-btn", () => {
        dialog.hide();
        this.hold_order();
      });
      const $sum = {
        count: $body.find(".fk-sum-count"),
        subtotal: $body.find(".fk-sum-subtotal"),
        discount: $body.find(".fk-sum-discount"),
        grand: $body.find(".fk-sum-grand"),
        received: $body.find(".fk-sum-received"),
        change: $body.find(".fk-sum-change")
      };
      const count = Object.keys(this.cart).reduce((s, k) => s + this.cart[k].qty, 0);
      const subtotal = this.cart_subtotal();
      const discount = this.cart_discount();
      $sum.count.text(count);
      $sum.subtotal.text(format_currency(subtotal));
      $sum.discount.text(`- ${format_currency(discount)}`);
      $sum.grand.text(format_currency(total));
      const render_summary = () => {
        const recv = flt($body.find(".fk-amount-input").val()) || 0;
        const change = recv - total;
        $sum.received.text(format_currency(recv));
        $sum.change.text(format_currency(Math.max(change, 0)));
        $sum.change.toggleClass("fk-sr-neg", change < 0);
      };
      const keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", ".", "0", "C"];
      $body.find(".fk-keypad").html(
        keys.map(
          (k) => `
						<button type="button" class="fk-pad-btn ${k === "C" ? "fk-pad-clear" : ""}" data-key="${k === "." ? "dot" : k}">${k}</button>`
        ).join("")
      );
      $body.on("click", ".fk-pad-btn", (e) => {
        const k = $(e.currentTarget).attr("data-key");
        const $input = $body.find(".fk-amount-input");
        let val = $input.val();
        if (k === "C") {
          $input.val(total);
        } else if (k === "dot") {
          if (!String(val).includes("."))
            $input.val(val === "" ? "0." : val + ".");
        } else {
          $input.val(val === "" ? k : String(val) + k);
        }
        render_summary();
      });
      $body.find(".fk-quick-pay").html(
        quick_pay.map((amt) => `<button type="button" class="fk-quick-pay-btn" data-amt="${amt}">+ ${format_currency(amt)}</button>`).join("")
      );
      $body.on("click", ".fk-quick-pay-btn", (e) => {
        $body.find(".fk-amount-input").val($(e.currentTarget).attr("data-amt"));
        render_summary();
      });
      $body.find(".fk-amount-input").on("input", render_summary);
      render_summary();
      $body.find(".fk-calculator-btn").on("click", () => {
        this.open_calculator(total, (value) => {
          $body.find(".fk-amount-input").val(flt(value));
          render_summary();
        });
      });
      const do_charge = (with_print) => {
        const amount_received = flt($body.find(".fk-amount-input").val()) || 0;
        if (amount_received < total) {
          frappe.show_alert({ message: __("Amount received is less than total."), indicator: "orange" });
          return;
        }
        doc.payments = [{ mode_of_payment: selected_mode, amount: total }];
        const buyer_tin = String($($body).find(".fk-buyer-tin-input").val() || "").replace(/\D/g, "");
        if (buyer_tin) {
          doc.custom_buyer_tin = buyer_tin;
        } else {
          doc.custom_buyer_tin = null;
        }
        if (!erpnext.POSV2.Offline.is_online()) {
          erpnext.POSV2.Offline.queue_order(doc);
          dialog.hide();
          this.cart = {};
          this.customer = null;
          this.payment_mode = null;
          this.$el.find(".fk-payment-label").text(__("Select"));
          this.discount_value = 0;
          this.$el.find(".etv2-sale-customer-btn span").html(`${__("Customer")}: <b>${this.walk_in_customer ? __("Walk-In Customer") : __("Choose Customer")}</b>`);
          this.$el.find(".fk-discount-input").val("");
          this.render_cart();
          frappe.show_alert({
            message: __("Offline mode: order {0} queued. It will be submitted automatically when the connection returns.", [format_currency(total)]),
            indicator: "orange"
          });
          return;
        }
        const pv = this.shell.get_pv();
        frappe.call({
          method: `${pv}.save_held_order`,
          args: { doc },
          freeze: true
        }).then((r) => {
          if (r.message && r.message.status === "ok") {
            frappe.call({ method: `${pv}.submit_invoice`, args: { name: r.message.invoice_name } }).then((res) => {
              if (res.message && res.message.status === "ok") {
                this.shell.last_invoice_name = res.message.invoice_name;
                const change = flt(amount_received) - total;
                dialog.hide();
                frappe.show_alert({
                  message: __("Invoice {0} submitted \xB7 change {1}", [res.message.invoice_name, format_currency(change)]),
                  indicator: "green"
                });
                this.cart = {};
                this.customer = null;
                this.payment_mode = null;
                this.$el.find(".fk-payment-label").text(__("Select"));
                this.discount_value = 0;
                this.$el.find(".etv2-sale-customer-btn span").html(`${__("Customer")}: <b>${this.walk_in_customer ? __("Walk-In Customer") : __("Choose Customer")}</b>`);
                this.$el.find(".fk-discount-input").val("");
                this.render_cart();
                this.finalize_sale_with_mor(res.message.invoice_name);
              } else {
                frappe.show_alert({
                  message: res.message && res.message.message || __("Invoice submission failed."),
                  indicator: "red"
                });
              }
            }).catch((err) => {
              console.error("Invoice submission error:", err);
            });
          } else {
            frappe.show_alert({
              message: r.message && r.message.message || __("Could not save the order."),
              indicator: "red"
            });
          }
        }).catch((err) => {
          console.error("Order save error:", err);
        });
      };
      $body.find(".fk-charge-btn").on("click", () => do_charge(false));
      $body.find(".fk-pay-cancel-btn").on("click", () => dialog.hide());
      dialog.show();
    }
    finalize_sale_with_mor(invoice_name) {
      const pv = this.shell.get_pv();
      frappe.call({
        method: `${pv}.queue_mor_registration`,
        args: { pos_invoice_name: invoice_name }
      }).then((r) => {
        const res = r.message || {};
        if (res.status === "queued") {
          frappe.show_alert({
            message: __("Sending to MoR in background\u2026"),
            indicator: "blue"
          });
        } else if (res.status === "error") {
          frappe.show_alert({
            message: res.message || __("MoR registration not queued."),
            indicator: "orange"
          });
        }
      }).catch((err) => {
        console.error("MoR queue error:", err);
      });
      frappe.call({
        method: `${pv}.get_light_receipt`,
        args: { pos_invoice_name: invoice_name }
      }).then((r) => {
        const res = r.message || {};
        if (!(res.status === "ok" && res.html)) {
          return;
        }
        const safe = String(res.html).replace(/<script[\s\S]*?<\/script>/gi, "").replace(/<\/?(?:html|head|body)[^>]*>/gi, "");
        const d = new frappe.ui.Dialog({
          title: __("Sales Receipt"),
          size: "small",
          primary_action_label: __("Print"),
          primary_action: () => {
            const w = window.open();
            if (w) {
              w.document.write(safe);
              w.document.close();
              w.focus();
              w.print();
            }
            d.hide();
          }
        });
        d.$body.html(safe);
        d.show();
      }).catch((err) => {
        console.error("Light receipt error:", err);
      });
    }
    open_calculator(initial, on_apply) {
      const dialog = new frappe.ui.Dialog({
        title: __("Calculator"),
        fields: [{ fieldtype: "HTML", fieldname: "body" }],
        primary_action_label: __("OK"),
        primary_action: () => {
          const res = dialog.fields_dict.body.$wrapper.find(".fk-calc-preview").text();
          const parsed = parseFloat(String(res).replace(/[^\d.-]/g, ""));
          if (!isNaN(parsed))
            on_apply(parsed);
          dialog.hide();
        }
      });
      dialog.$wrapper.addClass("fk-calc-dialog");
      dialog.fields_dict.body.$wrapper.addClass("fk-calc-card");
      const $w = dialog.fields_dict.body.$wrapper;
      $w.html(`
			<div class="fk-calc-content">
				<div class="fk-calc-display">
					<div class="fk-calc-expression"></div>
					<div class="fk-calc-preview">${initial || 0}</div>
				</div>
				<div class="fk-calc-grid">
					<button type="button" class="fk-calc-btn fk-calc-clear" data-k="C">C</button>
					<button type="button" class="fk-calc-btn fk-calc-op" data-k="/">\xF7</button>
					<button type="button" class="fk-calc-btn fk-calc-op" data-k="*">\xD7</button>
					<button type="button" class="fk-calc-btn fk-calc-clear" data-k="back">\u232B</button>
					<button type="button" class="fk-calc-btn" data-k="7">7</button>
					<button type="button" class="fk-calc-btn" data-k="8">8</button>
					<button type="button" class="fk-calc-btn" data-k="9">9</button>
					<button type="button" class="fk-calc-btn fk-calc-op" data-k="-">\u2212</button>
					<button type="button" class="fk-calc-btn" data-k="4">4</button>
					<button type="button" class="fk-calc-btn" data-k="5">5</button>
					<button type="button" class="fk-calc-btn" data-k="6">6</button>
					<button type="button" class="fk-calc-btn fk-calc-op" data-k="+">+</button>
					<button type="button" class="fk-calc-btn" data-k="1">1</button>
					<button type="button" class="fk-calc-btn" data-k="2">2</button>
					<button type="button" class="fk-calc-btn" data-k="3">3</button>
					<button type="button" class="fk-calc-btn fk-calc-op" data-k="=">=</button>
					<button type="button" class="fk-calc-btn" data-k="0">0</button>
					<button type="button" class="fk-calc-btn" data-k=".">.</button>
					<button type="button" class="fk-calc-btn fk-calc-op" data-k="00">00</button>
				</div>
			</div>
			<div class="fk-calc-actions">
				<button type="button" class="fk-calc-cancel-btn">${__("Cancel")}</button>
				<button type="button" class="fk-calc-apply-btn">${__("Apply")}</button>
			</div>
		`);
      let expr = String(initial || 0);
      const $expr = $w.find(".fk-calc-expression");
      const $preview = $w.find(".fk-calc-preview");
      const update = () => {
        $preview.text(expr || "0");
      };
      const compute = (e) => {
        try {
          const r = Function(`"use strict"; return (${e})`)();
          return isNaN(r) ? null : r;
        } catch (err) {
          return null;
        }
      };
      $w.on("click", ".fk-calc-btn", (e) => {
        const k = $(e.currentTarget).attr("data-k");
        if (k === "C") {
          expr = "0";
        } else if (k === "back") {
          expr = expr.length > 1 ? expr.slice(0, -1) : "0";
        } else if (k === "=") {
          const r = compute(expr);
          if (r !== null) {
            $expr.text(`${expr} =`);
            expr = String(round(r, 2));
          }
        } else if (["+", "-", "*", "/"].includes(k)) {
          expr = expr + k;
        } else {
          expr = expr === "0" ? k : expr + k;
        }
        update();
      });
      $w.find(".fk-calc-apply-btn").on("click", () => {
        const r = compute(expr);
        if (r !== null)
          on_apply(round(r, 2));
        dialog.hide();
      });
      $w.find(".fk-calc-cancel-btn").on("click", () => dialog.hide());
      dialog.show();
    }
    quick_pay_amounts(total) {
      const t = Math.ceil(total);
      const denominations = [10, 20, 50, 100, 200, 500, 1e3, 2e3];
      const out = [];
      for (const d of denominations) {
        const rounded = Math.ceil(t / d) * d;
        if (rounded > total && !out.includes(rounded))
          out.push(rounded);
        if (out.length >= 6)
          break;
      }
      if (!out.includes(t))
        out.unshift(t);
      return out.slice(0, 6);
    }
    after_sale_actions(invoice_name, change) {
      frappe.confirm(
        __("Invoice {0} submitted successfully{1}. Print the receipt?", [invoice_name, change ? ` (change ${format_currency(change)})` : ""]),
        () => this.print_receipt(invoice_name),
        () => {
        }
      );
    }
    print_receipt(invoice_name) {
      ethiotel_print("POS Invoice", invoice_name, "Forkiva Sales Receipt");
    }
    print_invoice(invoice_name) {
      ethiotel_print("POS Invoice", invoice_name, "EIMS Invoice");
    }
    refresh() {
      this.load_products(this.$el.find(".etv2-sale-search input").val());
    }
    hide() {
    }
  };
  window.etv2_ph = function(name) {
    const $div = $(`<div class="fk-product-img-ph">${frappe.utils.escape_html(String(name || "?").slice(0, 1).toUpperCase())}</div>`);
    return $div[0].outerHTML;
  };
  window.etv2_ph_row = function(name) {
    const $div = $(`<div class="fk-row-img-ph">${frappe.utils.escape_html(String(name || "?").slice(0, 1).toUpperCase())}</div>`);
    return $div[0].outerHTML;
  };
  window.etv2_ph_big = function(name) {
    return `<div class="etv2-id-img-ph">${frappe.utils.escape_html(String(name || "?").slice(0, 1).toUpperCase())}</div>`;
  };

  // ../ethiotel_pos/ethiotel_pos/ethio_telecom_pos_app/page/ethiotel_pos/js/etv2_shift_dashboard.js
  erpnext.POSV2 = erpnext.POSV2 || {};
  erpnext.POSV2.ShiftDashboardWorkspace = class {
    constructor({ shell, workspace, container, name }) {
      this.shell = shell;
      this.workspace = workspace;
      this.container = container;
      this.name = name;
      this.render();
    }
    render() {
      this.$el = $(`
			<section class="etv2-ws">
				<div class="etv2-ws-toolbar">
					<h2 class="etv2-page-title">${__("Shift Dashboard")}</h2>
					<div class="etv2-dash-date-range"></div>
				</div>
				<div class="etv2-dash-content">
					<div class="etv2-dash-metrics etv2-dash-metrics"></div>
					<div class="etv2-dash-grid">
						<div class="etv2-card etv2-dash-chart-card">
							<div class="etv2-card-header"><span class="etv2-card-title">${__("Hourly Sales")}</span></div>
							<div class="etv2-card-body"><div class="etv2-hourly etv2-hourly"></div></div>
						</div>
						<div class="etv2-card">
							<div class="etv2-card-header"><span class="etv2-card-title">${__("Payment Methods")}</span></div>
							<div class="etv2-card-body"><div class="etv2-list etv2-payments"></div></div>
						</div>
						<div class="etv2-card">
							<div class="etv2-card-header"><span class="etv2-card-title">${__("Top Selling Items")}</span></div>
							<div class="etv2-card-body"><div class="etv2-list etv2-top-items"></div></div>
						</div>
						<div class="etv2-card">
							<div class="etv2-card-header"><span class="etv2-card-title">${__("Recent Activity")}</span></div>
							<div class="etv2-card-body"><div class="etv2-activity etv2-activity"></div></div>
						</div>
						<div class="etv2-card">
							<div class="etv2-card-header"><span class="etv2-card-title">${__("Cash Drawer")}</span></div>
							<div class="etv2-card-body"><div class="etv2-cash-drawer"></div></div>
						</div>
					</div>
				</div>
			</section>
		`);
      return this.$el;
    }
    show() {
      this.load();
    }
    refresh() {
      this.load();
    }
    load() {
      const pv = this.shell.get_pv();
      frappe.call({
        method: `${pv}.get_dashboard_data`,
        args: { pos_profile: this.shell.pos_profile }
      }).then((r) => {
        const d = r.message || {};
        this.render_metrics(d);
        this.render_hourly(d.hourly_sales || []);
        this.render_payments(d.payment_methods || []);
        this.render_top_items(d.top_items || []);
        this.render_activity(d.recent_activity || []);
        this.render_cash_drawer(d.cash_drawer || {});
      });
    }
    render_metrics(d) {
      const metrics = [
        { label: __("Sales Today"), value: format_currency(d.sales_today || 0), sub: d.from_date || frappe.datetime.now_date() },
        { label: __("Transactions"), value: String(d.transactions || 0), sub: __("Invoices today") },
        { label: __("Customers"), value: String(d.customers || 0), sub: __("Served today") },
        { label: __("Held Orders"), value: String(d.held_orders || 0), sub: __("Pending drafts") }
      ];
      this.$el.find(".etv2-dash-metrics").html(
        metrics.map((m) => `
				<div class="etv2-metric">
					<span class="etv2-metric-label">${m.label}</span>
					<span class="etv2-metric-value">${m.value}</span>
					<span class="etv2-metric-sub">${m.sub}</span>
				</div>`).join("")
      );
    }
    render_hourly(hourly) {
      const $chart = this.$el.find(".etv2-hourly");
      if (!hourly.length) {
        $chart.html(`<div class="etv2-empty">${__("No sales yet today.")}</div>`);
        return;
      }
      const max = Math.max(...hourly.map((h) => h.amount), 1);
      $chart.html(
        hourly.map((h) => `
				<div class="etv2-hourly-col">
					<div class="etv2-hourly-bar" style="height:${Math.max(h.amount / max * 100, 4)}%">
						<span class="etv2-hourly-val">${format_currency(h.amount, void 0, 0)}</span>
					</div>
					<span class="etv2-hourly-label">${h.hr}:00</span>
				</div>`).join("")
      );
    }
    render_payments(payments) {
      const $list = this.$el.find(".etv2-payments");
      if (!payments.length) {
        $list.html(`<div class="etv2-empty">${__("No payments today.")}</div>`);
        return;
      }
      const max = Math.max(...payments.map((p) => p.amount), 1);
      $list.html(
        payments.map((p) => `
				<div class="etv2-list-row">
					<span class="etv2-list-row-label">${frappe.utils.escape_html(p.mode_of_payment)}</span>
					<div class="etv2-list-bar-wrap">
						<div class="etv2-list-bar"><div class="etv2-list-bar-fill" style="width:${Math.max(p.amount / max * 100, 4)}%"></div></div>
					</div>
					<span class="etv2-list-row-amount">${format_currency(p.amount)}</span>
				</div>`).join("")
      );
    }
    render_top_items(items) {
      const $list = this.$el.find(".etv2-top-items");
      if (!items.length) {
        $list.html(`<div class="etv2-empty">${__("No items sold.")}</div>`);
        return;
      }
      $list.html(
        items.map((i, idx) => `
				<div class="etv2-list-row">
					<span class="etv2-list-row-label">${idx + 1}. ${frappe.utils.escape_html(i.item_name || i.item_code)}</span>
					<div class="etv2-list-bar-wrap">
						<div class="etv2-list-bar"><div class="etv2-list-bar-fill" style="width:${100 - idx * 8}%"></div></div>
					</div>
					<span class="etv2-list-row-amount">${flt(i.qty)} \xD7 ${format_currency(i.amount / (i.qty || 1), void 0, 0)}</span>
				</div>`).join("")
      );
    }
    render_activity(activity) {
      const $list = this.$el.find(".etv2-activity");
      if (!activity.length) {
        $list.html(`<div class="etv2-empty">${__("No recent activity.")}</div>`);
        return;
      }
      $list.html(
        activity.map((a) => `
				<div class="etv2-activity-row">
					<div class="etv2-activity-avatar">${frappe.utils.escape_html((a.customer_name || a.customer || "?").slice(0, 1).toUpperCase())}</div>
					<div class="etv2-activity-info">
						<div class="etv2-activity-title">${frappe.utils.escape_html(a.customer_name || a.customer || __("Choose Customer"))}</div>
						<div class="etv2-activity-sub">${frappe.utils.escape_html(a.name)} \xB7 ${a.posting_time || ""}</div>
					</div>
					<span class="etv2-activity-amount">${format_currency(a.grand_total)}</span>
				</div>`).join("")
      );
    }
    render_cash_drawer(d) {
      const $drawer = this.$el.find(".etv2-cash-drawer");
      $drawer.html(`
			<div class="etv2-list">
				<div class="etv2-list-row">
					<span class="etv2-list-row-label">${__("Opening")}</span>
					<span class="etv2-list-row-amount">${format_currency(d.opening_amount || 0)}</span>
				</div>
				<div class="etv2-list-row">
					<span class="etv2-list-row-label">${__("Cash in")}</span>
					<span class="etv2-list-row-amount">${format_currency(d.cash_in || 0)}</span>
				</div>
				<div class="etv2-list-row">
					<span class="etv2-list-row-label">${__("Expected")}</span>
					<span class="etv2-list-row-amount">${format_currency(d.expected || 0)}</span>
				</div>
			</div>
		`);
    }
  };

  // ../ethiotel_pos/ethiotel_pos/ethio_telecom_pos_app/page/ethiotel_pos/js/etv2_held_orders.js
  erpnext.POSV2 = erpnext.POSV2 || {};
  erpnext.POSV2.HeldOrdersWorkspace = class {
    constructor({ shell, workspace, container, name }) {
      this.shell = shell;
      this.workspace = workspace;
      this.container = container;
      this.name = name;
      this.render();
    }
    render() {
      this.$el = $(`
			<section class="etv2-ws">
				<div class="etv2-ws-toolbar">
					<h2 class="etv2-page-title">${__("Held Orders")}</h2>
					<div class="etv2-search etv2-held-search">
						<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
						<input type="text" placeholder="${__("Search held orders\u2026")}" />
					</div>
				</div>
				<div class="etv2-ws-content">
					<div class="etv2-orders-grid etv2-held-grid"></div>
				</div>
			</section>
		`);
      let searchTimer;
      this.$el.find(".etv2-held-search input").on("input", (e) => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => this.load($(e.currentTarget).val()), 250);
      });
      this.$el.on("click", ".etv2-resume-btn", (e) => this.resume($(e.currentTarget).attr("data-name")));
      this.$el.on("click", ".etv2-delete-btn", (e) => this.delete_order($(e.currentTarget).attr("data-name")));
      return this.$el;
    }
    show() {
      this.load();
    }
    refresh() {
      this.load();
    }
    load(search_term = "") {
      const pv = this.shell.get_pv();
      frappe.call({
        method: `${pv}.get_held_orders`,
        args: { search_term, limit: 50 }
      }).then((r) => {
        const rows = r.message || [];
        const $grid = this.$el.find(".etv2-held-grid");
        if (!rows.length) {
          $grid.html(`<div class="etv2-empty">${__("No held orders.")}</div>`);
          return;
        }
        $grid.html(
          rows.map((d) => `
					<div class="etv2-order-card">
						<div class="etv2-order-id">#${frappe.utils.escape_html(d.name)}</div>
						<div class="etv2-order-meta">
							<span>${frappe.utils.escape_html(d.customer_name || d.customer || __("Choose customer"))}</span>
							<span>${d.posting_date || ""} ${d.posting_time || ""}</span>
						</div>
						<div class="etv2-order-total">${format_currency(d.grand_total, d.currency)}</div>
						<div class="etv2-order-actions">
							<button class="etv2-btn etv2-btn-primary etv2-resume-btn" data-name="${frappe.utils.escape_html(d.name)}">${__("Resume")}</button>
							<button class="etv2-btn etv2-btn-danger etv2-delete-btn" data-name="${frappe.utils.escape_html(d.name)}">${__("Delete")}</button>
						</div>
					</div>`).join("")
        );
      });
    }
    resume(name) {
      const me = this;
      frappe.db.get_doc("POS Invoice", name).then((doc) => {
        const sale = this.shell.workspaces.instances["sale"];
        if (!sale)
          return;
        sale.customer = doc.customer;
        sale.$el.find(".etv2-sale-customer-btn").html(`${__("Customer")}: <b>${frappe.utils.escape_html(doc.customer_name || doc.customer)}</b>`);
        (doc.items || []).forEach((it) => {
          sale.cart[it.item_code] = {
            item_code: it.item_code,
            item_name: it.item_name || it.item_code,
            rate: it.rate,
            price_list_rate: it.price_list_rate || it.rate || 0,
            discount_percentage: it.discount_percentage || 0,
            uom: it.uom,
            conversion_factor: it.conversion_factor || 1,
            currency: doc.currency,
            qty: it.qty,
            warehouse: it.warehouse || me.shell.warehouse,
            actual_qty: it.actual_qty || 0,
            is_stock_item: it.is_stock_item,
            stock_uom: it.stock_uom
          };
        });
        sale.render_cart();
        frappe.show_alert({ message: __("Loaded held order into cart."), indicator: "blue" });
      });
    }
    delete_order(name) {
      const me = this;
      frappe.confirm(__("Delete held order {0}?", [name]), () => {
        const pv = this.shell.get_pv();
        frappe.call({ method: `${pv}.delete_draft`, args: { name } }).then((r) => {
          frappe.show_alert({ message: __("Deleted"), indicator: "green" });
          me.load(me.$el.find(".etv2-held-search input").val());
        });
      });
    }
  };

  // ../ethiotel_pos/ethiotel_pos/ethio_telecom_pos_app/page/ethiotel_pos/js/etv2_customers.js
  erpnext.POSV2 = erpnext.POSV2 || {};
  erpnext.POSV2.CustomerWorkspace = class {
    constructor({ shell, workspace, container, name }) {
      this.shell = shell;
      this.workspace = workspace;
      this.container = container;
      this.name = name;
      this.selected = null;
      this.render();
    }
    render() {
      this.$el = $(`
			<section class="etv2-ws">
				<div class="etv2-ws-toolbar">
					<h2 class="etv2-page-title">${__("Customers")}</h2>
					<div class="etv2-search etv2-customer-search">
						<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
						<input type="text" placeholder="${__("Search customers\u2026")}" />
					</div>
				</div>
				<div class="etv2-customer-body">
					<div class="etv2-customer-grid"></div>
					<aside class="etv2-card etv2-customer-panel">
						<div class="etv2-customer-panel-empty">
							<svg viewBox="0 0 24 24" width="40" height="40" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle></svg>
							<p>${__("Select a customer to see their profile.")}</p>
						</div>
					</aside>
				</div>
			</section>
		`);
      let searchTimer;
      this.$el.find(".etv2-customer-search input").on("input", (e) => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => this.load($(e.currentTarget).val()), 250);
      });
      this.$el.on("click", ".etv2-customer-card", (e) => this.select_customer($(e.currentTarget).attr("data-name")));
      return this.$el;
    }
    show() {
      this.load();
    }
    refresh() {
      this.load();
    }
    load(search_term = "") {
      const pv = this.shell.get_pv();
      frappe.call({
        method: `${pv}.get_customers`,
        args: { search_term, limit: 80 }
      }).then((r) => {
        const rows = r.message || [];
        const $grid = this.$el.find(".etv2-customer-grid");
        if (!rows.length) {
          $grid.html(`<div class="etv2-empty">${__("No customers found.")}</div>`);
          return;
        }
        $grid.html(
          rows.map((c) => `
					<div class="etv2-customer-card" data-name="${frappe.utils.escape_html(c.name)}">
						<div class="etv2-customer-avatar">
							${c.image ? `<img src="${c.image}" onerror="this.remove()" />` : frappe.utils.escape_html((c.customer_name || c.name).slice(0, 1).toUpperCase())}
						</div>
						<div class="etv2-customer-card-info">
							<div class="etv2-customer-card-name">${frappe.utils.escape_html(c.customer_name || c.name)}</div>
							<div class="etv2-customer-card-sub">${frappe.utils.escape_html(c.mobile_no || c.customer_group || "")}</div>
						</div>
					</div>`).join("")
        );
      });
    }
    select_customer(name) {
      this.selected = name;
      this.$el.find(".etv2-customer-card").removeClass("selected");
      this.$el.find(`.etv2-customer-card[data-name="${name}"]`).addClass("selected");
      const pv = this.shell.get_pv();
      frappe.call({
        method: `${pv}.get_customer_details`,
        args: { customer: name }
      }).then((r) => {
        this.render_panel(r.message || {});
      });
    }
    render_panel({ customer, transactions }) {
      const c = customer || {};
      const $panel = this.$el.find(".etv2-customer-panel");
      const txns = transactions || [];
      $panel.html(`
			<div class="etv2-cp-head">
				<div class="etv2-cp-avatar">
					${c.image ? `<img src="${c.image}" onerror="this.remove()" />` : frappe.utils.escape_html((c.customer_name || c.name || "?").slice(0, 1).toUpperCase())}
				</div>
				<div class="etv2-cp-name">${frappe.utils.escape_html(c.customer_name || c.name)}</div>
				<div class="etv2-cp-meta">${frappe.utils.escape_html(c.customer_group || "")} \xB7 ${frappe.utils.escape_html(c.territory || "")}</div>
			</div>
			<div class="etv2-cp-section">
				<div class="etv2-cp-field"><span class="etv2-cp-field-label">${__("Mobile")}</span><span class="etv2-cp-field-value">${frappe.utils.escape_html(c.mobile_no || "\u2014")}</span></div>
				<div class="etv2-cp-field"><span class="etv2-cp-field-label">${__("Email")}</span><span class="etv2-cp-field-value">${frappe.utils.escape_html(c.email_id || "\u2014")}</span></div>
				<div class="etv2-cp-field"><span class="etv2-cp-field-label">${__("Loyalty")}</span><span class="etv2-cp-field-value">${frappe.utils.escape_html(c.loyalty_program || "\u2014")}</span></div>
			</div>
			<div class="etv2-cp-section">
				<div class="etv2-cp-section-title">${__("Transactions")}</div>
				${txns.length ? txns.map((t) => `
					<div class="etv2-cp-txn">
						<div class="etv2-cp-txn-name">#${frappe.utils.escape_html(t.name)}<br/><span class="etv2-muted">${t.posting_date || ""} ${t.posting_time || ""}</span></div>
						<div class="etv2-cp-txn-amt">${format_currency(t.grand_total, t.currency)}</div>
					</div>`).join("") : `<div class="etv2-empty">${__("No transactions.")}</div>`}
			</div>
		`);
    }
  };

  // ../ethiotel_pos/ethiotel_pos/ethio_telecom_pos_app/page/ethiotel_pos/js/etv2_checkin.js
  erpnext.POSV2 = erpnext.POSV2 || {};
  erpnext.POSV2.CheckinWorkspace = class {
    constructor({ shell, workspace, container, name }) {
      this.shell = shell;
      this.workspace = workspace;
      this.container = container;
      this.name = name;
      this.render();
    }
    render() {
      this.$el = $(`
            <section class="etv2-ws etv2-checkin">
                <div class="etv2-ws-toolbar">
                    <h2 class="etv2-page-title">${__("Shift Management")}</h2>
                    <div class="etv2-checkin-status"></div>
                </div>
                <div class="etv2-checkin-body">
                    <!-- Dynamic Content Injected Here -->
                </div>
            </section>
        `);
      return this.$el;
    }
    show() {
      this.load();
    }
    refresh() {
      this.load();
    }
    load() {
      const shell = this.shell;
      const entry = shell.pos_opening;
      const $status = this.$el.find(".etv2-checkin-status");
      const $body = this.$el.find(".etv2-checkin-body");
      if (!entry) {
        $status.html(`<span class="etv2-pill etv2-pill-muted">${__("Offline")}</span>`);
        $body.html(`
                <div class="etv2-empty-state-wrapper">
                    <div class="etv2-empty-state">
                        <div class="etv2-empty-icon">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                                <line x1="3" y1="9" x2="21" y2="9"></line>
                                <line x1="9" y1="21" x2="9" y2="9"></line>
                            </svg>
                        </div>
                        <h3>${__("Ready to start selling?")}</h3>
                        <p class="etv2-text-muted">${__("You don't have an active shift. Open a new shift to start processing sales and managing the register.")}</p>
                        <button class="etv2-btn etv2-btn-primary etv2-btn-large etv2-checkin-open-btn">
                            ${__("Open New Shift")}
                        </button>
                    </div>
                </div>
            `);
        this.$el.find(".etv2-checkin-open-btn").on("click", () => this.shell.open_shift_dialog());
        return;
      }
      $status.html(`<span class="etv2-pill etv2-pill-green"><span class="etv2-indicator-dot blink"></span>${__("Active Shift")} \xB7 ${frappe.datetime.str_to_user(shell.pos_opening_time)}</span>`);
      $body.html(`
            <div class="etv2-checkin-grid">
                <!-- Left Column: Shift Info -->
                <div class="etv2-card etv2-shift-info-card">
                    <div class="etv2-card-header"><span class="etv2-card-title">${__("Current Shift Details")}</span></div>
                    <div class="etv2-card-body etv2-checkin-shift">
                        <div class="etv2-info-group">
                            <label>${__("Opening Entry")}</label>
                            <div class="etv2-info-value">${frappe.utils.escape_html(entry)}</div>
                        </div>
                        <div class="etv2-info-group">
                            <label>${__("POS Profile")}</label>
                            <div class="etv2-info-value">${frappe.utils.escape_html(shell.pos_profile)}</div>
                        </div>
                        <div class="etv2-info-group">
                            <label>${__("Company")}</label>
                            <div class="etv2-info-value">${frappe.utils.escape_html(shell.company)}</div>
                        </div>
                        <div class="etv2-info-group">
                            <label>${__("Opened At")}</label>
                            <div class="etv2-info-value">${frappe.datetime.str_to_user(shell.pos_opening_time)}</div>
                        </div>
                    </div>
                </div>

                <!-- Right Column: Summary & Actions -->
                <div class="etv2-card etv2-shift-summary-card">
                    <div class="etv2-card-header"><span class="etv2-card-title">${__("Live Shift Summary")}</span></div>
                    <div class="etv2-card-body etv2-checkin-summary">
                        <div class="etv2-loading-shimmer">Loading summary...</div>
                    </div>
                </div>
            </div>
        `);
      const $summary = this.$el.find(".etv2-checkin-summary");
      const pv = shell.get_pv();
      frappe.call({
        method: `${pv}.get_shift_summary`,
        args: { pos_opening: entry }
      }).then((r) => {
        const d = r.message || {};
        $summary.html(`
                <!-- High-level Metrics -->
                <div class="etv2-metrics-grid">
                    <div class="etv2-metric-box metric-highlight">
                        <span class="etv2-metric-label">${__("Total Sales")}</span>
                        <span class="etv2-metric-value">${format_currency(d.sales_total || 0)}</span>
                    </div>
                    <div class="etv2-metric-box">
                        <span class="etv2-metric-label">${__("Invoices")}</span>
                        <span class="etv2-metric-value">${d.invoice_count || 0}</span>
                    </div>
                    <div class="etv2-metric-box">
                        <span class="etv2-metric-label">${__("Customers")}</span>
                        <span class="etv2-metric-value">${d.customer_count || 0}</span>
                    </div>
                </div>

                <div class="etv2-summary-sections">
                    <!-- Payments Received -->
                    <div class="etv2-summary-section">
                        <div class="etv2-section-title">${__("Payments Received")}</div>
                        <div class="etv2-breakdown-list">
                            ${(d.payments || []).length ? d.payments.map((p) => `
                                <div class="etv2-breakdown-row">
                                    <span class="etv2-breakdown-label">${frappe.utils.escape_html(p.mode_of_payment)}</span>
                                    <span class="etv2-breakdown-amount">${format_currency(p.amount)}</span>
                                </div>`).join("") : `<div class="etv2-empty-text">${__("No payments recorded yet.")}</div>`}
                        </div>
                    </div>

                    <!-- Opening Balance -->
                    <div class="etv2-summary-section">
                        <div class="etv2-section-title">${__("Opening Balance")}</div>
                        <div class="etv2-breakdown-list">
                            ${Object.keys(d.opening_balance || {}).length ? Object.keys(d.opening_balance).map((m) => `
                                <div class="etv2-breakdown-row">
                                    <span class="etv2-breakdown-label">${frappe.utils.escape_html(m)}</span>
                                    <span class="etv2-breakdown-amount">${format_currency(d.opening_balance[m])}</span>
                                </div>`).join("") : `<div class="etv2-empty-text">${__("No opening balance.")}</div>`}
                        </div>
                    </div>
                </div>

            `);
      });
    }
  };

  // ../ethiotel_pos/ethiotel_pos/ethio_telecom_pos_app/page/ethiotel_pos/js/etv2_returns.js
  erpnext.POSV2 = erpnext.POSV2 || {};
  erpnext.POSV2.ReturnsWorkspace = class {
    constructor({ shell, workspace, container, name }) {
      this.shell = shell;
      this.workspace = workspace;
      this.container = container;
      this.name = name;
      this.render();
    }
    render() {
      this.$el = $(`
			<section class="etv2-ws">
				<div class="etv2-ws-toolbar">
					<h2 class="etv2-page-title">${__("Returns")}</h2>
					<div class="etv2-search etv2-returns-search">
						<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
						<input type="text" placeholder="${__("Search invoices\u2026")}" />
					</div>
				</div>
				<div class="etv2-ws-content">
					<div class="etv2-orders-grid etv2-returns-grid"></div>
				</div>
			</section>
		`);
      let searchTimer;
      this.$el.find(".etv2-returns-search input").on("input", (e) => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => this.load($(e.currentTarget).val()), 250);
      });
      this.$el.on("click", ".etv2-return-btn", (e) => this.make_return($(e.currentTarget).attr("data-name")));
      return this.$el;
    }
    show() {
      this.load();
    }
    refresh() {
      this.load();
    }
    load(search_term = "") {
      const pv = this.shell.get_pv();
      frappe.call({
        method: `${pv}.get_invoices`,
        args: { search_term, status: "", limit: 50 }
      }).then((r) => {
        const rows = r.message || [];
        const $grid = this.$el.find(".etv2-returns-grid");
        if (!rows.length) {
          $grid.html(`<div class="etv2-empty">${__("No invoices found.")}</div>`);
          return;
        }
        $grid.html(
          rows.map((d) => `
					<div class="etv2-order-card">
						<div class="etv2-order-id">#${frappe.utils.escape_html(d.name)}</div>
						<div class="etv2-order-meta">
							<span>${frappe.utils.escape_html(d.customer_name || d.customer || __("Choose customer"))}</span>
							<span>${d.posting_date || ""} ${d.posting_time || ""}</span>
						</div>
						<div class="etv2-order-total">${format_currency(d.grand_total, d.currency)}</div>
						<div class="etv2-order-actions">
							<button class="etv2-btn etv2-btn-primary etv2-return-btn" data-name="${frappe.utils.escape_html(d.name)}">${__("Return")}</button>
						</div>
					</div>`).join("")
        );
      });
    }
    make_return(name) {
      frappe.set_route("Form", "POS Invoice", name);
      frappe.after_ajax(() => {
        const cur_frm = frappe.model.get_doc("POS Invoice", name).__onload;
        frappe.show_alert({ message: __("Open the invoice and use Return in the document action menu."), indicator: "blue" });
      });
    }
  };

  // ../ethiotel_pos/ethiotel_pos/ethio_telecom_pos_app/page/ethiotel_pos/js/etv2_reports.js
  erpnext.POSV2 = erpnext.POSV2 || {};
  erpnext.POSV2.ReportsWorkspace = class {
    constructor({ shell, workspace, container, name }) {
      this.shell = shell;
      this.workspace = workspace;
      this.container = container;
      this.name = name;
      this.render();
    }
    render() {
      this.$el = $(`
			<section class="etv2-ws">
				<div class="etv2-ws-toolbar">
					<h2 class="etv2-page-title">${__("Reports")}</h2>
					<div class="etv2-report-tabs">
						<button class="etv2-report-tab active" data-tab="sales">${__("Sales")}</button>
						<button class="etv2-report-tab" data-tab="x">${__("X Report")}</button>
						<button class="etv2-report-tab" data-tab="z">${__("Z Report")}</button>
					</div>
					<div class="etv2-report-filters etv2-report-filters-sales">
						<div class="etv2-date-field etv2-report-from"></div>
						<div class="etv2-date-field etv2-report-to"></div>
						<button class="etv2-btn etv2-btn-primary etv2-report-run">${__("Run")}</button>
					</div>
					<div class="etv2-report-filters etv2-report-filters-z" style="display:none;">
						<div class="etv2-date-field etv2-z-from"></div>
						<div class="etv2-date-field etv2-z-to"></div>
						<button class="etv2-btn etv2-btn-primary etv2-z-run">${__("Run")}</button>
					</div>
					<button class="etv2-btn etv2-btn-primary etv2-x-run etv2-report-filters-x">${__("Run X Report")}</button>
					<button class="etv2-btn etv2-inv-print-report">${__("Print")}</button>
				</div>
				<div class="etv2-ws-content etv2-report-body" style="flex-direction:column;">
					<div class="etv2-report-stats etv2-report-stats"></div>
					<div class="etv2-report-detail"></div>
				</div>
			</section>
		`);
      this.from_field = frappe.ui.form.make_control({
        df: { label: __("From"), fieldtype: "Date", default: frappe.datetime.month_start() },
        parent: this.$el.find(".etv2-report-from"),
        render_input: true
      });
      this.to_field = frappe.ui.form.make_control({
        df: { label: __("To"), fieldtype: "Date", default: frappe.datetime.now_date() },
        parent: this.$el.find(".etv2-report-to"),
        render_input: true
      });
      this.z_from_field = frappe.ui.form.make_control({
        df: { label: __("From"), fieldtype: "Date", default: frappe.datetime.now_date() },
        parent: this.$el.find(".etv2-z-from"),
        render_input: true
      });
      this.z_to_field = frappe.ui.form.make_control({
        df: { label: __("To"), fieldtype: "Date", default: frappe.datetime.now_date() },
        parent: this.$el.find(".etv2-z-to"),
        render_input: true
      });
      this.$el.find(".etv2-report-tab").on("click", (e) => {
        const tab = $(e.currentTarget).attr("data-tab");
        this.$el.find(".etv2-report-tab").removeClass("active");
        $(e.currentTarget).addClass("active");
        this.$el.find(".etv2-report-filters-sales").toggle(tab === "sales");
        this.$el.find(".etv2-report-filters-z").toggle(tab === "z");
        this.$el.find(".etv2-report-filters-x").toggle(tab === "x");
        this.active_tab = tab;
        if (tab === "x")
          this.run_x_report();
        else if (tab === "z")
          this.run_z_report();
        else
          this.run_report();
      });
      this.$el.find(".etv2-report-run").on("click", () => this.run_report());
      this.$el.find(".etv2-z-run").on("click", () => this.run_z_report());
      this.$el.find(".etv2-x-run").on("click", () => this.run_x_report());
      this.$el.find(".etv2-inv-print-report").on("click", () => {
        const content = this.$el.find(".etv2-report-body").clone();
        this.print_report(content);
      });
      this.active_tab = "sales";
      return this.$el;
    }
    show() {
      if (this.active_tab === "x")
        this.run_x_report();
      else if (this.active_tab === "z")
        this.run_z_report();
      else
        this.run_report();
    }
    refresh() {
      this.show();
    }
    print_report($content) {
      const $print = $("<div class='etv2-print-window'></div>");
      $print.append($content.html());
      $(document.body).append($print);
      $print.attr("data-print", "1");
      const win = window.open("", "_blank", "width=900,height=720,menubar=no,toolbar=no,location=no,status=no,resizable=yes,scrollbars=yes");
      if (!win)
        return frappe.msgprint(__("Popup blocked \u2014 allow popups to print."));
      win.document.write(`
			<html><head><title>${__("Report")}</title>
			<link href="/assets/ethiotel_pos/css/ui/ethiotel_pos_tokens.css" rel="stylesheet">
			<link href="/assets/ethiotel_pos/css/ui/ethiotel_pos_primitives.css" rel="stylesheet">
			<link href="/assets/ethiotel_pos/css/ui/ethiotel_pos_reports.css" rel="stylesheet">
			<style>
				body { padding: 20px; font-family: 'Cairo', Arial, sans-serif; }
				.etv2-report-body { display: flex; flex-direction: column; gap: 16px; }
				.etv2-report-stats { display: flex; gap: 12px; }
				.etv2-metric { background: #f1f5f9; border-radius: 10px; padding: 14px; min-width: 140px; }
				.etv2-metric-label { display: block; font-size: 11px; color: #64748b; }
				.etv2-metric-value { display: block; font-size: 20px; font-weight: 800; }
				.etv2-metric-sub { font-size: 11px; color: #94a3b8; }
				.etv2-report-table { width: 100%; border-collapse: collapse; font-size: 12px; }
				.etv2-report-table th, .etv2-report-table td { border: 1px solid #e2e8f0; padding: 6px 8px; text-align: left; }
				.etv2-report-table th { background: #0f172a; color: #fff; }
				table { border-collapse: collapse; width: 100%; }
			</style></head>
			<body>${$content.html()}</body></html>
		`);
      win.document.close();
      win.focus();
      setTimeout(() => win.print(), 400);
      $print.remove();
    }
    run_report() {
      const pv = this.shell.get_pv();
      frappe.call({
        method: `${pv}.get_sales_report`,
        args: {
          from_date: this.from_field && this.from_field.get_value() || frappe.datetime.month_start(),
          to_date: this.to_field && this.to_field.get_value() || frappe.datetime.now_date(),
          pos_profile: this.shell.pos_profile
        },
        freeze: true
      }).then((r) => {
        const d = r.message || {};
        this.$el.find(".etv2-report-stats").html(`
				<div class="etv2-metric"><span class="etv2-metric-label">${__("Total Sales")}</span><span class="etv2-metric-value">${format_currency(d.total_sales || 0)}</span><span class="etv2-metric-sub">${d.from_date || ""} \u2192 ${d.to_date || ""}</span></div>
				<div class="etv2-metric"><span class="etv2-metric-label">${__("Invoices")}</span><span class="etv2-metric-value">${d.invoice_count || 0}</span><span class="etv2-metric-sub">${__("Submitted")}</span></div>
				<div class="etv2-metric"><span class="etv2-metric-label">${__("Avg. Sale")}</span><span class="etv2-metric-value">${format_currency(d.avg_sale || 0)}</span><span class="etv2-metric-sub">${__("Per invoice")}</span></div>
			`);
        const rows = d.by_payment_mode || [];
        this.$el.find(".etv2-report-detail").html(`
				<div class="etv2-card">
					<div class="etv2-card-header"><span class="etv2-card-title">${__("By Payment Mode")}</span></div>
					<div class="etv2-card-body">${rows.length ? `<table class="etv2-report-table">
								<thead><tr><th>${__("Mode of Payment")}</th><th>${__("Amount")}</th><th>${__("Share")}</th></tr></thead>
								<tbody>${rows.map((r2) => `
									<tr>
										<td>${frappe.utils.escape_html(r2.mode_of_payment)}</td>
										<td>${format_currency(r2.amount)}</td>
										<td>${d.total_sales ? (r2.amount / d.total_sales * 100).toFixed(1) : 0}%</td>
									</tr>`).join("")}
								</tbody>
							</table>` : `<div class="etv2-empty">${__("No data for this period.")}</div>`}</div>
				</div>
			`);
      });
    }
    run_x_report() {
      const pv = this.shell.get_pv();
      frappe.call({
        method: `${pv}.get_x_report`,
        args: { pos_opening: this.shell.pos_opening, pos_profile: this.shell.pos_profile },
        freeze: true
      }).then((r) => this.render_xz(r.message || {}));
    }
    run_z_report() {
      const pv = this.shell.get_pv();
      frappe.call({
        method: `${pv}.get_z_report`,
        args: {
          from_date: this.z_from_field && this.z_from_field.get_value() || frappe.datetime.now_date(),
          to_date: this.z_to_field && this.z_to_field.get_value() || frappe.datetime.now_date(),
          pos_profile: this.shell.pos_profile
        },
        freeze: true
      }).then((r) => this.render_xz(r.message || {}));
    }
    render_xz(d) {
      const period = d.report_type === "X" ? `${__("Shift from")} ${d.period_start ? frappe.datetime.str_to_user(d.period_start) : "\u2014"}` : `${d.from_date || ""} \u2192 ${d.to_date || ""}`;
      this.$el.find(".etv2-report-stats").html(`
			<div class="etv2-metric"><span class="etv2-metric-label">${d.report_type === "X" ? __("X Report \u2014 Total") : __("Z Report \u2014 Total")}</span><span class="etv2-metric-value">${format_currency(d.grand_total || 0)}</span><span class="etv2-metric-sub">${period}</span></div>
			<div class="etv2-metric"><span class="etv2-metric-label">${__("Invoices")}</span><span class="etv2-metric-value">${d.invoice_count || 0}</span><span class="etv2-metric-sub">${__("Submitted")}</span></div>
			<div class="etv2-metric"><span class="etv2-metric-label">${__("Items Sold")}</span><span class="etv2-metric-value">${d.item_count || 0}</span><span class="etv2-metric-sub">${__("Total qty")}</span></div>
			<div class="etv2-metric"><span class="etv2-metric-label">${__("Net / Tax")}</span><span class="etv2-metric-value">${format_currency(d.net_total || 0)} / ${format_currency(d.tax_total || 0)}</span><span class="etv2-metric-sub">${__("Discounts: {0}", [format_currency(d.discount_total || 0)])}</span></div>
		`);
      const payments = (d.payments || []).map((p) => `<tr><td>${frappe.utils.escape_html(p.mode_of_payment)}</td><td>${format_currency(p.amount)}</td><td>${d.grand_total ? (p.amount / d.grand_total * 100).toFixed(1) : 0}%</td></tr>`).join("");
      const taxes = (d.taxes || []).map((t) => `<tr><td>${frappe.utils.escape_html(t.account_head)}</td><td>${t.rate}%</td><td>${format_currency(t.amount)}</td></tr>`).join("");
      const items = (d.items || []).slice(0, 100).map((i) => `<tr><td>${frappe.utils.escape_html(i.item_name || i.item_code)}</td><td>${flt(i.qty)}</td><td>${format_currency(i.amount)}</td></tr>`).join("");
      this.$el.find(".etv2-report-detail").html(`
			<div class="etv2-report-grid">
				<div class="etv2-card">
					<div class="etv2-card-header"><span class="etv2-card-title">${__("Payment Modes")}</span></div>
					<div class="etv2-card-body">${payments ? `<table class="etv2-report-table"><thead><tr><th>${__("Mode")}</th><th>${__("Amount")}</th><th>${__("Share")}</th></tr></thead><tbody>${payments}</tbody></table>` : `<div class="etv2-empty">${__("No payments")}</div>`}</div>
				</div>
				<div class="etv2-card">
					<div class="etv2-card-header"><span class="etv2-card-title">${__("Tax Summary")}</span></div>
					<div class="etv2-card-body">${taxes ? `<table class="etv2-report-table"><thead><tr><th>${__("Tax")}</th><th>${__("Rate")}</th><th>${__("Amount")}</th></tr></thead><tbody>${taxes}</tbody></table>` : `<div class="etv2-empty">${__("No taxes")}</div>`}</div>
				</div>
				<div class="etv2-card etv2-report-items-card">
					<div class="etv2-card-header"><span class="etv2-card-title">${__("Item Summary")}</span></div>
					<div class="etv2-card-body">${items ? `<table class="etv2-report-table"><thead><tr><th>${__("Item")}</th><th>${__("Qty")}</th><th>${__("Amount")}</th></tr></thead><tbody>${items}</tbody></table>` : `<div class="etv2-empty">${__("No items")}</div>`}</div>
				</div>
				<div class="etv2-card">
					<div class="etv2-card-header"><span class="etv2-card-title">${__("Invoice Detail")}</span></div>
					<div class="etv2-card-body etv2-report-inv-list">${(d.invoices || []).map((i) => `
								<div class="etv2-report-inv-row">
									<span><b>${frappe.utils.escape_html(i.name)}</b> \xB7 ${frappe.utils.escape_html(i.customer_name || i.customer || "")}</span>
									<span>${frappe.datetime.str_to_user(`${i.posting_date} ${i.posting_time || ""}`)}</span>
									<span>${format_currency(i.grand_total)}</span>
								</div>`).join("") || `<div class="etv2-empty">${__("No invoices")}</div>`}</div>
				</div>
			</div>
		`);
    }
    hide() {
    }
  };

  // ../ethiotel_pos/ethiotel_pos/ethio_telecom_pos_app/page/ethiotel_pos/js/etv2_mor.js
  erpnext.POSV2 = erpnext.POSV2 || {};
  var MOR_WALK_IN = "Walk-In Customer";
  erpnext.POSV2.MoRWorkspace = class {
    constructor({ shell, workspace, container, name }) {
      this.shell = shell;
      this.workspace = workspace;
      this.container = container;
      this.name = name;
      this.invoices = [];
      this.stats = {};
      this.render();
      this.load();
    }
    render() {
      this.$el = $(`
			<section class="etv2-ws">
				<div class="etv2-ws-toolbar">
					<h2 class="etv2-page-title">${__("MoR Invoices")}</h2>
					<select class="etv2-mor-filter etv2-input">
						<option value="All">${__("All Statuses")}</option>
						<option value="Not Submitted">${__("Not Submitted")}</option>
						<option value="Pending">${__("Pending")}</option>
						<option value="Failed">${__("Failed")}</option>
						<option value="Registered">${__("Registered")}</option>
						<option value="Cancelled">${__("Cancelled")}</option>
					</select>
					<input type="text" class="etv2-mor-search etv2-input" placeholder="${__("Search invoice / customer...")}">
					<button class="etv2-btn etv2-btn-primary etv2-mor-refresh">${__("Refresh")}</button>
				</div>
				<div class="etv2-ws-content etv2-mor-body">
					<div class="etv2-mor-stats"></div>
					<div class="etv2-mor-list"></div>
				</div>
			</section>
		`);
      this.$stats = this.$el.find(".etv2-mor-stats");
      this.$list = this.$el.find(".etv2-mor-list");
      this.$filter = this.$el.find(".etv2-mor-filter");
      this.$search = this.$el.find(".etv2-mor-search");
      this.$el.find(".etv2-mor-refresh").on("click", () => this.load());
      this.$filter.on("change", () => this.load());
      let search_timer = null;
      this.$search.on("input", () => {
        clearTimeout(search_timer);
        search_timer = setTimeout(() => this.load(), 300);
      });
    }
    load() {
      frappe.call({
        method: "ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos.get_mor_invoices",
        args: {
          status: this.$filter.val() || "All",
          search_term: (this.$search.val() || "").trim(),
          limit: 200
        },
        callback: (r) => {
          const res = r.message || {};
          this.invoices = res.invoices || (Array.isArray(res) ? res : []);
          this.stats = res.stats || {};
          this.render_stats();
          this.render_list();
        }
      });
    }
    render_stats() {
      const cards = [
        { key: "Registered", label: __("Registered"), cls: "green" },
        { key: "Pending", label: __("Pending"), cls: "orange" },
        { key: "Failed", label: __("Failed"), cls: "red" },
        { key: "Cancelled", label: __("Cancelled"), cls: "gray" }
      ];
      this.$stats.html(
        cards.map((c) => `
				<div class="etv2-mor-stat-card is-${c.cls}" data-status="${c.key}">
					<div class="etv2-mor-stat-num">${this.stats[c.key] || 0}</div>
					<div class="etv2-mor-stat-label">${c.label}</div>
				</div>`).join("")
      );
      this.$stats.find(".etv2-mor-stat-card").on("click", (e) => {
        this.$filter.val($(e.currentTarget).data("status"));
        this.load();
      });
    }
    status_badge(status) {
      const map = {
        "Not Submitted": "gray",
        "Pending": "orange",
        "Failed": "red",
        "Registered": "green",
        "Transmitted": "blue",
        "Cancelled": "red"
      };
      const color = map[status] || "gray";
      return `<span class="indicator ${color}">${__(status || "Not Submitted")}</span>`;
    }
    render_list() {
      const invoices = this.invoices || [];
      if (!invoices.length) {
        this.$list.html(`<div class="etv2-empty">${__("No invoices found.")}</div>`);
        return;
      }
      const rows = invoices.map((inv) => {
        const status = (inv.eims_status || "Not Submitted").trim();
        const is_walk_in = inv.customer === MOR_WALK_IN;
        const customer_html = is_walk_in ? `<span class="etv2-text-muted">${__("Walk-In Customer")}</span>` : frappe.utils.escape_html(inv.customer_name || inv.customer || "");
        const irn = inv.mor_irn || "";
        const actions = [];
        if (status === "Registered" || status === "Transmitted") {
          actions.push(`<button class="etv2-btn etv2-btn-primary etv2-mor-light" data-invoice="${inv.name}" title="${__("Compact receipt for walk-in customers")}">${__("Light Receipt")}</button>`);
          if (!is_walk_in) {
            actions.push(`<button class="etv2-btn etv2-mor-detailed" data-invoice="${inv.name}" title="${__("Detailed EIMS receipt \u2014 issued only on request")}">${__("Detailed Receipt")}</button>`);
          }
          actions.push(`<button class="etv2-btn etv2-mor-verify" data-invoice="${inv.name}">${__("Verify")}</button>`);
          actions.push(`<button class="etv2-btn etv2-btn-danger etv2-mor-cancel" data-invoice="${inv.name}">${__("Cancel")}</button>`);
        } else if (status !== "Cancelled") {
          actions.push(`<button class="etv2-btn etv2-btn-primary etv2-mor-resend" data-invoice="${inv.name}">${__("Resend")}</button>`);
        }
        actions.push(`<button class="etv2-btn etv2-mor-details" data-invoice="${inv.name}">${__("Details")}</button>`);
        return `
				<tr>
					<td><b>${inv.name}</b><br /><small class="etv2-text-muted">#${inv.custom_document_number || "\u2014"}</small></td>
					<td>${frappe.datetime.str_to_user ? frappe.datetime.str_to_user(inv.posting_date) : inv.posting_date}</td>
					<td>${customer_html}</td>
					<td class="etv2-mor-amount">${format_currency(inv.grand_total, inv.currency)}</td>
					<td>${this.status_badge(status)}</td>
					<td class="etv2-mor-irn" title="${frappe.utils.escape_html(irn)}">${irn ? irn.slice(0, 18) + (irn.length > 18 ? "\u2026" : "") : "\u2014"}</td>
					<td class="etv2-mor-actions">${actions.join("")}</td>
				</tr>`;
      }).join("");
      this.$list.html(`
			<table class="etv2-mor-table">
				<thead>
					<tr>
						<th>${__("Invoice")}</th>
						<th>${__("Date")}</th>
						<th>${__("Customer")}</th>
						<th>${__("Total")}</th>
						<th>${__("MoR Status")}</th>
						<th>${__("IRN")}</th>
						<th>${__("Actions")}</th>
					</tr>
				</thead>
				<tbody>${rows}</tbody>
			</table>
		`);
      this.$list.find(".etv2-mor-resend").on("click", (e) => this.resend($(e.currentTarget).data("invoice")));
      this.$list.find(".etv2-mor-light").on("click", (e) => this.light_receipt($(e.currentTarget).data("invoice")));
      this.$list.find(".etv2-mor-detailed").on("click", (e) => this.detailed_receipt($(e.currentTarget).data("invoice")));
      this.$list.find(".etv2-mor-verify").on("click", (e) => this.verify($(e.currentTarget).data("invoice")));
      this.$list.find(".etv2-mor-cancel").on("click", (e) => this.cancel($(e.currentTarget).data("invoice")));
      this.$list.find(".etv2-mor-details").on("click", (e) => this.details($(e.currentTarget).data("invoice")));
    }
    show_loading() {
      this.$list.html(`<div class="etv2-empty"><div class="etv2-spinner"></div><p>${__("Loading...")}</p></div>`);
    }
    resend(invoice) {
      frappe.call({
        method: "ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos.register_with_mor",
        args: { pos_invoice_name: invoice },
        freeze: true,
        freeze_message: __("Submitting to MoR..."),
        callback: (r) => {
          const res = r.message || {};
          if (res.status === "ok") {
            const result = res.result || {};
            const msg = result.message || __("Submitted to MoR.");
            const irn = res.irn || result.irn;
            frappe.show_alert({
              message: irn ? `${msg} \u2014 IRN: ${irn}` : msg,
              indicator: "green"
            });
          } else {
            frappe.msgprint(res.message || __("Submission failed."));
          }
          this.load();
        }
      });
    }
    light_receipt(invoice) {
      frappe.call({
        method: "ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos.get_light_receipt",
        args: { pos_invoice_name: invoice },
        callback: (r) => {
          const res = r.message || {};
          if (res.status !== "ok" || !res.html) {
            frappe.msgprint(res.message || __("Receipt generation failed."));
            return;
          }
          if (!res.registered) {
            frappe.show_alert({
              message: __("MoR registration still in progress \u2014 QR code is provisional."),
              indicator: "orange"
            });
          }
          this.show_print_dialog(__("Sales Receipt"), res.html, "small");
        }
      });
    }
    detailed_receipt(invoice) {
      frappe.confirm(
        __("Issue a detailed MoR receipt for {0}? This sends the receipt to MoR immediately.", [invoice]),
        () => {
          frappe.call({
            method: "ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos.get_pos_receipt",
            args: { pos_invoice_name: invoice },
            freeze: true,
            freeze_message: __("Generating detailed MoR receipt..."),
            callback: (r) => {
              const res = r.message || {};
              const html = res.status === "ok" && res.result && res.result.html || res.status === "ok" && res.already_active && res.html;
              if (html) {
                this.show_print_dialog(__("Detailed MoR Receipt"), html, "large");
              } else {
                frappe.msgprint(res.result && res.result.message || res.message || __("Receipt generation failed."));
              }
              this.load();
            }
          });
        }
      );
    }
    verify(invoice) {
      frappe.call({
        method: "ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos.verify_mor_pos_invoice",
        args: { pos_invoice_name: invoice },
        freeze: true,
        freeze_message: __("Verifying with MoR..."),
        callback: (r) => {
          const res = r.message || {};
          const result = res.result || {};
          const html = result.verification_summary || result.html;
          if (res.status === "ok" && html) {
            this.show_dialog(__("MoR Verification Result"), html);
          } else if (res.status === "ok" && result.verification_status) {
            frappe.show_alert({
              message: __(result.verification_status),
              indicator: result.verification_status === "Verified" ? "green" : "red"
            });
          } else {
            frappe.msgprint(result.error_logs || res.message || __("Verification failed."));
          }
        }
      });
    }
    details(invoice) {
      frappe.call({
        method: "frappe.client.get",
        args: { doctype: "POS Invoice", name: invoice },
        callback: (r) => {
          const d = r.message || {};
          if (!d.name) {
            frappe.msgprint(__("Unable to load invoice details."));
            return;
          }
          const irn = d.custom_irn || d.custom_mor_irn || "";
          const is_walk_in = d.customer === MOR_WALK_IN;
          const status = (d.custom_eims_status || "Not Submitted").trim();
          const items = (d.items || []).map((it) => `
					<tr>
						<td class="etv2-mor-item-code" data-label="${__("Code")}">${frappe.utils.escape_html(it.item_code)}</td>
						<td data-label="${__("Item")}">${frappe.utils.escape_html(it.item_name || "")}</td>
						<td class="etv2-right etv2-mor-num" data-label="${__("Qty")}">${it.qty} ${frappe.utils.escape_html(it.uom || "")}</td>
						<td class="etv2-right etv2-mor-num" data-label="${__("Rate")}">${format_currency(it.rate, d.currency)}</td>
						<td class="etv2-right etv2-mor-num etv2-mor-amt" data-label="${__("Amount")}">${format_currency(it.amount, d.currency)}</td>
					</tr>`).join("");
          const taxes = (d.taxes || []).map((t) => `
					<tr>
						<td colspan="2" data-label="${__("Tax")}">${frappe.utils.escape_html(t.description || t.account_head || "")}</td>
						<td class="etv2-right etv2-mor-num" data-label="${__("Rate")}">${t.rate}%</td>
						<td class="etv2-right etv2-mor-num etv2-mor-amt" data-label="${__("Amount")}">${format_currency(t.tax_amount, d.currency)}</td>
					</tr>`).join("");
          const html = `
					<div class="etv2-mor-detail">
						<div class="etv2-mor-dx-head">
							<div class="etv2-mor-dx-title">
								<span class="etv2-mor-dx-name">${frappe.utils.escape_html(d.name)}</span>
								${this.status_badge(status)}
							</div>
							<div class="etv2-mor-dx-meta">
								<span>${__("Doc #")}: <b>#${d.custom_document_number || "\u2014"}</b></span>
								<span>${frappe.datetime.str_to_user(d.posting_date)} ${d.posting_time || ""}</span>
							</div>
						</div>

						<div class="etv2-mor-dx-grid">
							<div class="etv2-mor-dx-cell"><label>${__("Customer")}</label><span>${is_walk_in ? `<i class="etv2-text-muted">${__("Walk-In Customer")}</i>` : frappe.utils.escape_html(d.customer_name || d.customer || "")}</span></div>
							<div class="etv2-mor-dx-cell"><label>${__("Cashier")}</label><span>${frappe.utils.escape_html(d.owner || "")}</span></div>
							<div class="etv2-mor-dx-cell"><label>${__("Price List")}</label><span>${frappe.utils.escape_html(d.selling_price_list || "\u2014")}</span></div>
							<div class="etv2-mor-dx-cell"><label>${__("Tax Template")}</label><span>${frappe.utils.escape_html(d.taxes_and_charges || "\u2014")}</span></div>
							<div class="etv2-mor-dx-cell etv2-mor-dx-irn">
								<label>${__("IRN")}</label>
								<span title="${frappe.utils.escape_html(irn)}">${irn ? irn.slice(0, 22) + (irn.length > 22 ? "\u2026" : "") : "\u2014"}</span>
								${irn ? `<button type="button" class="etv2-btn etv2-mor-copy-irn" data-irn="${frappe.utils.escape_html(irn)}">${__("Copy")}</button>` : ""}
							</div>
						</div>

						<div class="etv2-mor-dx-section">
							<h4>${__("Items")} <span class="etv2-mor-dx-count">${(d.items || []).length}</span></h4>
							<table class="etv2-mor-table etv2-mor-detail-table">
								<thead><tr><th>${__("Code")}</th><th>${__("Item")}</th><th class="etv2-right">${__("Qty")}</th><th class="etv2-right">${__("Rate")}</th><th class="etv2-right">${__("Amount")}</th></tr></thead>
								<tbody>${items || `<tr><td colspan="5" class="etv2-text-muted">${__("No items")}</td></tr>`}</tbody>
							</table>
						</div>

						<details class="etv2-mor-dx-taxes"${taxes ? "" : " hidden"}>
							<summary>${__("Taxes")} <span class="etv2-mor-dx-count">${(d.taxes || []).length}</span></summary>
							<table class="etv2-mor-table etv2-mor-detail-table"><tbody>${taxes}</tbody></table>
						</details>

						<div class="etv2-mor-dx-totals">
							<div class="etv2-mor-dx-total"><label>${__("Net Total")}</label><span>${format_currency(d.net_total, d.currency)}</span></div>
							<div class="etv2-mor-dx-total"><label>${__("Discount")}</label><span>-${format_currency(d.discount_amount || 0, d.currency)}</span></div>
							<div class="etv2-mor-dx-total"><label>${__("Total Tax")}</label><span>${format_currency(d.total_taxes_and_charges, d.currency)}</span></div>
							<div class="etv2-mor-dx-total is-grand"><label>${__("Grand Total")}</label><span>${format_currency(d.grand_total, d.currency)}</span></div>
						</div>

						${status === "Registered" || status === "Transmitted" ? `
						<div class="etv2-mor-dx-actions">
							<button type="button" class="etv2-btn etv2-btn-primary etv2-mor-dx-light" data-invoice="${d.name}">${__("Light Receipt")}</button>
							${!is_walk_in ? `<button type="button" class="etv2-btn etv2-mor-dx-detailed" data-invoice="${d.name}">${__("Detailed Receipt")}</button>` : ""}
							<button type="button" class="etv2-btn etv2-mor-dx-verify" data-invoice="${d.name}">${__("Verify")}</button>
						</div>` : ""}
					</div>`;
          const dd = new frappe.ui.Dialog({
            title: __("MoR Invoice Details"),
            size: "large"
          });
          dd.$body.html(html);
          dd.$body.find(".etv2-mor-copy-irn").on("click", (e) => {
            e.stopPropagation();
            const val = $(e.currentTarget).attr("data-irn");
            if (navigator.clipboard && navigator.clipboard.writeText) {
              navigator.clipboard.writeText(val).then(
                () => frappe.show_alert({ message: __("IRN copied."), indicator: "green" }),
                () => frappe.show_alert({ message: __("Could not copy IRN."), indicator: "red" })
              );
            } else {
              frappe.show_alert({ message: val, indicator: "blue" });
            }
          });
          dd.$body.find(".etv2-mor-dx-light").on("click", () => {
            dd.hide();
            this.light_receipt(d.name);
          });
          dd.$body.find(".etv2-mor-dx-detailed").on("click", () => {
            dd.hide();
            this.detailed_receipt(d.name);
          });
          dd.$body.find(".etv2-mor-dx-verify").on("click", () => {
            dd.hide();
            this.verify(d.name);
          });
          dd.show();
        }
      });
    }
    cancel(invoice) {
      const d = new frappe.ui.Dialog({
        title: __("Cancel MoR Invoice") + " \u2014 " + invoice,
        fields: [
          {
            fieldname: "cancellation_reasons",
            label: __("Cancellation Reasons"),
            fieldtype: "Select",
            options: ["", "Order cancelled", "Duplicate", "Data entry mistake", "Others"],
            default: "Order cancelled"
          },
          { fieldname: "remark", label: __("Remark"), fieldtype: "Small Text" }
        ],
        primary_action_label: __("Cancel Invoice"),
        primary_action: (values) => {
          frappe.call({
            method: "ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos.cancel_mor_pos_invoice",
            args: {
              pos_invoice_name: invoice,
              cancellation_reasons: values.cancellation_reasons || "Order cancelled",
              remark: values.remark || ""
            },
            freeze: true,
            freeze_message: __("Cancelling with MoR..."),
            callback: (r) => {
              const res = r.message || {};
              if (res.status === "ok" && res.result && res.result.status === "Cancelled") {
                frappe.show_alert({ message: __("Invoice cancelled with MoR."), indicator: "green" });
              } else {
                frappe.msgprint(res.result && res.result.message || res.message || __("Cancellation failed."));
              }
              d.hide();
              this.load();
            }
          });
        }
      });
      d.show();
    }
    show_dialog(title, html) {
      const d = new frappe.ui.Dialog({
        title,
        size: "large",
        primary_action_label: __("Close"),
        primary_action: () => d.hide()
      });
      d.$body.html(html);
      d.show();
    }
    show_print_dialog(title, html, size) {
      const safe = String(html || "").replace(/<script[\s\S]*?<\/script>/gi, "").replace(/<\/?(?:html|head|body)[^>]*>/gi, "");
      const d = new frappe.ui.Dialog({
        title,
        size: size || "large",
        primary_action_label: __("Print"),
        primary_action: () => {
          const w = window.open();
          if (w) {
            w.document.write(safe);
            w.document.close();
            w.focus();
            w.print();
          }
          d.hide();
        }
      });
      d.$body.html(safe);
      d.show();
    }
  };

  // ../ethiotel_pos/ethiotel_pos/ethio_telecom_pos_app/page/ethiotel_pos/js/etv2_settings.js
  erpnext.POSV2 = erpnext.POSV2 || {};
  erpnext.POSV2.SettingsWorkspace = class {
    constructor({ shell, workspace, container, name }) {
      this.shell = shell;
      this.workspace = workspace;
      this.container = container;
      this.name = name;
      this.render();
    }
    render() {
      this.$el = $(`
			<section class="etv2-ws">
				<div class="etv2-ws-toolbar">
					<h2 class="etv2-page-title">${__("Settings")}</h2>
				</div>
				<div class="etv2-ws-content" style="flex-direction:column;max-width:640px;">
					<div class="etv2-card">
						<div class="etv2-card-header"><span class="etv2-card-title">${__("Session")}</span></div>
						<div class="etv2-card-body">
							<div class="etv2-list">
								<div class="etv2-list-row"><span class="etv2-list-row-label">${__("User")}</span><span class="etv2-list-row-amount" style="text-align:left;min-width:0;flex:1">${frappe.utils.escape_html(frappe.session.user_fullname || frappe.session.user)}</span></div>
								<div class="etv2-list-row"><span class="etv2-list-row-label">${__("POS Profile")}</span><span class="etv2-list-row-amount" style="text-align:left;min-width:0;flex:1">${frappe.utils.escape_html(this.shell.pos_profile || "\u2014")}</span></div>
								<div class="etv2-list-row"><span class="etv2-list-row-label">${__("Warehouse")}</span><span class="etv2-list-row-amount" style="text-align:left;min-width:0;flex:1">${frappe.utils.escape_html(this.shell.warehouse || "\u2014")}</span></div>
								<div class="etv2-list-row"><span class="etv2-list-row-label">${__("Company")}</span><span class="etv2-list-row-amount" style="text-align:left;min-width:0;flex:1">${frappe.utils.escape_html(this.shell.company || "\u2014")}</span></div>
								<div class="etv2-list-row"><span class="etv2-list-row-label">${__("Tax Template")}</span><span class="etv2-list-row-amount etv2-session-tax" style="text-align:left;min-width:0;flex:1">${frappe.utils.escape_html(this.shell.tax_template || "\u2014")}</span></div>
							</div>
						</div>
					</div>
					<div class="etv2-card">
						<div class="etv2-card-header"><span class="etv2-card-title">${__("Actions")}</span></div>
						<div class="etv2-card-body">
							<div class="etv2-cart-actions" style="padding:0;max-width:420px;">
								<button class="etv2-btn etv2-btn-danger etv2-close-shift-btn" ${this.shell.pos_opening ? "" : "disabled"}>${__("Close Shift")}</button>
								<button class="etv2-btn etv2-btn-ghost etv2-signout-btn">${__("Sign Out")}</button>
								<button class="etv2-btn etv2-btn-ghost etv2-fullscreen2-btn">${__("Toggle Full Screen")}</button>
							</div>
						</div>
					</div>
				</div>
			</section>
		`);
      this.$el.find(".etv2-signout-btn").on("click", () => frappe.app.logout());
      this.$el.find(".etv2-fullscreen2-btn").on("click", () => {
        if (!document.fullscreenElement)
          document.documentElement.requestFullscreen();
        else if (document.exitFullscreen)
          document.exitFullscreen();
      });
      this.$el.find(".etv2-close-shift-btn").on("click", () => this.shell.close_shift());
      return this.$el;
    }
  };
})();
//# sourceMappingURL=ethiotel-pos-v2.bundle.CXZCFARZ.js.map

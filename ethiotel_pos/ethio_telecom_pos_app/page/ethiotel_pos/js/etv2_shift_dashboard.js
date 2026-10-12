// =====================================================================
// PHASE 6 — SHIFT DASHBOARD (redesigned)
//
//   Sales Today | Transactions | Customers | Held Orders
//   Hourly Sales Chart
//   Payment Methods               | Top Selling Items
//   Recent Activity               | Cash Drawer
// =====================================================================
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
			args: { pos_profile: this.shell.pos_profile },
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
			{ label: __("Held Orders"), value: String(d.held_orders || 0), sub: __("Pending drafts") },
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
					<div class="etv2-hourly-bar" style="height:${Math.max((h.amount / max) * 100, 4)}%">
						<span class="etv2-hourly-val">${format_currency(h.amount, undefined, 0)}</span>
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
		const max = Math.max(...payments.map((p) => flt(p.amount || 0) + flt(p.opening_amount || 0)), 1);
		$list.html(
			payments.map((p) => `
				<div class="etv2-list-row">
					<span class="etv2-list-row-label">${frappe.utils.escape_html(p.mode_of_payment)}</span>
					<div class="etv2-list-bar-wrap">
						<div class="etv2-list-bar"><div class="etv2-list-bar-fill" style="width:${Math.max((flt(p.amount) / max) * 100, 4)}%"></div></div>
					</div>
					<span class="etv2-list-row-amount">${format_currency(flt(p.amount))}</span>
					${flt(p.opening_amount) ? `<span class="etv2-list-row-sub">${__("Opening")}: ${format_currency(flt(p.opening_amount))}</span>` : ""}
					${flt(p.expected_amount) ? `<span class="etv2-list-row-sub">${__("Expected")}: ${format_currency(flt(p.expected_amount))}</span>` : ""}
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
					<span class="etv2-list-row-amount">${flt(i.qty)} × ${format_currency(i.amount / (i.qty || 1), undefined, 0)}</span>
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
						<div class="etv2-activity-sub">${frappe.utils.escape_html(a.name)} · ${a.posting_time || ""}</div>
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
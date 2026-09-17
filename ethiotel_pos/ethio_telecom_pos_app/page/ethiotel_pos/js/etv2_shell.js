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

		// user avatar (the scrim is already part of SHELL_TEMPLATE)
		const initials = (frappe.session.user_fullname || frappe.session.user || "U").slice(0, 1).toUpperCase();
		this.$main.find(".etv2-avatar").text(initials);
		this.$main.find(".fk-profile-name").text(frappe.session.user_fullname || frappe.session.user);
	}

	boot() {
		this.sidebar = new erpnext.POSV2.Sidebar({ shell: this });
		this.workspaces = new erpnext.POSV2.WorkspaceManager({ shell: this });

		// register workspaces
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

		// resolve shift then open the sale workspace (only once a shift/pos
		// profile is available — otherwise get_items would 404)
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
			args: { user: frappe.session.user },
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
		$chip.find(".etv2-shift-chip-text").text(`${__("Shift open")} · ${frappe.datetime.str_to_user(this.pos_opening_time)}`);
		if (this.sidebar) {
			this.sidebar.set_shift_time(`${__("Open")} · ${frappe.datetime.str_to_user(this.pos_opening_time)}`);
		}
	}

	load_profile() {
		const pv = "ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos";
		return frappe.call({
			method: `${pv}.get_pos_profile_data`,
			args: { pos_profile: this.pos_profile },
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

			// root item group
			return frappe.call({ method: `${pv}.get_root_item_group` }).then((r2) => {
				this.parent_item_group = (r2.message && r2.message[0] && r2.message[0].name) || "All Item Groups";
			});
		});
	}

	set_status_bar() {
		this.$statusProfile.text(`${__("Profile")}: ${this.pos_profile}`);
		this.$statusWarehouse.text(`${__("Warehouse")}: ${this.warehouse || "—"}`);
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
						filters: { company: dialog.fields_dict.company.get_value() },
					}),
					onchange: () => fetch_payments(),
				},
				{
					fieldname: "taxes_and_charges",
					fieldtype: "Link",
					label: __("Tax Template"),
					options: "Sales Taxes and Charges Template",
					description: __("Sales Taxes and Charges Template for this shift's invoices. Defaults to the POS Profile; overrides the EIMS Setting default."),
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
						{ fieldname: "opening_amount", fieldtype: "Currency", in_list_view: 1, label: __("Opening Amount"), default: 0 },
					],
				},
			],
			primary_action_label: __("Open"),
			primary_action: function (values) {
				const balance = (values.balance_details || []).filter((d) => d.mode_of_payment);
				if (!balance.length) {
					frappe.show_alert({ message: __("Add at least one mode of payment."), indicator: "orange" });
					return;
				}
				frappe.call({
					method: "ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos.create_opening_voucher",
					args: { pos_profile: values.pos_profile, company: values.company, balance_details: balance, taxes_and_charges: values.taxes_and_charges },
					freeze: true,
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
			},
		});

		function fetch_payments() {
			const profile = dialog.fields_dict.pos_profile.get_value();
			if (!profile) return;
			// Only MoR-valid modes configured on the profile (rule 7022).
			frappe.call({
				method: "ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos.get_opening_payment_modes",
				args: { pos_profile: profile },
				silent: true,
			}).then((r) => {
				const modes = r.message || [];
				const mode_field = dialog.fields_dict.balance_details.df.fields.find((f) => f.fieldname === "mode_of_payment");
				if (mode_field) {
					mode_field.options = modes;
				}
				dialog.fields_dict.balance_details.df.data = modes.map((mode) => ({
					mode_of_payment: mode,
					opening_amount: 0,
				}));
				dialog.fields_dict.balance_details.grid.refresh();
				frappe.db.get_doc("POS Profile", profile).then((doc) => {
					// Default the shift tax template from the POS Profile (settings).
					if (!dialog.fields_dict.taxes_and_charges.get_value() && doc.taxes_and_charges) {
						dialog.set_value("taxes_and_charges", doc.taxes_and_charges);
					}
				});
			});
		}

		dialog.show();
	}

	// shared Close Shift action — opened from the Settings workspace so the
	// register can be locked from one place.
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
					freeze_message: __("Closing Shift..."),
				}).then((r) => {
				if (r.message && r.message.status === "ok") {
					frappe.show_alert({ message: __("Shift successfully closed (Entry: {0})", [r.message.closing_entry]), indicator: "green" });
					this.pos_opening = null;
					this.pos_profile = null;
					this.$main.find(".etv2-shift-chip").addClass("etv2-shift-chip-hidden");
					if (this.sidebar) this.sidebar.set_shift_time(null);
					// no active shift left — re-gate the page on the open dialog
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
		setInterval(tick, 1000);
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

	// helper: load POS invoices for a customer (used by several workspaces)
	get_pv() {
		return "ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos";
	}
};
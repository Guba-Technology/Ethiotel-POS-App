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

		this.discount_mode = "percentage"; // "percentage" | "value"
		this.discount_value = 0;

		this.tax_template = this.shell.tax_template || null;
		this.tax_rate = null;

		this.view_mode = "grid"; // "grid" | "list"

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
			method: `${pv}.get_walk_in_customer`,
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
							<input type="text" placeholder="${__("Search products…")}" />
						
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

		// search
		let searchTimer;
		this.$el.find(".etv2-sale-search input").on("input", (e) => {
			clearTimeout(searchTimer);
			searchTimer = setTimeout(() => this.load_products($(e.currentTarget).val()), 250);
		});

		// barcode scan — Enter (or hardware scanner terminator) adds the item
		this.$el.find(".etv2-sale-barcode input").on("keydown", (e) => {
			if (e.key === "Enter") {
				e.preventDefault();
				const code = $(e.currentTarget).val().trim();
				if (code) this.scan_barcode(code);
			}
		});

		// barcode — camera / QR scan button
		this.$el.find(".etv2-barcode-camera-btn").on("click", () => this.open_camera_scanner());

		// product view toggle (grid / list)
		this.$el.on("click", ".fk-view-btn", (e) => {
			const mode = $(e.currentTarget).attr("data-view");
			if (!mode || mode === this.view_mode) return;
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
		// categories
		this.$el.on("click", ".fk-cat-chip", (e) => {
			const $chip = $(e.currentTarget);
			this.$el.find(".fk-cat-chip").removeClass("active");
			$chip.addClass("active");
			this.active_item_group = $chip.attr("data-group");
			this.load_products(this.$el.find(".etv2-sale-search input").val());
		});

		// product click -> auto-add to cart (grid card or list row)
		this.$el.on("click", ".fk-product-card, .fk-product-row", (e) => {
			const item = this.items.find((i) => i.item_code === $(e.currentTarget).attr("data-code"));
			if (item) {
				this.add_to_cart(item);
				frappe.utils.play_sound("submit");
			}
		});

		// cart qty controls
		this.$el.on("click", ".fk-qty-btn-plus", (e) => this.change_qty($(e.currentTarget).attr("data-code"), 1));
		this.$el.on("click", ".fk-qty-btn-minus", (e) => this.change_qty($(e.currentTarget).attr("data-code"), -1));

		// cart row eye icon -> item details dialog (update cart mode)
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

		// cart row trash icon -> remove item entirely
		this.$el.on("click", ".fk-ci-remove", (e) => {
			e.stopPropagation();
			const code = $(e.currentTarget).attr("data-code");
			if (this.cart[code]) {
				delete this.cart[code];
				this.render_cart();
			}
		});

		// customer select
		this.$el.find(".etv2-sale-customer-btn").on("click", () => this.select_customer());
		//payment method select
		this.$el.find(".etv2-sale-payment-btn").on("click", () => this.select_payment_mode());
		// tax template select
		this.$el.find(".etv2-sale-tax-btn").on("click", () => this.select_tax_template());
		// cart actions
		this.$el.find(".fk-hold-btn").on("click", () => this.hold_order());
		this.$el.find(".etv2-checkin-btn").on("click", () => this.checkout());
		this.$el.find(".fk-print-invoice-btn").on("click", () => this.save_and_print("EIMS Invoice"));
		this.$el.find(".fk-print-receipt-btn").on("click", () => this.save_and_print("Forkiva Sales Receipt"));

		// discount type cards (Percentage / Amount)
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
						message: __("Discount cannot be greater than 100%."),
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
				filters: { pos_profile: this.shell.pos_profile },
			},
		}).then((r) => {
			this.item_groups = (r.message || []).map((row) => row[0]);
			const $cats = this.$el.find(".etv2-cats");
			$cats.html(
				`<button class="fk-cat-chip active" data-group="">${__("All")}</button>` +
					this.item_groups.map((g) => `<button class="fk-cat-chip" data-group="${frappe.utils.escape_html(g)}">${frappe.utils.escape_html(g)}</button>`).join("")
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
				search_term,
			},
		}).then((r) => {
			const data = r.message || { items: [] };
			Offline.cache_catalog(page_key, data);
			this.apply_products(data);
		}).catch(() => {
			// offline — fall back to the cached catalog
			const cached = Offline.load_cached_catalog(page_key);
			if (cached) {
				this.apply_products(cached);
				frappe.show_alert({ message: __("Offline mode — showing cached catalog."), indicator: "orange" });
			} else {
				frappe.show_alert({ message: __("No cached catalog for this view."), indicator: "red" });
			}
		});
	}

	apply_products(data) {
		this.items = (data && data.items) || [];
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
			is_list
				? this.items.map((i) => this.render_list_row(i)).join("")
				: this.items.map((i) => this.render_grid_card(i)).join("")
		);
	}

	render_grid_card(i) {
		const img = i.item_image
			? `<img src="${i.item_image}" onerror="this.outerHTML = etv2_ph(${JSON.stringify(i.item_name)})" />`
			: `<div class="fk-product-img-ph">${frappe.utils.escape_html((i.item_name || i.item_code || "?").slice(0, 1).toUpperCase())}</div>`;
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
		const img = i.item_image
			? `<img src="${i.item_image}" onerror="this.outerHTML = etv2_ph_row(${JSON.stringify(i.item_name)})" />`
			: `<div class="fk-row-img-ph">${frappe.utils.escape_html((i.item_name || i.item_code || "?").slice(0, 1).toUpperCase())}</div>`;
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
		const me = this;
		const key = item.item_code;
		const in_cart = this.cart[key];
		const is_update = Boolean(in_cart);

		// const full = this.items.find((i) => i.item_code === key) || item;
		const full = this.items.find((i) => i.item_code === key) || item;
		if (!full || !full.item_code) {
			frappe.show_alert({ message: __("Item details unavailable."), indicator: "orange" });
			return;
		}
		const currency = full.currency || frappe.boot.sysdefaults.currency;
		const allow_rate_change = parseInt(this.shell.settings.allow_rate_change ?? 1, 10) !== 0;
		const allow_discount_change = parseInt(this.shell.settings.allow_discount_change ?? 1, 10) !== 0;

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
				if (qty > 0 && !(await this.check_stock(row, qty, wh))) return;
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
					message: __("Cart updated · {0} × {1}", [qty, full.item_name]),
					indicator: "green",
				});
			},
		});
		dialog.$wrapper.addClass("fk-item-dialog");

		const img = full.item_image
			? `<img class="etv2-id-img" src="${full.item_image}" onerror="this.outerHTML = etv2_ph_big(${JSON.stringify(full.item_name)})" />`
			: etv2_ph_big(full.item_name || full.item_code || "?");

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
		const uoms = (full.uoms && full.uoms.length)
			? full.uoms
			: [{ uom: full.stock_uom || default_uom, conversion_factor: 1 }];
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
		$form.find(".fk-id-discount").on("input", function () {
			let v = flt($(this).val()) || 0;
			if (v < 0) v = 0;
			if (v > 100) v = 100;
			const base = flt($form.find(".fk-id-price_list_rate").val()) || 0;
			$form.find(".fk-id-rate").val(flt(base * (1 - v / 100), 2));
		});
		$form.find(".fk-id-uom").on("change", function () {
			const $opt = $(this).find("option:selected");
			const cf = flt($opt.attr("data-cf")) || 1;
			const cfInput = $form.find(".fk-id-conversion_factor");
			cfInput.val(cf);
			cfInput.prop("readonly", $(this).val() === full.stock_uom);
		});
		$form.find(".fk-id-warehouse").on("change", function () {
			const warehouse = $(this).val();
			if (!warehouse) return;
			const pv = me.shell.get_pv();
			frappe.call({
				method: `${pv}.get_warehouse_stock`,
				args: { item_code: full.item_code, warehouse },
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

	// ---------------------------------------------------------------
	// Per-field live updates in the item details dialog (ports v1's
	// form_updated): discount -> rate, uom -> conversion factor,
	// warehouse -> live stock + out-of-stock guard.
	// ---------------------------------------------------------------
	form_updated(fieldname, ctrl, controls, item) {
		if (this._suppress_onchange) return;
		const pv = this.shell.get_pv();
		if (fieldname === "discount_percentage") {
			let value = flt(ctrl.get_value()) || 0;
			if (value < 0) value = 0;
			if (value > 100) value = 100;
			ctrl.set_value(value);
			const base = flt(controls.price_list_rate.get_value()) || 0;
			controls.rate.set_value(flt(base * (1 - value / 100), 2));
		}
		if (fieldname === "uom") {
			frappe.call({
				method: `${pv}.get_uom_conversion_factor`,
				args: { item_code: item.item_code, uom: ctrl.get_value() },
			}).then((r) => {
				const cf = (r.message && r.message.conversion_factor) || 1;
				controls.conversion_factor.set_value(cf);
				controls.conversion_factor.df.read_only = ctrl.get_value() === item.stock_uom;
				controls.conversion_factor.refresh();
			});
		}
		if (fieldname === "warehouse") {
			const warehouse = ctrl.get_value();
			if (!warehouse) return;
			frappe.call({
				method: `${pv}.get_warehouse_stock`,
				args: { item_code: item.item_code, warehouse },
			}).then((r) => {
				const d = r.message || {};
				const available_qty = flt(d.actual_qty);
				controls.actual_qty.set_value(available_qty);
				if (available_qty === 0 && d.is_stock_item) {
					ctrl.set_value("");
					frappe.show_alert({
						message: __("Item {0} is not available under warehouse {1}.", [
							item.item_code.bold(),
							warehouse.bold(),
						]),
						indicator: "orange",
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
			stock_uom: item.stock_uom,
		};
	}

	// ---------------------------------------------------------------
	// Barcode scanner — resolve the code server-side then add to cart
	// ---------------------------------------------------------------
	scan_barcode(code) {
		const me = this;
		const pv = this.shell.get_pv();
		frappe.call({
			method: `${pv}.get_item_by_barcode`,
			args: { barcode: code, price_list: this.shell.price_list, pos_profile: this.shell.pos_profile },
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
			// offline — try the cached catalog
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

	// ---------------------------------------------------------------
	// Camera-based barcode / QR scanning. Uses the native BarcodeDetector
	// API where available (covers most 1D barcodes + QR on Chromium-based
	// browsers); otherwise falls back to the jsQR library (QR only),
	// loaded lazily from a CDN the first time it's needed.
	// ---------------------------------------------------------------
	open_camera_scanner() {
		const me = this;

		if (!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)) {
			frappe.show_alert({ message: __("Camera access is not available on this device or browser."), indicator: "orange" });
			return;
		}

		const dialog = new frappe.ui.Dialog({
			title: __("Scan Barcode / QR"),
			fields: [{ fieldtype: "HTML", fieldname: "body" }],
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
			if (stopped) return;
			stopped = true;
			if (rafId) cancelAnimationFrame(rafId);
			if (stream) {
				stream.getTracks().forEach((t) => t.stop());
				stream = null;
			}
		};

		dialog.$wrapper.on("hidden.bs.modal", cleanup);
		$wrapper.on("click", ".fk-scanner-cancel-btn", () => dialog.hide());

		const on_detected = (value) => {
			if (stopped || !value) return;
			cleanup();
			dialog.hide();
			this.$el.find(".etv2-sale-barcode input").val(value);
			this.scan_barcode(value);
		};

		const tick = async () => {
			if (stopped) return;
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
					// a single frame failing to decode is expected; keep scanning
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
					message: __("Could not access the camera: {0}", [(err && err.message) || err]),
					indicator: "red",
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
			// item already in cart — increment
			row.qty = flt(row.qty || 0) + qty;
		} else {
			// new item — set qty directly
			const new_row = this.cart_item_from(item);
			new_row.qty = qty;
			this.cart[key] = new_row;
		}
		// always re-render after modifying cart
		this.render_cart();
	}

	async change_qty(item_code, delta) {
		if (!this.cart[item_code]) return;
		const row = this.cart[item_code];
		const next = flt(row.qty || 0) + flt(delta);
		const wh = row.warehouse || this.warehouse;
		if (next > row.qty && !(await this.check_stock(row, next - row.qty, wh))) return;
		row.qty = Math.max(0, next);
		if (row.qty <= 0) delete this.cart[item_code];
		this.render_cart();
	}

	// ---------------------------------------------------------------
	// Stock guard on add/increment (ports v1's check_stock_availability).
	// Uses the same ERPNext helper so allow_negative_stock, stock-item
	// detection and per-warehouse quantities all match the v1 POS.
	// ---------------------------------------------------------------
	async check_stock(item, qty_needed, warehouse) {
		if (!item || !item.item_code) return true;
		const r = await frappe.call({
			method: "erpnext.accounts.doctype.pos_invoice.pos_invoice.get_stock_availability",
			args: { item_code: item.item_code, warehouse: warehouse },
		});
		const resp = r.message || [0, 1, 0];
		const available = flt(resp[0]);
		const is_stock_item = resp[1];
		const allow_negative = flt(resp[2]);

		if (allow_negative || !is_stock_item) return true;

		if (available <= 0) {
			frappe.show_alert({
				message: __("Item {0} is not available under warehouse {1}.", [
					item.item_code.bold(),
					(warehouse || "—").bold(),
				]),
				indicator: "orange",
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
						(warehouse || "—").bold(),
						available,
						(item.stock_uom || "").bold(),
					]
				),
				indicator: "orange",
			});
			frappe.utils.play_sound("error");
			return false;
		}
		return true;
	}

	cart_subtotal() {
		return Object.keys(this.cart).reduce((s, k) => s + this.cart[k].rate * this.cart[k].qty, 0);
	}

	// Taxable base before discount — mirrors the invoice net_total. When the
	// POS Profile prices are tax-inclusive, the shelf rates include VAT, so
	// the net is gross / (1 + rate).
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
			return (net * flt(this.discount_value || 0)) / 100;
		}
		return Math.min(flt(this.discount_value || 0), net);
	}

	cart_tax() {
		const taxable = this.cart_net_subtotal() - this.cart_discount();
		return (taxable * flt(this.tax_rate || 0)) / 100;
	}

	cart_total() {
		return this.cart_net_subtotal() - this.cart_discount() + this.cart_tax();
	}

	render_cart() {
		const $list = this.$el.find(".fk-cart-list");
		const keys = Object.keys(this.cart);
		const count = keys.reduce((sum, k) => sum + this.cart[k].qty, 0);
		this.$el.find(".fk-cart-count").text(count);

		// --- Top: cart items list ---
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
                        <button class="fk-qty-btn fk-qty-btn-minus" data-code="${frappe.utils.escape_html(k)}" type="button">−</button>
                        <span class="fk-qty-value">${c.qty}</span>
                        <button class="fk-qty-btn fk-qty-btn-plus" data-code="${frappe.utils.escape_html(k)}" type="button">+</button>
                    </div>
                    <div class="fk-cart-item-price">${format_currency(c.rate * c.qty, c.currency)}</div>
                </div>
            </div>`;
    }).join("")
);
				
			}

		// --- Bottom: discount + payment ---
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

		// Show/hide discount input row based on mode
		// if (this.discount_mode === "percentage" && this.discount_value > 0) {
		// 	this.$el.find(".fk-discount-input-row").show();
		// } else if (this.discount_mode === "value" && this.discount_value > 0) {
		// 	this.$el.find(".fk-discount-input-row").show();
		// } else {
		// 	this.$el.find(".fk-discount-input-row").hide();
		// }
				this.$el.find(".fk-discount-input-row").show();
	}

	// ---------------------------------------------------------------
	// Customer selection — searchable dialog over the profile customers
	// ---------------------------------------------------------------
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
			},
		});
		dialog.$wrapper.addClass("fk-customer-picker");

		const $body = dialog.fields_dict.body.$wrapper;
		$body.addClass("etv2-customer-picker");
		$body.html(`
			<div class="fk-search-box etv2-customer-picker-search">
				<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
				<input type="text" placeholder="${__("Search customers…")}" />
			</div>
			<div class="etv2-customer-picker-list"></div>
		`);

		const load = (term = "") => {
			const pv = this.shell.get_pv();
			frappe.call({
				method: `${pv}.get_customers`,
				args: { search_term: term, limit: 50 },
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
				me.$el.find(".etv2-sale-customer-btn span").html(`${__("Customer")}: <b>${frappe.utils.escape_html((message && message.customer_name) || name)}</b>`);
				dialog.hide();
			});
		});

		load();
		dialog.show();
	}
	// 	---------------------------------------------------------------
	// payment method selection
	// 	---------------------------------------------------------------
	select_payment_mode() {
	const modes = (this.shell.settings.payments || []).map((p) => p.mode_of_payment);
	if (!modes.length) {
		frappe.show_alert({ message: __("No payment modes configured on this POS Profile."), indicator: "orange" });
		return;
	}
	const dialog = new frappe.ui.Dialog({
		title: __("Select Payment Method"),
		fields: [{ fieldtype: "HTML", fieldname: "body" }],
	});
	dialog.fields_dict.body.$wrapper.html(
		`<div class="fk-pay-modes">` +
		modes.map((m) => `
			<div class="fk-pay-mode ${m === this.payment_mode ? "active" : ""}" data-mode="${frappe.utils.escape_html(m)}">
				<span class="fk-pm-info"><span class="fk-pm-name">${frappe.utils.escape_html(m)}</span></span>
				<span class="fk-pm-check"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"></path></svg></span>
			</div>`).join("") +
		`</div>`
	);
	dialog.fields_dict.body.$wrapper.on("click", ".fk-pay-mode", (e) => {
		this.payment_mode = $(e.currentTarget).attr("data-mode");
		this.$el.find(".fk-payment-label").text(this.payment_mode);
		dialog.hide();
	});
	dialog.show();
}
	// ---------------------------------------------------------------
	// Tax template — load the current shift template + its rate
	// ---------------------------------------------------------------
	load_tax_template() {
		const me = this;
		const pv = this.shell.get_pv();
		frappe.call({
			method: `${pv}.get_tax_templates`,
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
			method: `${pv}.get_tax_templates`,
		}).then((r) => {
			const data = r.message || {};
			const templates = data.templates || [];
			const dialog = new frappe.ui.Dialog({
				title: __("Select Tax Template"),
				fields: [{ fieldtype: "HTML", fieldname: "body" }],
			});
			dialog.fields_dict.body.$wrapper.html(
				`<div class="fk-pay-modes">` +
				templates.map((t) => `
					<div class="fk-pay-mode ${t.name === this.tax_template ? "active" : ""}" data-tax="${frappe.utils.escape_html(t.name)}">
						<span class="fk-pm-info">
							<span class="fk-pm-name">${frappe.utils.escape_html(t.name)}</span>
							<span class="fk-pm-sub">${__("Tax")} ${flt(t.rate)}%</span>
						</span>
						<span class="fk-pm-check"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"></path></svg></span>
					</div>`).join("") +
				`</div>`
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
					args: { tax_template: name },
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
		const default_customer = this.customer || this.walk_in_customer || (this.shell.settings && this.shell.settings.customer) || null;
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
					warehouse: c.warehouse || this.shell.warehouse,
				};
			}),
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
		if (!doc) return;
		const pv = this.shell.get_pv();
		frappe.call({
			method: `${pv}.save_held_order`,
			args: { doc },
			freeze: true,
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
		if (!doc) return;
		const pv = this.shell.get_pv();
		const win = ethiotel_print_placeholder();
		frappe.call({
			method: `${pv}.save_held_order`,
			args: { doc },
			freeze: true,
		}).then((r) => {
			if (r.message && r.message.status === "ok" && win) {
				win.location = ethiotel_print_url("POS Invoice", r.message.invoice_name, print_format);
			} else if (win) {
				win.close();
			}
		});
	}

	// ---------------------------------------------------------------
	// Checkout — forkiva payment dialog: payment-mode cards, keypad,
	// quick-pay chips, calculator popup, order-summary column with
	// grand total + change return, then submit + optional print.
	// ---------------------------------------------------------------
	checkout() {
		const doc = this.build_order_doc();
		if (!doc) return;
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
			primary_action: null,
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
							${(modes.length ? modes : [default_mode])
								.map((m) => `
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

		// payment mode select
		$body.on("click", ".fk-pay-mode", (e) => {
			selected_mode = $(e.currentTarget).attr("data-mode");
			$body.find(".fk-pay-mode").removeClass("active");
			$(e.currentTarget).addClass("active");
		});
		$body.on("click", ".fk-checkout-hold-btn", () => { dialog.hide(); this.hold_order(); });
		// summary helper
		const $sum = {
			count: $body.find(".fk-sum-count"),
			subtotal: $body.find(".fk-sum-subtotal"),
			discount: $body.find(".fk-sum-discount"),
			grand: $body.find(".fk-sum-grand"),
			received: $body.find(".fk-sum-received"),
			change: $body.find(".fk-sum-change"),
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

		// keypad
		const keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", ".", "0", "C"];
		$body.find(".fk-keypad").html(
			keys
				.map(
					(k) => `
						<button type="button" class="fk-pad-btn ${k === "C" ? "fk-pad-clear" : ""}" data-key="${k === "." ? "dot" : k}">${k}</button>`
				)
				.join("")
		);
		$body.on("click", ".fk-pad-btn", (e) => {
			const k = $(e.currentTarget).attr("data-key");
			const $input = $body.find(".fk-amount-input");
			let val = $input.val();
			if (k === "C") {
				$input.val(total);
			} else if (k === "dot") {
				if (!String(val).includes(".")) $input.val(val === "" ? "0." : val + ".");
			} else {
				$input.val(val === "" ? k : String(val) + k);
			}
			render_summary();
		});

		// quick pay
		$body.find(".fk-quick-pay").html(
			quick_pay.map((amt) => `<button type="button" class="fk-quick-pay-btn" data-amt="${amt}">+ ${format_currency(amt)}</button>`).join("")
		);
		$body.on("click", ".fk-quick-pay-btn", (e) => {
			$body.find(".fk-amount-input").val($(e.currentTarget).attr("data-amt"));
			render_summary();
		});

		// live summary on manual input
		$body.find(".fk-amount-input").on("input", render_summary);
		render_summary();

		// calculator popup
		$body.find(".fk-calculator-btn").on("click", () => {
			this.open_calculator(total, (value) => {
				$body.find(".fk-amount-input").val(flt(value));
				render_summary();
			});
		});

		// charge actions
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

			// OFFLINE MODE — queue the order locally, sync when back online
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
					indicator: "orange",
				});
				return;
			}

			const pv = this.shell.get_pv();
			frappe.call({
				method: `${pv}.save_held_order`,
				args: { doc },
				freeze: true,
			}).then((r) => {
				if (r.message && r.message.status === "ok") {
					frappe.call({ method: `${pv}.submit_invoice`, args: { name: r.message.invoice_name } }).then((res) => {
						if (res.message && res.message.status === "ok") {
							this.shell.last_invoice_name = res.message.invoice_name;
							const change = flt(amount_received) - total;
							dialog.hide();
							frappe.show_alert({
								message: __("Invoice {0} submitted · change {1}", [res.message.invoice_name, format_currency(change)]),
								indicator: "green",
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
								message: (res.message && res.message.message) || __("Invoice submission failed."),
								indicator: "red",
							});
						}
					}).catch((err) => {
						console.error("Invoice submission error:", err);
					});
				} else {
					frappe.show_alert({
						message: (r.message && r.message.message) || __("Could not save the order."),
						indicator: "red",
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

	// ---------------------------------------------------------------
	// After a sale is submitted: hand MoR registration + light-receipt
	// preparation to a background worker, and immediately show the light
	// (Forkiva) receipt so the cashier can print it right away.
	// ---------------------------------------------------------------
	finalize_sale_with_mor(invoice_name) {
		const pv = this.shell.get_pv();
		frappe.call({
			method: `${pv}.queue_mor_registration`,
			args: { pos_invoice_name: invoice_name },
		}).then((r) => {
			const res = r.message || {};
			if (res.status === "queued") {
				frappe.show_alert({
					message: __("Sending to MoR in background…"),
					indicator: "blue",
				});
			} else if (res.status === "error") {
				frappe.show_alert({
					message: res.message || __("MoR registration not queued."),
					indicator: "orange",
				});
			}
		}).catch((err) => {
			console.error("MoR queue error:", err);
		});
		frappe.call({
			method: `${pv}.get_light_receipt`,
			args: { pos_invoice_name: invoice_name },
		}).then((r) => {
			const res = r.message || {};
			if (!(res.status === "ok" && res.html)) {
				return;
			}
			const safe = String(res.html)
				.replace(/<script[\s\S]*?<\/script>/gi, "")
				.replace(/<\/?(?:html|head|body)[^>]*>/gi, "");
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
				},
			});
			d.$body.html(safe);
			d.show();
		}).catch((err) => {
			console.error("Light receipt error:", err);
		});
	}

	// ---------------------------------------------------------------
	// Calculator popup — forkiva calculator-card (4-col grid, display,
	// expression + preview). on_apply(value) receives the result.
	// ---------------------------------------------------------------
	open_calculator(initial, on_apply) {
		const dialog = new frappe.ui.Dialog({
			title: __("Calculator"),
			fields: [{ fieldtype: "HTML", fieldname: "body" }],
			primary_action_label: __("OK"),
			primary_action: () => {
				const res = dialog.fields_dict.body.$wrapper.find(".fk-calc-preview").text();
				const parsed = parseFloat(String(res).replace(/[^\d.-]/g, ""));
				if (!isNaN(parsed)) on_apply(parsed);
				dialog.hide();
			},
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
					<button type="button" class="fk-calc-btn fk-calc-op" data-k="/">÷</button>
					<button type="button" class="fk-calc-btn fk-calc-op" data-k="*">×</button>
					<button type="button" class="fk-calc-btn fk-calc-clear" data-k="back">⌫</button>
					<button type="button" class="fk-calc-btn" data-k="7">7</button>
					<button type="button" class="fk-calc-btn" data-k="8">8</button>
					<button type="button" class="fk-calc-btn" data-k="9">9</button>
					<button type="button" class="fk-calc-btn fk-calc-op" data-k="-">−</button>
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
				// eslint-disable-next-line no-new-func
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
			if (r !== null) on_apply(round(r, 2));
			dialog.hide();
		});
		$w.find(".fk-calc-cancel-btn").on("click", () => dialog.hide());

		dialog.show();
	}

	quick_pay_amounts(total) {
		const t = Math.ceil(total);
		const denominations = [10, 20, 50, 100, 200, 500, 1000, 2000];
		const out = [];
		for (const d of denominations) {
			const rounded = Math.ceil(t / d) * d;
			if (rounded > total && !out.includes(rounded)) out.push(rounded);
			if (out.length >= 6) break;
		}
		if (!out.includes(t)) out.unshift(t);
		return out.slice(0, 6);
	}

	// ---------------------------------------------------------------
	// Post-sale actions — print invoice + print receipt via EIMS formats
	// ---------------------------------------------------------------
	after_sale_actions(invoice_name, change) {
		frappe.confirm(
			__("Invoice {0} submitted successfully{1}. Print the receipt?", [invoice_name, change ? ` (change ${format_currency(change)})` : ""]),
			() => this.print_receipt(invoice_name), // yes
			() => {} // no
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
		// nothing needed
	}
};

// global helpers used by inline onerror handlers
window.etv2_ph = function (name) {
	const $div = $(`<div class="fk-product-img-ph">${frappe.utils.escape_html(String(name || "?").slice(0, 1).toUpperCase())}</div>`);
	return $div[0].outerHTML;
};

window.etv2_ph_row = function (name) {
	const $div = $(`<div class="fk-row-img-ph">${frappe.utils.escape_html(String(name || "?").slice(0, 1).toUpperCase())}</div>`);
	return $div[0].outerHTML;
};

window.etv2_ph_big = function (name) {
	return `<div class="etv2-id-img-ph">${frappe.utils.escape_html(String(name || "?").slice(0, 1).toUpperCase())}</div>`;
};
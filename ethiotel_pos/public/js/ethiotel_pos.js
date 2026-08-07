/* =========================================================================
   Ethio Telecom / Tele POS — EIMS-style UX + OFFLINE support
   Loaded app-wide; self-guards to POS pages.
   ========================================================================= */

frappe.provide("ethiotel_pos");

ethiotel_pos.OFFLINE_KEY = "et_offline_queue";
ethiotel_pos.CATALOG_KEY = "et_catalog_cache";
ethiotel_pos.state = { app_ready: false, timers: [] };

/* -------------------------------------------------------------------------
   Helpers
   ------------------------------------------------------------------------- */
ethiotel_pos.get_current_time = function () {
	const now = new Date();
	return now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
};

ethiotel_pos.is_online = function () {
	return navigator.onLine !== false;
};

ethiotel_pos.is_pos_page = function () {
	const p = window.location.pathname || "";
	return p.indexOf("/ethiotel-pos") !== -1;
};

ethiotel_pos.toggle_fullscreen = function () {
	const fs = document.fullscreenElement;
	if (fs) document.exitFullscreen().catch(() => {});
	else
		document.documentElement
			.requestFullscreen()
			.catch(() => frappe.show_alert({ message: __("Fullscreen not supported"), indicator: "orange" }));
};

/* -------------------------------------------------------------------------
   Offline queue (localStorage)
   ------------------------------------------------------------------------- */
ethiotel_pos.get_queue = function () {
	try {
		return JSON.parse(localStorage.getItem(ethiotel_pos.OFFLINE_KEY)) || [];
	} catch (e) {
		return [];
	}
};

ethiotel_pos.save_queue = function (q) {
	localStorage.setItem(ethiotel_pos.OFFLINE_KEY, JSON.stringify(q));
};

ethiotel_pos.queue_order = function (order_doc, ref) {
	const q = ethiotel_pos.get_queue();
	q.push({
		ref: ref || "ofl-" + frappe.utils.get_random(6),
		timestamp: new Date().toISOString(),
		order: JSON.parse(JSON.stringify(order_doc)),
	});
	ethiotel_pos.save_queue(q);
	ethiotel_pos.update_offline_badge();
	frappe.show_alert({
		message: __("Network unavailable. Order queued for sync (id: {0}).", [ref]),
		indicator: "orange",
	});
};

ethiotel_pos.sync_queued = function () {
	if (!ethiotel_pos.is_online()) return;

	const q = ethiotel_pos.get_queue();
	if (!q.length) return;

	const item = q[0];
	frappe.call({
		method: "ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos.save_offline_order",
		args: { order: item.order, ref: item.ref },
		freeze: true,
		callback: (r) => {
			if (r.message && r.message.status === "ok") {
				ethiotel_pos.save_queue(q.slice(1));
				frappe.show_alert({
					message: __("Offline order synced: {0}", [r.message.invoice_name]),
					indicator: "green",
				});
				ethiotel_pos.update_offline_badge();
				/* drain next */
				ethiotel_pos.sync_queued();
			} else {
				frappe.show_alert({
					message: __("Offline order sync failed: {0}", [r.message && r.message.message]),
					indicator: "red",
				});
			}
		},
	});
};

ethiotel_pos.update_offline_badge = function () {
	let $badge = $(".et-offline-badge");
	const pending = ethiotel_pos.get_queue().length;

	if (ethiotel_pos.is_online() && pending === 0) {
		$badge.remove();
		return;
	}
	if (!$badge.length) {
		$badge = $('<span class="et-offline-badge"></span>');
		$(".navbar-right").prepend($badge);
	}
	$badge.text(ethiotel_pos.is_online() ? __("{0} to sync", [pending]) : __("OFFLINE") + " (" + pending + ")");
};

/* -------------------------------------------------------------------------
   Catalog cache — used by the frappe.call interceptor
   ------------------------------------------------------------------------- */
ethiotel_pos.get_catalog = function (key) {
	try {
		const all = JSON.parse(localStorage.getItem(ethiotel_pos.CATALOG_KEY)) || {};
		return all[key] || null;
	} catch (e) {
		return null;
	}
};

ethiotel_pos.cache_catalog = function (key, data) {
	try {
		const all = JSON.parse(localStorage.getItem(ethiotel_pos.CATALOG_KEY)) || {};
		all[key] = data;
		localStorage.setItem(ethiotel_pos.CATALOG_KEY, JSON.stringify(all));
	} catch (e) {
		console.warn("[ethiotel_pos] catalog cache error", e);
	}
};

/* -------------------------------------------------------------------------
   Intercept frappe.call:
   - get_items / item lookups: serve from cache when offline (then queue the
     call so data can refresh once back online)
   - frappe.client.save (POS Invoice submit): queue the doc when offline

   IMPORTANT FIX:
   Calls that we don't need to modify MUST be forwarded to the original
   frappe.call using `_orig_call.apply(this, arguments)` — i.e. the exact,
   untouched original arguments. Frappe core supports two call signatures:
     1) frappe.call({ method, args, callback })              (object form)
     2) frappe.call(method, args, callback, headers)          (positional form)
   The original bug rebuilt a normalized object from the positional form and
   then called `_orig_call.call(this, args)` — passing only ONE argument.
   frappe.call's own internal parsing re-inspects `arguments[0]` /
   `arguments[1]` / `arguments[2]`, so when it received just one argument,
   `arguments[1]` (the actual params, e.g. { page: "Home" }) was lost and an
   empty payload was sent to the server — causing errors like:
     TypeError: get_desktop_page() missing 1 required positional argument: 'page'
   This version only builds a normalized object when it actually needs to
   mutate something (e.g. wrap the callback for caching); otherwise it calls
   `_orig_call.apply(this, arguments)` to preserve the original call shape.
   ------------------------------------------------------------------------- */
(function () {
	if (!window.frappe || !frappe.call) return;
	const _orig_call = frappe.call;

	const CACHED_GET_METHODS = [
		"ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos.get_items",
		"ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos.get_past_order_list",
		"erpnext.accounts.doctype.pos_invoice.pos_invoice.get_stock_availability",
	];
	const SUBMIT_METHODS = [
		"frappe.client.save",
		"frappe.desk.form.save.savedocs",
	];

	frappe.call = function () {
		/* Normalize ONLY for inspection (method name, args, etc). We do not
		   forward this normalized object unless we actually need to mutate
		   the call (e.g. wrap the callback). */
		let opts = arguments[0];
		if (typeof opts === "string") {
			opts = {
				method: arguments[0],
				args: arguments[1],
				callback: arguments[2],
				headers: arguments[3],
			};
		}

		const method = (opts && opts.method) || "";
		const is_pos_page = ethiotel_pos.is_pos_page();
		const offline = !ethiotel_pos.is_online();

		/* ---- cached GETs ---- */
		if (is_pos_page && CACHED_GET_METHODS.indexOf(method) !== -1) {
			const cache_key = method + ":" + JSON.stringify((opts && opts.args) || {});
			const cached = ethiotel_pos.get_catalog(cache_key);

			/* when offline, serve cache immediately — don't hit the server at all */
			if (offline && cached) {
				opts.callback && opts.callback({ message: cached, cached: true });
				return { message: cached, cached: true };
			}

			/* We need to wrap the callback to refresh the cache on success.
			   Since we're intentionally mutating the call, it's safe (and
			   necessary) to forward the normalized `opts` object here rather
			   than the raw arguments — this covers both call signatures
			   uniformly. */
			const user_cb = opts.callback;
			opts.callback = function (r) {
				if (r && r.message && !r.cached) {
					ethiotel_pos.cache_catalog(cache_key, r.message);
				}
				user_cb && user_cb(r);
			};

			return _orig_call.call(this, opts);
		}

		/* ---- POS invoice submit while offline → queue ---- */
		if (
			is_pos_page &&
			offline &&
			SUBMIT_METHODS.indexOf(method) !== -1 &&
			opts.args &&
			opts.args.doc &&
			opts.args.doc.doctype === "POS Invoice"
		) {
			ethiotel_pos.queue_order(opts.args.doc, opts.args.doc.name);
			return;
		}

		/* ---- everything else: forward the EXACT original arguments ----
		   This is the critical fix. Do not rebuild/collapse arguments here,
		   or frappe.call's internal positional-vs-object parsing breaks. */
		return _orig_call.apply(this, arguments);
	};

	/* re-attempt queued sync when connectivity returns */
	window.addEventListener("online", function () {
		ethiotel_pos.update_offline_badge();
		setTimeout(ethiotel_pos.sync_queued, 1500);
	});
})();

/* -------------------------------------------------------------------------
   Navbar branding + live clock (EIMS-style)
   ------------------------------------------------------------------------- */
ethiotel_pos.apply_branding = function () {
	if (!frappe.ui || !frappe.ui.toolbar) return;

	ethiotel_pos.replace_navbar_brand();

	if (!$(".et-nav-clock").length) {
		const $clock = $(
			'<div class="et-nav-clock" title="Ethio Telecom — Live time"><i></i><span></span></div>'
		);
		$(".navbar-right").prepend($clock);
	}
	$(".et-nav-clock span").text(ethiotel_pos.get_current_time());

	if (ethiotel_pos.state.timers.length === 0) {
		ethiotel_pos.state.timers.push(
			setInterval(function () {
				$(".et-nav-clock span").text(ethiotel_pos.get_current_time());
				ethiotel_pos.update_offline_badge();
			}, 1000)
		);
	}

	if (!$(".et-nav-shop").length) {
		const $shop = $(
			'<div class="et-nav-shop"><a href="/app/ethiotel-pos" title="Open Tele POS"><i class="fa fa-cart-arrow-down" aria-hidden="true"></i> POS</a></div>'
		);
		$(".navbar-right").append($shop);
	}
};

/* Replace the default ERPNext navbar logo with the ethiotel brand mark. */
ethiotel_pos.replace_navbar_brand = function () {
	if ($(".et-nav-brand").length) return;

	var $brand = $(".navbar .navbar-brand, .navbar-header .navbar-brand, .desk-sidebar .sidebar-logo").first();
	var logo_url = "/assets/ethiotel_pos/images/tele.jpg";

	/* -------------------------------------------------------------
	   PUT YOUR LOGO IMAGE HERE:
	     apps/ethiotel_pos/ethiotel_pos/public/images/tele.jpg
	   (served at /assets/ethiotel_pos/images/tele.jpg).
	   Keep the file name or update the flag below.
	---------------------------------------------------------------- */
	var $el = $(
		'<a class="et-nav-brand navbar-brand" href="/app">' +
			'<img class="et-nav-logo" src="' + logo_url + '" alt="ethiotel Invoice" ' +
				'onerror="this.style.display=\'none\'" />' +
			'<span class="et-nav-brand-text">ethiotel Invoice</span>' +
		"</a>"
	);

	if ($brand.length) {
		$el.attr("href", $brand.attr("href") || "/app");
		$brand.replaceWith($el);
	} else {
		$(".navbar .container").prepend($el);
	}
};

/* -------------------------------------------------------------------------
   POS page: keyboard shortcuts & quick-cash helper
   ------------------------------------------------------------------------- */
ethiotel_pos.pos_page_hook = function () {
	if (!ethiotel_pos.is_pos_page()) return;

	window.addEventListener("keydown", function (e) {
		if (e.shiftKey && e.ctrlKey && (e.key === "F" || e.key === "f")) {
			e.preventDefault();
			ethiotel_pos.toggle_fullscreen();
			return;
		}
		if (e.key === "F2") {
			e.preventDefault();
			const $search = $(".point-of-sale-app .search-field input").first();
			if ($search.length) $search.focus();
			return;
		}
		if (e.key === "F9") {
			e.preventDefault();
			ethiotel_pos.sync_queued();
			return;
		}
	});
};

/* -------------------------------------------------------------------------
   Boot
   ------------------------------------------------------------------------- */
$(document).on("app_ready", function () {
	ethiotel_pos.state.app_ready = true;
	ethiotel_pos.apply_branding();
	ethiotel_pos.pos_page_hook();
	ethiotel_pos.update_offline_badge();

	window.addEventListener("offline", ethiotel_pos.update_offline_badge);
	setTimeout(() => ethiotel_pos.update_offline_badge(), 800);
});
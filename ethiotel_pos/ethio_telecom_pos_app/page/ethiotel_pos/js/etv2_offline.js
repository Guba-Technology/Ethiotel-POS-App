// =====================================================================
// OFFLINE MODE — catalog cache + order queue for the V2 POS
// * Catalog: get_items / get_item_by_barcode responses are cached in
//   localStorage; served from cache when the network is down or the
//   request fails, so cashiers can keep selling.
// * Orders: checkout while offline stores the order doc in a queue and
//   replays it through save_offline_order when the network returns.
// =====================================================================
erpnext.POSV2 = erpnext.POSV2 || {};

erpnext.POSV2.Offline = {
	OFFLINE_KEY: "et_offline_queue",
	CATALOG_KEY: "et_catalog_cache",
	CATALOG_TTL: 1000 * 60 * 60 * 6, // 6h: keep item cache short so stale product data is not retained
	QUEUE_MAX_AGE: 1000 * 60 * 60 * 24 * 2, // 48h: drop orders that can never be synced
	SYNCED_FLAG_KEY: "et_offline_synced_at",

	is_online() {
		return navigator.onLine !== false;
	},

	// ---------------- catalog cache ----------------
	get_catalog() {
		try {
			return JSON.parse(localStorage.getItem(this.CATALOG_KEY) || "{}");
		} catch (e) {
			return {};
		}
	},

	cache_catalog(page_key, data) {
		if (!data) return;
		try {
			const cache = this.get_catalog();
			cache[page_key] = { data, ts: Date.now() };
			// keep only the most recent 40 pages
			const keys = Object.keys(cache);
			if (keys.length > 40) {
				keys.sort((a, b) => (cache[a].ts || 0) - (cache[b].ts || 0));
				keys.slice(0, keys.length - 40).forEach((k) => delete cache[k]);
			}
			localStorage.setItem(this.CATALOG_KEY, JSON.stringify(cache));
		} catch (e) {
			// storage full / unavailable — skip caching
		}
	},

	load_cached_catalog(page_key) {
		try {
			const cache = this.get_catalog();
			const entry = cache[page_key];
			if (!entry) return null;
			if (Date.now() - (entry.ts || 0) > this.CATALOG_TTL) return null;
			return entry.data;
		} catch (e) {
			return null;
		}
	},

	// Find an item in any cached page by code/barcode (barcode fallback).
	find_cached_item(code) {
		const cache = this.get_catalog();
		for (const key of Object.keys(cache)) {
			const items = cache[key].data && cache[key].data.items;
			if (!items) continue;
			const hit = items.find(
				(i) => i.item_code === code || (i.barcode && i.barcode === code)
			);
			if (hit) return hit;
		}
		return null;
	},

	// ---------------- offline order queue ----------------
	get_queue() {
		try {
			const queue = JSON.parse(localStorage.getItem(this.OFFLINE_KEY) || "[]");
			// purge stale entries so synced/customer data is not kept indefinitely
			const now = Date.now();
			const fresh = queue.filter((q) => q && (now - (q.ts || 0)) <= this.QUEUE_MAX_AGE);
			if (fresh.length !== queue.length) {
				this.set_queue(fresh);
			}
			return fresh;
		} catch (e) {
			return [];
		}
	},

	set_queue(queue) {
		try {
			localStorage.setItem(this.OFFLINE_KEY, JSON.stringify(queue));
		} catch (e) {
			// ignore
		}
	},

	clear_synced_flag() {
		try {
			localStorage.removeItem(this.SYNCED_FLAG_KEY);
		} catch (e) {
			// ignore
		}
	},

	queue_order(doc) {
		const original = this.get_queue();
		const now = Date.now();
		// store a copy; strip non-essential fields that could carry PII to disk
		const doc_copy = this._sanitize_doc_for_storage(doc);
		const queue = original.concat([{ doc: doc_copy, ts: now, ref: `offline-${now}-${original.length + 1}` }]);
		this.set_queue(queue);
	},

	_sanitize_doc_for_storage(doc) {
		// Keep the order replayable but avoid persisting fields the server can
		// re-resolve (addresses/contacts) that include PII in browser storage.
		const clean = { ...(doc || {}) };
		[ "customer_address", "shipping_address_name", "shipping_address", "contact_email",
		  "contact_mobile", "contact_phone", "additional_notes", "remark", "remarks" ]
			.forEach((k) => { if (k in clean) clean[k] = ""; });
		return clean;
	},

	// ---------------- sync ----------------
	sync_queue() {
		if (!this.is_online()) return Promise.resolve({ synced: 0 });
		const queue = this.get_queue();
		if (!queue.length) return Promise.resolve({ synced: 0 });

		const pv = "ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos";
		const refs = queue.map((q) => q.ref);
		return frappe
			.call({
				method: `${pv}.save_offline_order`,
				args: { order: queue[queue.length - 1].doc, ref: refs[refs.length - 1] },
				freeze: true,
				freeze_message: __("Syncing offline orders…"),
			})
			.then((r) => {
				if (r.message && r.message.status === "ok") {
					const remaining = queue.slice(0, -1);
					this.set_queue(remaining);
					this.clear_synced_flag();
					return { synced: 1, invoice_name: r.message.invoice_name };
				}
				return { synced: 0 };
			})
			.catch(() => ({ synced: 0 }));
	},

	start_sync_watcher() {
		$(window).on("online.etv2", () => {
			this.sync_queue().then((res) => {
				if (res.synced) {
					frappe.show_alert({
						message: __("Offline order {0} synced.", [res.invoice_name || ""]),
						indicator: "green",
					});
				}
			});
		});
	},
};

// wire the sync watcher as soon as the page loads
$(function () {
	erpnext.POSV2.Offline.start_sync_watcher();
});

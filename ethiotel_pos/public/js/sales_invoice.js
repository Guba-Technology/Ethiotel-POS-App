
const SI_MOR_WALK_IN = "Walk-In Customer";

frappe.ui.form.on("Sales Invoice", {
	refresh: function (frm) {
		if (frm.fields_dict.disable_rounded_total) {
			frm.set_value("disable_rounded_total", 1);
			frm.set_df_property("disable_rounded_total", "read_only", 1);
			frm.refresh_field("disable_rounded_total");
		}
		frm.events.setup_mor_tasks(frm);
	},

	setup_mor_tasks: function (frm) {
		// inner buttons are re-added on every refresh — clear them all first
		[
			"Register with MoR",
			"Retry Registration",
			"Re-send Registration",
			"Get Receipt",
			"Get Withholding Receipt",
			"Verify with MoR",
			"Cancel MoR Invoice",
			"MoR Details",
			// legacy labels from older builds
			"Register Invoice To MoR",
			"Verify",
			"Cancel",
		].forEach((label) => frm.page.remove_inner_button(label, __("MoR Tasks")));

		frm.events.inject_mor_css(frm);

		const is_submitted = !frm.is_new() && frm.doc.docstatus === 1;
		const status = is_submitted ? (frm.doc.custom_eims_status || "").trim() : "";
		const has_irn = !!frm.doc.custom_irn;

		frm.events.render_mor_banner(frm, status, has_irn);

		if (!is_submitted) return;

		const add = (label, handler, danger) => {
			const btn = frm.page.add_inner_button(__(label), function () {
				handler(frm);
			}, __("MoR Tasks"));
			if (danger && btn) btn.addClass("btn-danger");
		};

		switch (status) {
			case "Registered":
				add("Get Receipt", frm.events.get_receipt);
				add("Verify with MoR", frm.events.verify);
				add("Cancel MoR Invoice", frm.events.cancel, true);
				break;
			case "Failed":
				add("Retry Registration", frm.events.register_with_mor);
				break;
			case "Pending":
				// async registration in flight at MoR; resending reuses the
				// same document number and is idempotent server-side
				add("Re-send Registration", frm.events.register_with_mor);
				break;
			case "Cancelled":
				break;
			default:
				// Not Submitted
				add("Register with MoR", frm.events.register_with_mor);
		}
		if (status !== "") {
			add("MoR Details", frm.events.show_details);
		}
	},

	render_mor_banner: function (frm, status, has_irn) {
		const $wrap = frm.$wrapper.find(".layout-main-section-wrapper");
		if (!$wrap.length) return;
		let $banner = $wrap.find("#etv2-si-mor-banner");
		if (!frm.is_new() && frm.doc.docstatus === 1) {
			if (!$banner.length) {
				$banner = $('<div id="etv2-si-mor-banner"></div>').prependTo($wrap);
			}
			const irn = frm.doc.custom_irn || "";
			const tone = {
				Registered: "is-green",
				Pending: "is-orange",
				Failed: "is-red",
				Cancelled: "is-gray",
			}[status] || "is-blue";
			const label = status || "Not Submitted";
			const irn_html = irn
				? `<span class="etv2-si-kv"><label>IRN</label><code class="etv2-si-irn" title="${frappe.utils.escape_html(irn)}">${frappe.utils.escape_html(irn.slice(0, 24))}${irn.length > 24 ? "…" : ""}</code>
					<button type="button" class="btn btn-xs btn-default etv2-si-copy" data-irn="${frappe.utils.escape_html(irn)}">${__("Copy")}</button></span>`
				: "";
			const total = frm.doc.custom_mor_total_value
				? `<span class="etv2-si-kv"><label>${__("MoR Total")}</label><b>${format_currency(frm.doc.custom_mor_total_value, frm.doc.currency)}</b></span>`
				: "";
			$banner.attr("class", `etv2-si-banner ${tone}`).html(`
				<span class="etv2-si-badge">${__(label)}</span>
				${irn_html}
				${frm.doc.custom_document_number ? `<span class="etv2-si-kv"><label>${__("Doc #")}</label><b>#${frappe.utils.escape_html(String(frm.doc.custom_document_number))}</b></span>` : ""}
				${total}
				<a class="etv2-si-more" href="javascript:void(0)">${__("Details")} ›</a>
			`);
			$banner.find(".etv2-si-copy").on("click", function (e) {
				e.stopPropagation();
				frm.events.copy_irn($(e.currentTarget).attr("data-irn"));
			});
			$banner.find(".etv2-si-more").on("click", () => frm.events.show_details(frm));
			$banner.off("click").on("click", () => frm.events.show_details(frm));
		} else if ($banner.length) {
			$banner.remove();
		}
	},

	inject_mor_css: function () {
		if (document.getElementById("etv2-si-mor-css")) return;
		const css = `
			.etv2-si-banner{display:flex;align-items:center;gap:14px;flex-wrap:wrap;
				padding:9px 14px;margin:0 0 12px;border-radius:10px;border:1px solid #e2e8f0;
				background:#f8fafc;font-size:12px;cursor:pointer;}
			.etv2-si-banner.is-green{background:#f0fdf4;border-color:#86efac;}
			.etv2-si-banner.is-orange{background:#fffbeb;border-color:#fcd34d;}
			.etv2-si-banner.is-red{background:#fef2f2;border-color:#fca5a5;}
			.etv2-si-banner.is-gray{background:#f8fafc;border-color:#cbd5e1;}
			.etv2-si-banner.is-blue{background:#eff6ff;border-color:#93c5fd;}
			.etv2-si-badge{padding:3px 11px;border-radius:9999px;font-weight:700;font-size:10px;
				letter-spacing:.5px;text-transform:uppercase;background:#1e293b;color:#fff;}
			.is-green .etv2-si-badge{background:#16a34a;} .is-orange .etv2-si-badge{background:#d97706;}
			.is-red .etv2-si-badge{background:#dc2626;} .is-gray .etv2-si-badge{background:#64748b;}
			.is-blue .etv2-si-badge{background:#2563eb;}
			.etv2-si-badge-green{background:#16a34a;} .etv2-si-badge-orange{background:#d97706;}
			.etv2-si-badge-red{background:#dc2626;} .etv2-si-badge-gray{background:#64748b;}
			.etv2-si-badge-blue{background:#2563eb;}
			.etv2-si-kv{display:inline-flex;align-items:center;gap:5px;color:#475569;}
			.etv2-si-kv label{font-size:10px;text-transform:uppercase;letter-spacing:.4px;
				color:#94a3b8;font-weight:700;}
			.etv2-si-irn{font-family:monospace;font-size:11px;padding:1px 6px;background:#fff;
				border:1px solid #e2e8f0;border-radius:4px;max-width:260px;overflow:hidden;
				text-overflow:ellipsis;white-space:nowrap;display:inline-block;vertical-align:middle;}
			.etv2-si-copy{margin-left:2px;}
			.etv2-si-more{margin-left:auto;color:#16a34a;font-weight:700;font-size:12px;}
			.etv2-si-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin-bottom:12px;}
			.etv2-si-cell{border:1px solid #e2e8f0;border-radius:8px;padding:7px 10px;background:#fff;
				display:flex;flex-direction:column;gap:2px;min-width:0;}
			.etv2-si-cell label{font-size:10px;text-transform:uppercase;letter-spacing:.4px;
				color:#94a3b8;font-weight:700;}
			.etv2-si-cell span{font-weight:600;word-break:break-word;color:#1e293b;font-size:12px;}
			.etv2-si-irncell{flex-direction:row;align-items:center;gap:8px;grid-column:span 2;}
			.etv2-si-irncell span{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
				font-family:monospace;font-size:11px;}
			.etv2-si-section h4,.etv2-si-h4{margin:14px 0 6px;font-size:13px;color:#1e293b;font-weight:700;}
			.etv2-si-count{display:inline-block;min-width:18px;text-align:center;background:#dcfce7;
				color:#15803d;font-size:10px;font-weight:800;border-radius:9px;padding:1px 6px;margin-left:4px;}
			.etv2-si-table{width:100%;border-collapse:collapse;font-size:12px;margin-bottom:4px;}
			.etv2-si-table th{background:#f1f5f9;color:#475569;text-align:left;padding:5px 8px;
				font-size:10px;text-transform:uppercase;letter-spacing:.4px;border-bottom:2px solid #e2e8f0;}
			.etv2-si-table td{padding:5px 8px;border-bottom:1px solid #f1f5f9;color:#334155;}
			.etv2-si-right{text-align:right;} .etv2-si-num{font-variant-numeric:tabular-nums;}
			.etv2-si-totals{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin-top:10px;}
			.etv2-si-total{border:1px dashed #e2e8f0;border-radius:8px;padding:7px 10px;text-align:right;background:#fff;}
			.etv2-si-total label{display:block;font-size:10px;color:#94a3b8;font-weight:700;text-transform:uppercase;}
			.etv2-si-total span{font-weight:700;color:#1e293b;font-variant-numeric:tabular-nums;font-size:12px;}
			.etv2-si-total.is-grand{background:#f0fdf4;border-style:solid;border-color:#86efac;}
			.etv2-si-total.is-grand span{font-size:13px;font-weight:800;color:#14532d;}
			.etv2-si-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px;padding-top:10px;
				border-top:1px solid #e2e8f0;}
			.etv2-si-muted{color:#94a3b8;} .etv2-si-mono{font-family:monospace;}
			@media (max-width: 640px){
				.etv2-si-table thead{display:none;}
				.etv2-si-table tr{display:block;border:1px solid #e2e8f0;border-radius:8px;
					margin-bottom:8px;padding:6px 10px;background:#fff;}
				.etv2-si-table td{display:flex;justify-content:space-between;align-items:baseline;
					gap:12px;border-bottom:none;padding:3px 0;text-align:right;}
				.etv2-si-table td::before{content:attr(data-label);color:#94a3b8;font-weight:700;
					font-size:10px;text-transform:uppercase;text-align:left;flex-shrink:0;}
				.etv2-si-irncell{grid-column:1/-1;}
			}`;
		const $style = $(`<style id="etv2-si-mor-css">${css}</style>`);
		$("head").append($style);
	},

	/* ------------------------------------------------------------------
	   ACTIONS
	   ------------------------------------------------------------------ */
	register_with_mor: function (frm) {
		frappe.call({
			method: "ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos.register_sales_invoice",
			args: { sales_invoice: frm.doc.name },
			freeze: true,
			freeze_message: __("Registering with MoR…"),
			callback: function (r) {
				const res = r.message || {};
				const result = res.result || {};
				if (res.status === "ok") {
					if ((result.message || "").indexOf("Already") === 0) {
						frappe.show_alert({ message: result.message, indicator: "blue" });
					} else {
						frappe.show_alert({
							message: res.irn ? `${__("Registered. IRN:")} ${res.irn}` : __("Submitted to MoR."),
							indicator: "green",
						});
					}
					frm.reload_doc();
				} else {
					// connector may have set Failed/Pending before returning —
					// refresh so the status banner reflects the real state
					frm.reload_doc();
					const detail = frappe.utils.escape_html(res.message || result.message || "");
					frappe.msgprint({
						title: res.eims_status
							? `${__("MoR Registration")} — ${__(res.eims_status)}`
							: __("MoR Registration Failed"),
						message:
							`<div>${__("Invoice")}: <b>${frappe.utils.escape_html(frm.doc.name)}</b>` +
							(res.document_number ? ` · ${__("Doc #")}${frappe.utils.escape_html(String(res.document_number))}` : "") +
							`</div>` +
							(detail
								? `<div style="margin-top:8px;white-space:pre-wrap;word-break:break-word;max-height:260px;overflow:auto;background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:8px 10px;font-size:12px;color:#7f1d1d;">${detail}</div>`
								: "") +
							`<div style="margin-top:8px;" class="text-muted">${__("Full response is stored in Error Log → 'V2 MoR Sales Invoice registration error' / 'EIMS submission rejected'.")}</div>`,
						indicator: "red",
					});
				}
			},
			error: function (r) {
				// framework-level failure (timeout, HTTP 500, auth) — frappe.call
				// only routes here when no _server_messages were handled
				let msg = "";
				try {
					if (r && r._server_messages) {
						msg = JSON.parse(r._server_messages)
							.map((m) => JSON.parse(m).message || "")
							.join(" ");
					}
				} catch (e) {
					msg = "";
				}
				if (!msg && r && r.exc) {
					msg = r.exc.split("\n").filter(Boolean).slice(-1)[0] || "";
				}
				frappe.msgprint({
					title: __("MoR Registration Failed"),
					message: frappe.utils.escape_html(
						msg || __("Request failed — see the browser console and Error Log for details.")
					),
					indicator: "red",
				});
			},
		});
	},

	get_receipt: function (frm) {
		frappe.call({
			method: "ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos.get_invoice_receipt",
			args: { sales_invoice: frm.doc.name },
			freeze: true,
			freeze_message: __("Preparing MoR receipt…"),
			callback: function (r) {
				const res = r.message || {};

				if (res.status === "no_payment_entry") {
					frappe.msgprint({
						title: __("No Payment Entry"),
						message:
							`<div>${__("Invoice")}: <b>${frappe.utils.escape_html(frm.doc.name)}</b></div>` +
							`<div style="margin-top:8px;">${frappe.utils.escape_html(
								res.message || __("A MoR receipt can only be issued after the payment is received and recorded as a Payment Entry.")
							)}</div>`,
						indicator: "orange",
					});
					return;
				}

				if (res.status === "ok" && res.receipt_name) {
					frappe.show_alert({
						message: res.already_active
							? __("Existing receipt opened for review.")
							: __("Receipt document created — review it and click Authorize MoR Receipt."),
						indicator: res.already_active ? "blue" : "green",
					});
					// /app/eims-invoice-receipt/<receipt name>
					frappe.set_route("Form", "EIMS Invoice Receipt", res.receipt_name);
					return;
				}

				if (res.status !== "ok") {
					frappe.msgprint({
						title: __("Receipt Failed"),
						message:
							`<div>${__("Invoice")}: <b>${frappe.utils.escape_html(frm.doc.name)}</b></div>` +
							`<div style="margin-top:8px;white-space:pre-wrap;word-break:break-word;max-height:260px;overflow:auto;background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:8px 10px;font-size:12px;color:#7f1d1d;">${frappe.utils.escape_html(
								res.message || __("Request failed — see Error Log for details.")
							)}</div>`,
						indicator: "red",
					});
				}
			},
			error: function (r) {
				let msg = "";
				try {
					if (r && r._server_messages) {
						msg = JSON.parse(r._server_messages)
							.map((m) => JSON.parse(m).message || "")
							.join(" ");
					}
				} catch (e) {
					msg = "";
				}
				if (!msg && r && r.exc) {
					msg = r.exc.split("\n").filter(Boolean).slice(-1)[0] || "";
				}
				frappe.msgprint({
					title: __("Receipt Failed"),
					message: frappe.utils.escape_html(
						msg || __("Request failed — see the browser console and Error Log for details.")
					),
					indicator: "red",
				});
			},
		});
	},

	verify: function (frm) {
		frappe.call({
			method: "ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos.verify_sales_invoice",
			args: { sales_invoice: frm.doc.name },
			freeze: true,
			freeze_message: __("Verifying with MoR…"),
			callback: function (r) {
				const res = r.message || {};
				const result = res.result || {};
				const html = result.verification_summary || result.html;
				if (res.status === "ok" && html) {
					frm.events.show_dialog(__("MoR Verification Result"), html);
				} else if (res.status === "ok" && result.verification_status) {
					frappe.show_alert({
						message: __(result.verification_status),
						indicator: result.verification_status === "Verified" ? "green" : "red",
					});
				} else {
					frappe.msgprint({
						title: __("Verification Failed"),
						message: frappe.utils.escape_html(result.error_logs || res.message || __("Verification failed.")),
						indicator: "red",
					});
				}
			},
		});
	},

	cancel: function (frm) {
		const d = new frappe.ui.Dialog({
			title: __("Cancel MoR Invoice"),
			fields: [
				{
					fieldname: "cancellation_reasons",
					label: __("Cancellation Reason"),
					fieldtype: "Select",
					options: ["Mistake", "Duplicate", "Fraudulent", "Change of Order", "Others"],
					reqd: 1,
				},
				{ fieldname: "remark", label: __("Remark"), fieldtype: "Small Text" },
			],
			primary_action_label: __("Cancel Invoice"),
			primary_action: function (values) {
				frappe.call({
					method: "ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos.cancel_sales_invoice",
					args: {
						sales_invoice: frm.doc.name,
						cancellation_reasons: values.cancellation_reasons || "Mistake",
						remark: values.remark || "",
					},
					freeze: true,
					freeze_message: __("Cancelling with MoR…"),
					callback: function (r) {
						d.hide();
						const res = r.message || {};
						if (res.status === "ok" && res.result && res.result.status === "Cancelled") {
							frappe.show_alert({ message: __("Invoice cancelled with MoR."), indicator: "green" });
							frm.reload_doc();
						} else {
							frappe.msgprint({
								title: __("Cancellation Failed"),
								message: frappe.utils.escape_html(
									(res.result && res.result.message) || res.message || __("Cancellation failed.")
								),
								indicator: "red",
							});
						}
					},
				});
			},
		});
		d.show();
	},

	show_details: function (frm) {
		frappe.call({
			method: "ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos.get_mor_details",
			args: { sales_invoice: frm.doc.name },
			freeze: true,
			freeze_message: __("Loading MoR details…"),
			callback: function (r) {
				const res = r.message || {};
				if (res.status !== "ok" || !res.details) {
					frappe.msgprint(frappe.utils.escape_html(res.message || __("Unable to load details.")));
					return;
				}
				frm.events.render_details_dialog(frm, res.details, res.receipt, res.verification);
			},
		});
	},

	render_details_dialog: function (frm, d, receipt, verification) {
		const esc = frappe.utils.escape_html;
		const cur = d.currency;
		const status_tone = {
			Registered: "etv2-si-badge-green",
			Pending: "etv2-si-badge-orange",
			Failed: "etv2-si-badge-red",
			Cancelled: "etv2-si-badge-gray",
		}[d.eims_status] || "etv2-si-badge-blue";

		const items = (d.items || [])
			.map(
				(it) => `<tr>
					<td class="etv2-si-muted etv2-si-mono" data-label="${__("Code")}">${esc(it.item_code)}</td>
					<td data-label="${__("Item")}">${esc(it.item_name || "")}</td>
					<td class="etv2-si-right etv2-si-num" data-label="${__("Qty")}">${it.qty} ${esc(it.uom || "")}</td>
					<td class="etv2-si-right etv2-si-num" data-label="${__("Rate")}">${format_currency(it.rate, cur)}</td>
					<td class="etv2-si-right etv2-si-num" data-label="${__("Amount")}"><b>${format_currency(it.amount, cur)}</b></td>
				</tr>`
			)
			.join("");
		const taxes = (d.taxes || [])
			.map(
				(t) => `<tr>
					<td colspan="2" data-label="${__("Tax")}">${esc(t.description || "")}</td>
					<td class="etv2-si-right etv2-si-num" data-label="${__("Rate")}">${t.rate}%</td>
					<td class="etv2-si-right etv2-si-num" data-label="${__("Amount")}">${format_currency(t.tax_amount, cur)}</td>
				</tr>`
			)
			.join("");

		const receipt_html = receipt
			? `<div class="etv2-si-grid">
				<div class="etv2-si-cell"><label>${__("Receipt")}</label><span>${esc(receipt.name)}</span></div>
				<div class="etv2-si-cell"><label>${__("RRN")}</label><span class="etv2-si-mono">${esc(receipt.eims_rrn || "—")}</span></div>
				<div class="etv2-si-cell"><label>${__("Status")}</label><span>${esc(receipt.eims_status || "—")}</span></div>
				<div class="etv2-si-cell"><label>${__("Date")}</label><span>${receipt.receipt_date ? frappe.datetime.str_to_user(receipt.receipt_date) : "—"}</span></div>
			</div>`
			: "";

		const verification_html = verification
			? `<div class="etv2-si-grid">
				<div class="etv2-si-cell"><label>${__("Last Verification")}</label><span>${esc(verification.name)}</span></div>
				<div class="etv2-si-cell"><label>${__("Result")}</label><span>${esc(verification.verification_status || "—")}</span></div>
				<div class="etv2-si-cell"><label>${__("Verified At")}</label><span>${esc(verification.verified_at || "—")}</span></div>
			</div>`
			: "";

		const qr_html = d.qr_code_url
			? `<img src="${esc(d.qr_code_url)}" alt="QR" style="height:90px;border:1px solid #e2e8f0;border-radius:8px;background:#fff;">`
			: "";

		const can_receipt = d.eims_status === "Registered";
		const footer = `
			<div class="etv2-si-actions">
${can_receipt ? `<button type="button" class="btn btn-primary btn-sm etv2-si-fx-receipt">${__("Get Receipt")}</button>` : ""}
${can_receipt ? `<button type="button" class="btn btn-default btn-sm etv2-si-fx-verify">${__("Verify with MoR")}</button>` : ""}
				<button type="button" class="btn btn-default btn-sm etv2-si-fx-open">${__("Open Document")}</button>
			</div>`;

		const html = `
			<div class="etv2-si-detail">
				<div style="display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;
					border-bottom:2px solid #e2e8f0;padding-bottom:8px;margin-bottom:10px;">
					<div style="display:flex;align-items:center;gap:8px;">
						<span style="font-size:15px;font-weight:800;">${esc(d.name)}</span>
						<span class="etv2-si-badge ${status_tone}">${__(d.eims_status)}</span>
					</div>
					<span class="etv2-si-muted" style="font-size:12px;">
						${frappe.datetime.str_to_user(d.posting_date)} ${esc(d.posting_time || "")}
					</span>
				</div>

				<div class="etv2-si-grid">
					<div class="etv2-si-cell"><label>${__("Customer")}</label><span>${esc(d.customer_name || d.customer || "")}</span></div>
					<div class="etv2-si-cell"><label>${__("Cashier")}</label><span>${esc(d.owner || "")}</span></div>
					<div class="etv2-si-cell"><label>${__("Doc #")}</label><span>#${esc(String(d.document_number || "—"))}</span></div>
					${qr_html ? `<div class="etv2-si-cell" style="align-items:center;">${qr_html}</div>` : ""}
					<div class="etv2-si-cell etv2-si-irncell">
						<label>IRN</label>
						<span title="${esc(d.irn)}">${d.irn ? esc(d.irn.slice(0, 26)) + (d.irn.length > 26 ? "…" : "") : "—"}</span>
						${d.irn ? `<button type="button" class="btn btn-xs btn-default etv2-si-dlg-copy" data-irn="${esc(d.irn)}">${__("Copy")}</button>` : ""}
					</div>
				</div>

				${receipt_html}
				${verification_html}

				<h4 class="etv2-si-h4">${__("Items")} <span class="etv2-si-count">${(d.items || []).length}</span></h4>
				<table class="etv2-si-table">
					<thead><tr><th>${__("Code")}</th><th>${__("Item")}</th><th class="etv2-si-right">${__("Qty")}</th><th class="etv2-si-right">${__("Rate")}</th><th class="etv2-si-right">${__("Amount")}</th></tr></thead>
					<tbody>${items || `<tr><td colspan="5" class="etv2-si-muted">${__("No items")}</td></tr>`}</tbody>
				</table>

				${taxes ? `<details><summary class="etv2-si-h4" style="cursor:pointer;">${__("Taxes")} <span class="etv2-si-count">${(d.taxes || []).length}</span></summary>
					<table class="etv2-si-table"><tbody>${taxes}</tbody></table></details>` : ""}

				<div class="etv2-si-totals">
					<div class="etv2-si-total"><label>${__("Net Total")}</label><span>${format_currency(d.net_total, cur)}</span></div>
					<div class="etv2-si-total"><label>${__("Discount")}</label><span>-&nbsp;${format_currency(d.discount_amount, cur)}</span></div>
					<div class="etv2-si-total"><label>${__("Total Tax")}</label><span>${format_currency(d.total_taxes_and_charges, cur)}</span></div>
					<div class="etv2-si-total is-grand"><label>${__("Grand Total")}</label><span>${format_currency(d.grand_total, cur)}</span></div>
					${d.mor_total ? `<div class="etv2-si-total is-grand"><label>${__("Registered @ MoR")}</label><span>${format_currency(d.mor_total, cur)}</span></div>` : ""}
				</div>
				${footer}
			</div>`;

		const dd = new frappe.ui.Dialog({ title: __("MoR Invoice Details"), size: "large" });
		dd.$body.html(html);
		dd.$body.find(".etv2-si-dlg-copy").on("click", function (e) {
			e.stopPropagation();
			frm.events.copy_irn($(e.currentTarget).attr("data-irn"));
		});
		dd.$body.find(".etv2-si-fx-receipt").on("click", () => {
			dd.hide();
			frm.events.get_receipt(frm);
		});
		dd.$body.find(".etv2-si-fx-verify").on("click", () => {
			dd.hide();
			frm.events.verify(frm);
		});
		dd.$body.find(".etv2-si-fx-open").on("click", () => {
			dd.hide();
			frappe.set_route("Form", "Sales Invoice", d.name);
		});
		dd.show();
	},

	copy_irn: function (irn) {
		if (!irn) return;
		if (navigator.clipboard && navigator.clipboard.writeText) {
			navigator.clipboard.writeText(irn).then(
				() => frappe.show_alert({ message: __("IRN copied."), indicator: "green" }),
				() => frappe.show_alert({ message: irn, indicator: "blue" })
			);
		} else {
			frappe.show_alert({ message: irn, indicator: "blue" });
		}
	},

	/* ------------------------------------------------------------------
	   DIALOGS
	   ------------------------------------------------------------------ */
	show_dialog: function (title, html) {
		const dd = new frappe.ui.Dialog({ title, size: "large" });
		dd.$body.html(si_mor_clean_html(html));
		dd.show();
		return dd;
	},
});

/* Shared sanitizer: frappe-rendered documents are full HTML pages that may
   embed scripts — strip scripts and document wrappers before injecting. */
function si_mor_clean_html(html) {
	return String(html || "")
		.replace(/<script[\s\S]*?<\/script>/gi, "")
		.replace(/<\/?(?:!DOCTYPE|html|head|body)[^>]*>/gi, "");
}

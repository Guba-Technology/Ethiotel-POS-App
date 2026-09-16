frappe.ui.form.on("Purchase Invoice", {
	refresh: function (frm) {
		frm.events.setup_withholding_button(frm);
	},

	setup_withholding_button: function (frm) {
		const is_submitted = !frm.is_new() && frm.doc.docstatus === 1;
		if (!is_submitted) return;

		frm.page.remove_inner_button(__("Get Withholding Receipt"), __("MoR Tasks"));

		frm.page.add_inner_button(
			__("Get Withholding Receipt"),
			function () {
				frm.events.get_withholding_receipt(frm);
			},
			__("MoR Tasks")
		);
	},

	get_withholding_receipt: function (frm) {
		frappe.call({
			method: "ethiotel_pos.ethio_telecom_pos_app.doctype.withholding_receipt.withholding_receipt.create_withholding_receipt_for_purchase",
			args: { purchase_invoice: frm.doc.name },
			freeze: true,
			freeze_message: __("Preparing withholding receipt from purchase invoice…"),
			callback: function (r) {
				const res = r.message || {};

				if (res.status === "ok" && res.receipt_name) {
					frappe.show_alert({
						message: res.already_created
							? __("Existing withholding receipt opened for review.")
							: __(
									"Withholding receipt created. Enter the seller-provided IRN & withheld amount, then click Authorize MoR Withholding."
							  ),
						indicator: res.already_created ? "blue" : "green",
					});
					frappe.set_route("Form", "Withholding Receipt", res.receipt_name);
					return;
				}

				frappe.msgprint({
					title: __("Withholding Receipt Failed"),
					message:
						`<div>${__("Purchase Invoice")}: <b>${frappe.utils.escape_html(frm.doc.name)}</b></div>` +
						`<div style="margin-top:8px;white-space:pre-wrap;word-break:break-word;max-height:260px;overflow:auto;background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:8px 10px;font-size:12px;color:#7f1d1d;">${frappe.utils.escape_html(
							res.message || __("Request failed — see Error Log for details.")
						)}</div>`,
					indicator: "red",
				});
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
					title: __("Withholding Receipt Failed"),
					message: frappe.utils.escape_html(
						msg || __("Request failed — see the browser console and Error Log for details.")
					),
					indicator: "red",
				});
			},
		});
	},
});

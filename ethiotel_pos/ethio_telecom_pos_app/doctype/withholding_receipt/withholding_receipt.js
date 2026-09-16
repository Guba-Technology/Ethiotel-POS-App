frappe.ui.form.on("Withholding Receipt", {
    onload: function (frm) {
        frm.events.render_receipt(frm);
    },
    withholding_rate: function (frm) {
        frm.events.recalculate_withholding(frm);
        frm.events.render_receipt(frm);
    },

    pre_tax_amount: function (frm) {
        frm.events.recalculate_withholding(frm);
        frm.events.render_receipt(frm);
    },

    withholding_amount: function (frm) {
        frm.events.recalculate_pre_tax(frm);
        frm.events.render_receipt(frm);
    },

    agent_name: function (frm) {
        frm.events.render_receipt(frm);
    },
    agent_tin: function (frm) {
        frm.events.render_receipt(frm);
    },
    agent_address: function (frm) {
        frm.events.render_receipt(frm);
    },
    seller_name: function (frm) {
        frm.events.render_receipt(frm);
    },
    seller_tin: function (frm) {
        frm.events.render_receipt(frm);
    },
    invoice_date: function (frm) {
        frm.events.render_receipt(frm);
    },
    withholding_type: function (frm) {
        frm.events.render_receipt(frm);
    },
    signatory_name: function (frm) {
        frm.events.render_receipt(frm);
    },
    signatory_title: function (frm) {
        frm.events.render_receipt(frm);
    },
    seal_notes: function (frm) {
        frm.events.render_receipt(frm);
    },

    payment_entry: function (frm) {
        frappe.call({
            doc: frm.doc,
            method: "populate_from_payment_entry",
            args: { payment_entry: frm.doc.payment_entry },
            callback: function (r) {
                const v = r.message || {};
                if (v && typeof v === "object") {
                    frm.set_value("paid_amount", v.paid_amount);
                    frm.set_value("mode_of_payment", v.mode_of_payment);
                    frm.set_value("payment_date", v.payment_date || null);
                    frm.set_value("payment_reference", v.payment_reference);
                    frm.set_value("collector_name", v.collector_name);
                }
                frm.events.render_receipt(frm);
            },
        });
    },
    paid_amount: function (frm) {
        frm.events.render_receipt(frm);
    },
    mode_of_payment: function (frm) {
        frm.events.render_receipt(frm);
    },
    payment_date: function (frm) {
        frm.events.render_receipt(frm);
    },
    payment_reference: function (frm) {
        frm.events.render_receipt(frm);
    },
    collector_name: function (frm) {
        frm.events.render_receipt(frm);
    },

    recalculate_withholding: function (frm) {
        // Forward: gross supply (pre_tax) known -> compute withheld amount.
        if (frm.doc.eims_status === "Active") return;

        const rate = flt(frm.doc.withholding_rate, 6);
        const pre_tax = flt(frm.doc.pre_tax_amount, 2);

        if (pre_tax > 0 && rate > 0) {
            frm.set_value("withholding_amount", Math.round((pre_tax * rate) / 100 * 100) / 100);
        }
    },

    recalculate_pre_tax: function (frm) {
        // Reverse: withheld amount known -> compute the gross supply / pre-tax
        // amount (pre_tax = withheld * 100 / rate). Only updates pre_tax when
        // withholding_amount was changed manually.
        const rate = flt(frm.doc.withholding_rate, 6);
        const wht = flt(frm.doc.withholding_amount, 2);

        if (wht > 0 && rate > 0) {
            frm.set_value("pre_tax_amount", Math.round((wht * 100) / rate * 100) / 100);
        }
    },

    render_receipt: function (frm) {
        frappe.call({
            doc: frm.doc,
            method: "compile_receipt_html",
            callback: function (r) {
                if (r.message && frm.get_field("receipt_viewport")) {
                    frm.get_field("receipt_viewport").html(r.message);
                }
            },
        });
    },

    refresh: function (frm) {
        if (frm.doc.eims_status === "Active") {
            frm.disable_form();
        }

        if (!frm.is_new()) {
            frm.events.render_receipt(frm);
            frm.add_custom_button(__("Print Receipt"), function () {
                frappe.call({
                    doc: frm.doc,
                    method: "compile_receipt_html",
                    callback: function (r) {
                        if (!r.message) return;
                        const w = window.open("", "_blank", "width=520,height=720");
                        if (!w) {
                            frappe.msgprint(__("Please allow pop-ups to print the receipt."));
                            return;
                        }
                        w.document.write(
                            "<!doctype html><html><head><title>Withholding Tax Receipt</title>" +
                            "<style>body{margin:0;padding:24px;background:#fff;}</style>" +
                            "</head><body>" + r.message + "</body></html>"
                        );
                        w.document.close();
                        setTimeout(function () { w.print(); }, 350);
                    },
                });
            });
        }

        if (frm.doc.eims_status !== "Active") {
            frm.add_custom_button(__("Fetch Payment Entry"), function () {
                frappe.call({
                    method: "fetch_default_payment_entry",
                    doc: frm.doc,
                    callback: function (r) {
                        frm.reload_doc();
                    },
                });
            });

            frm.add_custom_button(__("Authorize MoR Withholding"), function () {
                frappe.call({
                    method: "trigger_remote_withholding_receipt",
                    doc: frm.doc,
                    freeze: true,
                    freeze_message: __("Transmitting Withholding Receipt to Revenue Endpoint..."),
                    callback: function (r) {
                        if (r.message && r.message.success) {
                            
                            if (r.message.html && frm.get_field("receipt_viewport")) {
                                frm.get_field("receipt_viewport").html(r.message.html);
                            }
                            frm.reload_doc().then(() => {
                                frappe.show_alert({
                                    message: __("Withholding Receipt Certified and Registered Successfully!"),
                                    indicator: "green",
                                });
                            });
                        } else if (r.message && !r.message.success) {
                            frappe.msgprint({
                                title: __("EIRMS Gateway Rejection"),
                                indicator: "red",
                                message: r.message.message,
                            });
                        }
                    },
                });
            }).addClass("btn-primary");
        }
    },
});

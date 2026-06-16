// Copyright (c) 2026, Guba Technology and contributors
// For license information, please see license.txt

frappe.ui.form.on('EIMS Invoice Cancellation', {
    refresh: function(frm) {
        if (frm.doc.status === 'Cancelled') {
            frm.disable_form();
        }

        if (frm.doc.status !== 'Cancelled') {
            frm.add_custom_button(__('Request Invoice Cancellation '), function() {
                if (!frm.doc.remark) {
                    frappe.msgprint({
                        title: __('Missing Input'),
                        indicator: 'red',
                        message: __('Please write a reason in the Remark section before cancelling.')
                    });
                    return;
                }

                frappe.call({
                    method: 'trigger_remote_cancellation',
                    doc: frm.doc,
                    freeze: true,
                    freeze_message: __('Dispatching Cancellation Request to Ministry of Revenues Node...'),
                    callback: function(r) {
                        if (!r.exc && r.message) {
                            frappe.show_alert({
                                message: __('EIMS Clearance Records Successfully Synced!'),
                                indicator: 'green'
                            });
                            
                            frm.reload_doc();
                        }
                    }
                });
            }).addClass('btn-primary');
        }
    }
});
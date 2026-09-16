// Copyright (c) 2026, Guba Technology and contributors
// For license information, please see license.txt

frappe.ui.form.on('EIMS Manual Invoice', {
    refresh: function(frm) {
        if (frm.doc.status === 'Registered') {
            frm.disable_form();
        }

        if (frm.doc.status !== 'Registered') {
            frm.add_custom_button(__('Submit to EIRMS'), function() {
                if (!frm.doc.items || frm.doc.items.length === 0) {
                    frappe.msgprint({
                        title: __('Missing Input'),
                        indicator: 'orange',
                        message: __('Add at least one item before submitting.')
                    });
                    return;
                }
                if (frm.is_dirty()) {
                    frappe.throw(__('Please save the document before submitting to EIRMS.'));
                }
                frappe.confirm(
                    __('Submit this manual invoice (issued during registration outage) to EIRMS within the 72-hour window?'),
                    function() {
                        frappe.call({
                            method: 'submit_to_eirms',
                            doc: frm.doc,
                            freeze: true,
                            freeze_message: __('Registering with EIRMS...'),
                            callback: function(r) {
                                if (!r.exc && r.message) {
                                    if (r.message.status === 'Registered') {
                                        frappe.show_alert({
                                            message: __('Manual invoice registered with EIRMS!'),
                                            indicator: 'green'
                                        });
                                    } else {
                                        frappe.show_alert({
                                            message: __('Submission failed: ' + (r.message.message || 'see log')),
                                            indicator: 'red'
                                        });
                                    }
                                    frm.reload_doc();
                                }
                            }
                        });
                    }
                );
            }).addClass('btn-primary');
        }
    }
});
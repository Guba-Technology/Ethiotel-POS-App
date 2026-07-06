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
                if (frm.is_dirty()) {
                    frappe.throw(__('Please save the document before requesting cancellation.'));
                }
                frappe.confirm(
                    __('Are you sure you want to request invoice cancellation?'),
                    function() {
                        frappe.call({
                            method: 'trigger_remote_cancellation',
                            doc: frm.doc,
                            freeze: true,
                            freeze_message: __('Requesting Invoice Cancellation...'),
                            callback: function(r) {
                                if (!r.exc && r.message) {
                                    frappe.show_alert({
                                        message: __('Invoice Cancellation Request Sent!'),
                                        indicator: 'green'
                                    });
                                    
                                    frm.reload_doc();
                                }
                            }
                        });
                    },
                    function() {
                        frappe.show_alert({
                            message: __('Invoice Cancellation Request Cancelled!'),
                            indicator: 'red'
                        });
                    }
                );
            }).addClass('btn-primary');
        }
              
        },
        is_bulk_cancellation: function(frm) {
            if (frm.doc.is_bulk_cancellation) {
                frm.doc.set_value('sales_invoice', '');
                frm.doc.set_value('irn', '');
                frm.doc.set_df_property('invoice_list', 'reqd', 1);
            }
            else{
                frm.doc.set_df_property('invoice_list', 'reqd', 0);
                frm.clear_table('invoice_list');
                frm.set_df_property('sales_invoice', 'reqd', 1);
                frm.set_df_property('irn', 'reqd', 1);
            }
        }
    
});
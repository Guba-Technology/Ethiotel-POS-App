// Copyright (c) 2026, Guba Technology and contributors
// For license information, please see license.txt

frappe.ui.form.on('EIMS Setting', {
    validate: function(frm) {
        // Count how many rows have "is_default" checked
        let default_rows = (frm.doc.client_data_list || []).filter(row => row.is_default == 1);
        
        if (default_rows.length === 0) {
            frappe.msgprint(__('You must mark exactly one row as default in the Client Data List.'));
            frappe.validated = false;
        } else if (default_rows.length > 1) {
            frappe.msgprint(__('Only one row can be marked as default.'));
            frappe.validated = false;
        }
    },
    refresh: function(frm) {
        if (frm.doc.sms_enabled) {
            frm.add_custom_button(__('Send Test SMS'), function() {
                frappe.prompt([
                    { fieldname: 'phone', label: __('Recipient Phone'), fieldtype: 'Data', reqd: 1 },
                    { fieldname: 'message', label: __('Message'), fieldtype: 'Small Text' }
                ], function(values) {
                    frappe.call({
                        method: 'ethiotel_pos.ethio_telecom_pos_app.doctype.eims_setting.eims_setting.send_test_sms',
                        args: { phone: values.phone, message: values.message },
                        callback: function(r) {
                            if (r.message && r.message.sent) {
                                frappe.msgprint(__('Test SMS sent successfully.'));
                            } else {
                                let reason = (r.message && r.message.reason) || 'unknown';
                                frappe.msgprint(__('Test SMS failed: {0}', [reason]));
                            }
                        }
                    });
                }, __('Send Test SMS'));
            }, __('SMS'));
        }
    }
});

frappe.ui.form.on('Client Data', {
    is_default: function(frm, cdt, cdn) {
        let current_row = locals[cdt][cdn];
        
        if (current_row.is_default == 1) {
            $.each(frm.doc.client_data_list || [], function(i, row) {
                if (row.name !== current_row.name && row.is_default == 1) {
                    frappe.model.set_value(row.doctype, row.name, 'is_default', 0);
                }
            });
            
            frm.set_value('default_system_number', current_row.system_number);
        } else {
            // If the user unchecks a row, verify if any default remains
            let default_exists = (frm.doc.client_data_list || []).some(row => row.is_default == 1);
            if (!default_exists) {
                frm.set_value('default_system_number', '');
            }
        }
    },
    
    system_number: function(frm, cdt, cdn) {
        let current_row = locals[cdt][cdn];
        // If the system number is updated on the active default row, update the parent field too
        if (current_row.is_default == 1) {
            frm.set_value('default_system_number', current_row.system_number);
        }
    },
    
    client_data_list_remove: function(frm) {
        // If the default row gets deleted, clear or update the parent field
        let default_row = (frm.doc.client_data_list || []).find(row => row.is_default == 1);
        if (default_row) {
            frm.set_value('default_system_number', default_row.system_number);
        } else {
            frm.set_value('default_system_number', '');
        }
    }
});

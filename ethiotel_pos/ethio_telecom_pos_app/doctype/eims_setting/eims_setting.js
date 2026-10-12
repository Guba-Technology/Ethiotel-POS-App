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

        // Account Config needs exactly one default EIMS tax code: it is the
        // fallback used when an invoice line carries no tax code of its own.
        let tax_rows = (frm.doc.tax_code_config || []);
        if (tax_rows.length) {
            let tax_defaults = tax_rows.filter(row => row.is_default == 1);
            if (tax_defaults.length === 0) {
                frappe.msgprint(__('You must mark exactly one row as Default in the Account Config table.'));
                frappe.validated = false;
            } else if (tax_defaults.length > 1) {
                frappe.msgprint(__('Only one tax code can be marked as Default.'));
                frappe.validated = false;
            } else if (!tax_defaults[0].item_tax_template) {
                // The Default row is applied to invoice items that carry no tax
                // of their own, and it is applied through an Item Tax Template
                // so ERPNext posts the tax and recalculates the total.
                frappe.msgprint(
                    __('Row {0}: the Default tax code needs an Item Tax Template.', [tax_defaults[0].idx]),
                    __('EIMS Tax Code Mapping Error')
                );
                frappe.validated = false;
            }
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

frappe.ui.form.on('EIMS Tax Code Config', {
    // Checking a row clears the flag on every other row, so the table can
    // never end up with two defaults. Unchecking the last one is allowed on
    // screen so the user can re-pick, but saving is blocked until exactly one
    // default remains.
    is_default: function(frm, cdt, cdn) {
        let current_row = locals[cdt][cdn];
        if (current_row.is_default != 1) {
            return;
        }
        (frm.doc.tax_code_config || []).forEach(function(row) {
            if (row.name !== current_row.name && row.is_default == 1) {
                frappe.model.set_value(row.doctype, row.name, 'is_default', 0);
            }
        });

        // Point the new Default at a template that taxes the same account, so
        // the field is usually already correct. The user can still change it.
        if (!current_row.item_tax_template) {
            suggest_template_for_account(current_row);
        }
    },

    account: function(frm, cdt, cdn) {
        let current_row = locals[cdt][cdn];
        if (current_row.is_default == 1) {
            suggest_template_for_account(current_row);
        }
    }
});

// Pre-fill the Default row's Item Tax Template. Only a template that actually
// taxes this row's account (and rates it like the Account does) is offered,
// because that pairing is what EIMS Setting validation requires.
function suggest_template_for_account(row) {
    let account = row.account;
    if (!account) {
        return;
    }
    frappe.call({
        method: 'ethiotel_pos.ethio_telecom_pos_app.doctype.eims_setting.eims_setting.item_tax_templates_for_account',
        args: { account: account },
        callback: function(r) {
            let templates = (r.message && r.message.templates) || [];
            if (templates.length === 1) {
                frappe.model.set_value(row.doctype, row.name, 'item_tax_template', templates[0]);
            }
        }
    });
}

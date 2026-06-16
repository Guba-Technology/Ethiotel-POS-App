// Copyright (c) 2026, Guba Technology and contributors
// For license information, please see license.txt

frappe.ui.form.on('Invoice Registration', {
    setup: function(frm) {
        // Enforce strict link queries for manual overrides inside rows
        frm.set_query('sales_invoice', 'sales_invoice_list', function() {
            return {
                filters: {
                    'docstatus': 1,
                    'custom_eims_status': ['in', ['Not Submitted', 'Failed', 'Pending','']]
                }
            };
        });
    },

    refresh: function(frm) {
        toggle_grid_restrictions(frm);
    },

    invoice_registration_type: function(frm) {
        auto_populate_filtered_invoices(frm);
    }
});

frappe.ui.form.on('Invoice List', {
    sales_invoice: function(frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        
        if (row.sales_invoice) {
            frappe.model.set_value(cdt, cdn, 'status', 'Pending');
            
            // Safety Guard: Force row truncation if accidentally manipulated in Single mode
            if (frm.doc.invoice_registration_type === 'Single' && frm.doc.sales_invoice_list.length > 1) {
                console.warn("=== EIMS LOG: Single mode violation caught! Dropping extra lines ===");
                frappe.msgprint({
                    title: __('Validation Warning'),
                    indicator: 'orange',
                    message: __('Single Registration profiles are restricted to exactly 1 record. Extra rows dropped.')
                });
                
                frm.doc.sales_invoice_list = frm.doc.sales_invoice_list.filter(d => d.name === cdn);
                frm.refresh_field('sales_invoice_list');
            }
        }
    },
    
    sales_invoice_list_add: function(frm, cdt, cdn) {
        if (frm.doc.invoice_registration_type === 'Single' && frm.doc.sales_invoice_list.length > 1) {
            console.warn("=== EIMS LOG: Blocked row addition in Single mode ===");
            frappe.model.clear_doc(cdt, cdn);
            frappe.msgprint(__('Cannot append multiple rows while Registration Type is set to Single.'));
        }
    }
});


function toggle_grid_restrictions(frm) {
    let grid = frm.get_field('sales_invoice_list').grid;
    
    if (frm.doc.invoice_registration_type === 'Single') {
        grid.cannot_add_rows = true;
        grid.grid_buttons.hide('.btn-add-row');
    } else {
        grid.cannot_add_rows = false;
        grid.grid_buttons.show('.btn-add-row');
    }
    frm.refresh_field('sales_invoice_list');
}


function auto_populate_filtered_invoices(frm) {
    let registration_type = frm.doc.invoice_registration_type;
    
    if (!registration_type) {
        frm.clear_table('sales_invoice_list');
        frm.refresh_field('sales_invoice_list');
        return;
    }

    let max_records = (registration_type === 'Single') ? 1 : 50;

    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Sales Invoice',
            filters: {
                'docstatus': 1,
                'custom_eims_status': ['in', ['Not Submitted', 'Failed', 'Pending','']]
            },
            fields: ['name'],
            limit_page_length: max_records,
            order_by: 'creation desc'
        },
        freeze: true,
        freeze_message: __(`Fetching unsubmitted invoices for ${registration_type} queue...`),
        callback: function(r) {
            
            frm.clear_table('sales_invoice_list');
            
            if (r.message && r.message.length > 0) {
                
                r.message.forEach((invoice, index) => {
                    let child = frm.add_child('sales_invoice_list');
                    child.sales_invoice = invoice.name;
                    child.status = 'Pending';
                    
                });
                
                frappe.show_alert({
                    message: __(`Successfully loaded ${r.message.length} invoices into your workspace.`),
                    indicator: 'green'
                });
            } else {
                frappe.show_alert({
                    message: __('No pending unsubmitted invoices found.'),
                    indicator: 'blue'
                });
            }
            
            frm.fields_dict['sales_invoice_list'].grid.refresh();
            toggle_grid_restrictions(frm);
        }
    });
}
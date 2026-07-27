frappe.pages['lite-manager'].on_page_load = function(wrapper) {
    // 1. Setup the page
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'System Pruning Manager',
        single_column: true
    });

    frappe.require('/assets/ethiotel_pos/js/prunning_gui.js', function() {
        if (window.init_pruning_manager) {
            window.init_pruning_manager(wrapper, page);
        } else {
            frappe.msgprint(__("Script loaded but Manager not initialized. Check console."));
        }
    });
}
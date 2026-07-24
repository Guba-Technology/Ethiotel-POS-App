frappe.ui.form.on("Sales Invoice", {
    refresh: function(frm) {
        if (frm.fields_dict.disable_rounded_total) {
            console.log("disable_rounded_total exists");
            
            frm.set_value("disable_rounded_total", 1);
            
            frm.set_df_property("disable_rounded_total", "read_only", 1); 
            
            frm.refresh_field("disable_rounded_total");
        }
    }
});

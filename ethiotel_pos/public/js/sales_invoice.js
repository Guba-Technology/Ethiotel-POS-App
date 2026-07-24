frappe.ui.form.on("Sales Invoice", {
    onload: function(frm) {
       //check if disable_rounded_total field  exists
        if(frm.fields_dict.disable_rounded_total){
            console.log("disable_rounded_total exists");
            frm.set_df_property("disable_rounded_total","checked",1);
        frm.set_df_property("disable_rounded_total", "read_only", 1); 
        }
       
    }
});
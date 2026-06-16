import frappe
from frappe import _
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice

class CustomSalesInvoice(SalesInvoice):
    def before_save(self):
        super().before_save()
        
        if not self.custom_document_number or int(self.custom_document_number) == 0:
            result = frappe.db.sql("""
                SELECT MAX(CAST(custom_document_number AS UNSIGNED)) 
                FROM `tabSales Invoice`
            """)
            cdn = result[0][0] if result and result[0][0] is not None else 0
            self.custom_document_number = cdn + 1

        allowed_tax_types = [
            "TOT10", "TOT2", "VAT15", "VWHT", "TWHT", "VATEX", 
            "VATWH", "WHOP2", "WTHOI", "VAT0", "VWTH"
        ]
        
        for tax in self.get("taxes"):
            if tax.account_head:
                tax_type = frappe.db.get_value("Account", tax.account_head, "account_name")
                
                if tax_type not in allowed_tax_types:
                    frappe.msgprint(
                        _("Row #{0}: Tax account type '{1}' (from Account: {2}) is not valid for EIMS submission. Allowed types are: {3}")
                        .format(tax.idx, tax_type, tax.account_head, ", ".join(allowed_tax_types))
                    )

        valid_uoms = ["LTR", "MTR", "101", "PCS", "ROL", "MTS", "PKG", "SET", "KLG"]
        invalid_uom_alerts = []

        for item in self.get("items"):
            current_uom = str(item.uom or "").strip().upper()
            if current_uom and current_uom not in valid_uoms:
                invalid_uom_alerts.append(f"Row #{item.idx} ({item.item_code}): '{item.uom}'")

        if invalid_uom_alerts:
            frappe.msgprint(
                msg=_(
                    "<b>Notice:</b> The following items use non-standard EIMS units of measure. "
                    "The system will default them to 'PCS' during automated transmission:<br><br>{0} Allowed unit of measures are {1}."
                ).format("<br>".join(invalid_uom_alerts), ", ".join(valid_uoms)),
                title=_("EIMS Unit Verification"),
                indicator="orange",
                alert=True
            )
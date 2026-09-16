# Copyright (c) 2026, Guba Technology and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

TAX_RATE_DEFAULTS = {"VAT15": 15.0, "VAT0": 0.0}


class EIMSManualInvoice(Document):
    def before_save(self):
        self.recompute_totals()
        self._validate_buyer_tin()

    def recompute_totals(self):
        pre_tax_total = 0.0
        tax_total = 0.0
        grand_total = 0.0
        for row in self.items:
            qty = float(row.quantity or 1)
            unit_price = float(row.unit_price or 0)
            discount = float(row.discount_amount or 0)
            pre_tax = round(qty * unit_price - discount, 2)
            if pre_tax < 0:
                frappe.throw(
                    _("Line '{0}': pre-tax value cannot be negative. Check unit price vs discount.").format(
                        row.item_description
                    )
                )
            tax_rate = float(row.tax_rate or 0)
            tax_amount = round(pre_tax * tax_rate / 100.0, 2)
            row.pre_tax_value = pre_tax
            row.tax_amount = tax_amount
            row.total_line_amount = round(pre_tax + tax_amount, 2)
            pre_tax_total += pre_tax
            tax_total += tax_amount
            grand_total += row.total_line_amount
        self.pre_tax_total = round(pre_tax_total, 2)
        self.tax_total = round(tax_total, 2)
        self.grand_total = round(grand_total, 2)

    def _validate_buyer_tin(self):
        tin = (self.buyer_tin or "").strip()
        if not tin:
            return
        clean = "".join(ch for ch in tin if ch.isdigit())
        if len(clean) < 10 or len(clean) > 20:
            frappe.throw(
                _("Buyer TIN must be purely numeric and between 10 and 20 digits. Found: '{0}'").format(tin),
                title=_("EIMS Schema Error: Invalid TIN"),
            )

    @frappe.whitelist()
    def submit_to_eirms(self):
        if not frappe.has_permission("EIMS Manual Invoice", "write", doc=self):
            frappe.throw(_("Not permitted to submit this manual invoice to EIRMS."), frappe.PermissionError)

        from ethiotel_pos.eims_connector import EIMSConnector

        connector = EIMSConnector()
        result = connector.submit_manual_invoice(self.name)
        return result
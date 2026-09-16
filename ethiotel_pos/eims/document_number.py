import re

import frappe


class EIMSConnectorDocNum:
    def _lookup_irn_for_doc_num(self, doc_num):
        if doc_num <= 0:
            return ""
        db_res = frappe.db.sql(
            """SELECT custom_irn FROM `tabSales Invoice`
               WHERE custom_document_number = %s AND docstatus = 1 LIMIT 1""",
            doc_num, as_dict=1
        )
        if db_res:
            return db_res[0].get("custom_irn") or ""
        db_res = frappe.db.sql(
            """SELECT custom_mor_irn FROM `tabPOS Invoice`
               WHERE custom_document_number = %s AND docstatus = 1 LIMIT 1""",
            doc_num, as_dict=1
        )
        if db_res:
            return db_res[0].get("custom_mor_irn") or ""
        return ""

    def _lookup_irn_for_invoice(self, invoice_name):
        """Return the EIRMS IRN of a registered Sales Invoice or POS Invoice
        (used for CRE/DEB note references), or None when it is not registered."""
        if not invoice_name:
            return None
        for doctype, irn_field in (("Sales Invoice", "custom_irn"),
                                   ("POS Invoice", "custom_mor_irn")):
            if frappe.db.exists(doctype, invoice_name):
                irn = frappe.db.get_value(doctype, invoice_name, irn_field)
                if irn:
                    return irn
        return None

    def _peek_next_document_number(self):
       
        row = frappe.db.sql(
            """SELECT value FROM `tabSingles`
            WHERE doctype = 'EIMS Setting' AND field = 'last_document_number'"""
        )
        last_num = int(row[0][0]) if row and row[0][0] else 0
        next_from_setting = last_num + 1

        max_si = frappe.db.sql(
            """SELECT MAX(custom_document_number) FROM `tabSales Invoice`
               WHERE custom_document_number IS NOT NULL AND custom_document_number > 0"""
        )
        max_pos = frappe.db.sql(
            """SELECT MAX(custom_document_number) FROM `tabPOS Invoice`
               WHERE custom_document_number IS NOT NULL AND custom_document_number > 0"""
        )
        max_used = max(
            int(max_si[0][0] or 0) if max_si else 0,
            int(max_pos[0][0] or 0) if max_pos else 0,
        )

        # Only use invoice max if it's a reasonable increment over the setting
        # (prevents a single corrupt entry like 901 from hijacking the sequence).
        REASONABLE_GAP = 1000
        if max_used > last_num and (max_used - last_num) <= REASONABLE_GAP:
            return max(next_from_setting, max_used + 1)

        # Fallback: authoritative setting wins
        return next_from_setting

    def _parse_expected_doc_num(self, response_text):
       
        match = re.search(r"expected\s*:\s*(\d+)", response_text or "", re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    def _commit_document_number(self, doc_num):
    
        doc_num = int(doc_num)
        exists = frappe.db.sql(
            """SELECT 1 FROM `tabSingles`
            WHERE doctype = 'EIMS Setting' AND field = 'last_document_number'"""
        )
        if exists:
            frappe.db.sql(
                """UPDATE `tabSingles` SET value = %s
                WHERE doctype = 'EIMS Setting' AND field = 'last_document_number'""",
                (doc_num,),
            )
        else:
            frappe.db.sql(
                """INSERT INTO `tabSingles` (doctype, field, value)
                VALUES ('EIMS Setting', 'last_document_number', %s)""",
                (doc_num,),
            )
        frappe.db.commit()
        self.settings.last_document_number = doc_num

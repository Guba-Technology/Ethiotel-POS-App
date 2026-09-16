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
        """Read-only peek at the next MoR document number: the highest of
        last_document_number + 1 and every document number ever recorded on
        a Sales Invoice or POS Invoice, plus one. This guarantees a fresh
        submission never reuses a number that was already sent to MoR.
        Does NOT reserve or persist anything. The caller must call
        _commit_document_number() only after MoR confirms a successful
        registration for that number."""
        row = frappe.db.sql(
            """SELECT value FROM `tabSingles`
            WHERE doctype = 'EIMS Setting' AND field = 'last_document_number'"""
        )
        last_num = int(row[0][0]) if row and row[0][0] else 0
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
        return max(last_num + 1, max_used + 1)

    def _parse_expected_doc_num(self, response_text):
        """Extract the MoR-expected next document number from a rule
        validation error, e.g. 'Document number is not in correct sequence
        expected : 107'. Returns None when the error carries no number."""
        match = re.search(r"expected\s*:\s*(\d+)", response_text or "", re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    def _commit_document_number(self, doc_num):
        """Persist doc_num as the new EIMS Setting.last_document_number.
        Called only after MoR confirms successful registration for that
        number, so a failed/rejected/pending submission never burns a
        document number."""
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

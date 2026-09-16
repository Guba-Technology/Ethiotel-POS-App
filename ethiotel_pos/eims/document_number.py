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

    def _active_client_last_doc(self):
        """The per-system document counter of the currently default Client Data
        row. Each System Number has its own MoR sequence; switching the default
        switches the sequence too. Returns None when the active client has no
        tracked counter yet - in that case callers should fall back to the
        synced parent last_document_number."""
        rows = frappe.db.sql(
            """SELECT last_document_number FROM `tabClient Data`
               WHERE parent = %s AND parentfield = 'client_data_list' AND is_default = 1""",
            self.settings.name,
        )
        if rows and rows[0][0]:
            return int(rows[0][0])
        return None

    def _peek_next_document_number(self):
        """Read-only peek at the next MoR document number.

        The active Client Data row's per-system counter (synced to the parent
        EIMS Setting.last_document_number) is the single source of truth.
        Invoice document numbers are NOT considered because they cross System
        Number boundaries: an invoice registered under another System Number
        must not advance this system's sequence. Sequence drift (e.g. a lost
        response) is recovered by self-healing via MoR's 'expected : NNN'
        response.

        Does NOT reserve or persist anything. The caller must call
        _commit_document_number() only after MoR confirms a successful
        registration for that number."""
        last_num = self._active_client_last_doc()
        if last_num is None:
            row = frappe.db.sql(
                """SELECT value FROM `tabSingles`
                WHERE doctype = 'EIMS Setting' AND field = 'last_document_number'"""
            )
            last_num = int(row[0][0]) if row and row[0][0] else 0
        return last_num + 1

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
        # Keep the active System Number's per-system counter in sync so the
        # number follows the default Client Data row when it is switched later.
        rows = frappe.db.sql(
            """SELECT name FROM `tabClient Data`
               WHERE parent = %s AND parentfield = 'client_data_list' AND is_default = 1""",
            self.settings.name,
        )
        if rows:
            frappe.db.sql(
                """UPDATE `tabClient Data` SET last_document_number = %s WHERE name = %s""",
                (doc_num, rows[0][0]),
            )
        frappe.db.commit()
        self.settings.last_document_number = doc_num

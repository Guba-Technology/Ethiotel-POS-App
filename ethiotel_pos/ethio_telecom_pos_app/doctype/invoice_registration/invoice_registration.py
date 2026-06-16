# Copyright (c) 2026, Guba Technology and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.model.document import Document
from ethiotel_pos.eims_connector import EIMSConnector

class InvoiceRegistration(Document):
    def before_save(self):
        if self.invoice_registration_type == "Single":
            self.process_single_registration()
        elif self.invoice_registration_type == "Bulk":
            self.process_bulk_registration()

    def process_single_registration(self):
        connector = EIMSConnector()
        results = []
        
        for row in self.sales_invoice_list:
            if row.sales_invoice:
                res = connector.submit_single_invoice(row.sales_invoice)
                row.status = res.get("status", "Rule Error")
                
                results.append({
                    "invoice": row.sales_invoice,
                    "status": res.get("status"),
                    "details": res.get("message")
                })
        
        self.responces = json.dumps(results, indent=4)

    def process_bulk_registration(self):
        connector = EIMSConnector()
        
        invoices_to_submit = []
        skipped_logs = []
        results_map = {}
        
        for row in self.sales_invoice_list:
            if row.sales_invoice:
                if row.status == "Transmitted":
                    skipped_logs.append(f"[{row.sales_invoice}] Skipped -> Already Transmitted")
                    results_map[row.sales_invoice] = {"status": "Transmitted", "message": "Already Transmitted"}
                else:
                    # Fetch document sequence number for accurate sorting
                    doc_num = frappe.db.get_value("Sales Invoice", row.sales_invoice, "custom_document_number")
                    try:
                        doc_num_int = int(doc_num) if doc_num else 1
                    except ValueError:
                        doc_num_int = 1
                    invoices_to_submit.append({"name": row.sales_invoice, "doc_num": doc_num_int})
        
        invoices_to_submit.sort(key=lambda x: x["doc_num"])
        sorted_names = [item["name"] for item in invoices_to_submit]
        
        if sorted_names:
            batch_execution = connector.submit_bulk_invoices(sorted_names)
            batch_results = batch_execution.get("results", {})
            results_map.update(batch_results)
            
            submission_logs = batch_execution.get("message", "")
            if skipped_logs:
                self.responces = f"{submission_logs}\n\nSkipped Items:\n" + "\n".join(skipped_logs)
            else:
                self.responces = submission_logs
        else:
            self.responces = "Iterative Batch Processing Complete.\nAll listed invoices are already marked as Transmitted.\n\nSkipped Items:\n" + "\n".join(skipped_logs)
            
        for row in self.sales_invoice_list:
            if row.sales_invoice and row.sales_invoice in results_map:
                row.status = results_map[row.sales_invoice].get("status", "Rule Error")
                
        frappe.db.commit()
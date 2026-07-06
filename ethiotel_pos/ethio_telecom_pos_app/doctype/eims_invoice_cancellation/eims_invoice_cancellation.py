# Copyright (c) 2026, Guba Technology and contributors
# For license information, please see license.txt

import json
import requests
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime
from ethiotel_pos.eims_connector import EIMSConnector


CANCELLATION_REASON_MAP = {
    "Order cancelled": "1",
    "DuplicateData entry": "2",
    "Mistake": "3",
    "Others": "4"
}


class EIMSInvoiceCancellation(Document):
    def before_save(self):
        # Prevent manual edits to already-cancelled records
        if self.status == "Cancelled" and not self.is_new():
            existing_status = frappe.db.get_value("EIMS Invoice Cancellation", self.name, "status")
            if existing_status == "Cancelled":
                frappe.throw(_("Verified EIMS audit records are immutable and cannot be manually altered."))

    def map_failure(self, failure_reason):
        """Standardizes internal failure flags upon general connectivity anomalies"""
        self.status = "Failed"
        self.status_code = str(failure_reason)

    @frappe.whitelist()
    def trigger_remote_cancellation(self):

        if self.is_bulk_cancellation:
            return self.trigger_bulk_cancellation()
        return self.trigger_single_cancellation()

 
    def trigger_single_cancellation(self):
        if not self.irn:
            frappe.throw(_("Please provide an Invoice Reference Number (IRN) before attempting cancellation."))

        if not getattr(self, "remark", None):
            frappe.throw(_("A cancellation remark must be specified before dispatching protocol context."))

        connector = EIMSConnector()

        try:
            token = connector.get_valid_token()
            base_url = connector.settings.base_url.strip().replace('"', '').replace("'", "").rstrip('/')
            url = f"{base_url}/v1/cancel"
            headers = self._build_headers(connector, token)

            # MoR expects payload variables to be capitalized precisely ("Irn", "ReasonCode", "Remark")
            payload_data = json.dumps({
                "Irn": self.irn.strip(),
                "ReasonCode": CANCELLATION_REASON_MAP.get(self.cancellation_reasons, "1"),
                "Remark": self.remark.strip()
            })

            response = requests.post(url, data=payload_data, headers=headers, timeout=15)

            try:
                res_data = response.json()
            except ValueError:
                err_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                self.map_failure(err_msg)
                self.cancelled_at = now_datetime()
                self.save()
                frappe.db.commit()
                return self.get_return_payload()

            if response.status_code == 200 and res_data.get("statusCode") == 200:
                self.status = "Cancelled"
                body = res_data.get("body", {})
                self.status_code = f"Success: Cancelled on {body.get('cancellationDate', 'Unknown Date')}"
                self._mark_sales_invoice_cancelled(self.sales_invoice)
            else:
                self.status = "Failed"
                self.status_code = self._extract_error_message(res_data)

        except requests.exceptions.RequestException as e:
            self.map_failure(f"Network transport level connection exception: {str(e)}")

        self.cancelled_at = now_datetime()
        self.save()
        frappe.db.commit()

        return self.get_return_payload()

    def trigger_bulk_cancellation(self):
        if not self.invoice_list:
            frappe.throw(_(
                "Please add at least one row to the Invoice List before attempting bulk cancellation."
            ))

        if not getattr(self, "remark", None):
            frappe.throw(_("A cancellation remark must be specified before dispatching protocol context."))

        rows_missing_irn = [
            (row.sales_invoice or row.name) for row in self.invoice_list if not (row.irn or "").strip()
        ]
        if rows_missing_irn:
            frappe.throw(_(
                "The following rows in Invoice List are missing an IRN and cannot be submitted "
                "for cancellation: {0}"
            ).format(", ".join(rows_missing_irn)))

        connector = EIMSConnector()
        reason_code = CANCELLATION_REASON_MAP.get(self.cancellation_reasons, "1")
        remark_text = self.remark.strip()

        try:
            token = connector.get_valid_token()
            base_url = connector.settings.base_url.strip().replace('"', '').replace("'", "").rstrip('/')
            url = f"{base_url}/v1/bulkCancel"
            headers = self._build_headers(connector, token)


            bulk_payload = [
                {
                    "Irn": row.irn.strip(),
                    "ReasonCode": reason_code,
                    "Remark": remark_text
                }
                for row in self.invoice_list
            ]

            response = requests.post(
                url, data=json.dumps(bulk_payload), headers=headers, timeout=30
            )

            try:
                res_data = response.json()
            except ValueError:
                err_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                for row in self.invoice_list:
                    row.status = "Failed"
                self.map_failure(err_msg)
                self.cancelled_at = now_datetime()
                self.save()
                frappe.db.commit()
                return self.get_return_payload()

            self._apply_bulk_results(response.status_code, res_data)

        except requests.exceptions.RequestException as e:
            for row in self.invoice_list:
                row.status = "Failed"
            self.map_failure(f"Network transport level connection exception: {str(e)}")

        self.cancelled_at = now_datetime()
        self.save()
        frappe.db.commit()

        return self.get_return_payload()

    def _apply_bulk_results(self, http_status, res_data):

        body = res_data.get("body") if isinstance(res_data, dict) else res_data

        results_by_irn = {}
        if isinstance(body, list):
            for item in body:
                if isinstance(item, dict):
                    key = (item.get("Irn") or item.get("irn") or "").strip()
                    if key:
                        results_by_irn[key] = item
        elif isinstance(body, dict):
            key = (body.get("Irn") or body.get("irn") or "").strip()
            if key:
                results_by_irn[key] = body

        overall_accepted = http_status == 200 and isinstance(res_data, dict) and res_data.get("statusCode") == 200

        success_count = 0
        failure_count = 0

        for row in self.invoice_list:
            row_irn = (row.irn or "").strip()
            item = results_by_irn.get(row_irn)

            if item is not None:
                if self._is_item_success(item):
                    row.status = "Cancelled"
                    success_count += 1
                    self._mark_sales_invoice_cancelled(row.sales_invoice)
                else:
                    row.status = "Failed"
                    failure_count += 1
            elif overall_accepted:

                row.status = "Cancelled"
                success_count += 1
                self._mark_sales_invoice_cancelled(row.sales_invoice)
            else:
                row.status = "Failed"
                failure_count += 1

        if failure_count == 0:
            self.status = "Cancelled"
            self.status_code = f"Success: {success_count} invoice(s) cancelled."
        elif success_count == 0:
            self.status = "Failed"
            self.status_code = self._extract_error_message(res_data)
        else:
            self.status = "Failed"
            self.status_code = (
                f"Partially completed: {success_count} cancelled, {failure_count} failed. "
                f"See Invoice List rows for per-invoice detail."
            )

    def _is_item_success(self, item):
        if not isinstance(item, dict):
            return False
        status_value = item.get("status") or item.get("Status") or ""
        return str(status_value).strip().upper() == "C"

    def _extract_error_message(self, res_data):
        if not isinstance(res_data, dict):
            return json.dumps(res_data)

        body_content = res_data.get("body")
        msg_header = res_data.get("message", "Processing_Error")

        if isinstance(body_content, dict) and "msg" in body_content:
            return f"[{msg_header}] {body_content.get('msg')}"

        if isinstance(body_content, list) and len(body_content) > 0:
            first_item = body_content[0]
            if isinstance(first_item, dict) and "message" in first_item:
                return f"[{msg_header}] {first_item.get('message')}"
            return f"[{msg_header}] {str(first_item)}"

        return f"[{msg_header}] {json.dumps(res_data)}"

    def _build_headers(self, connector, token):
        return {
            "Authorization": f"Bearer {token}",
            "apikey": connector.settings.get_password("api_key"),
            "Content-Type": "application/json",
            "Accept": "*/*",
            "User-Agent": "ERPNext-EthiotelPOS-Integration/1.0",
            "Connection": "keep-alive"
        }

    def _mark_sales_invoice_cancelled(self, sales_invoice):
        if not sales_invoice:
            return
        try:
            frappe.db.set_value(
                "Sales Invoice", sales_invoice, "custom_eims_status", "Cancelled", update_modified=True
            )
        except Exception:
            frappe.log_error(
                message=frappe.get_traceback(),
                title=f"EIMS Cancellation: failed to update Sales Invoice {sales_invoice}"
            )

    def get_return_payload(self):
        """Helper to safely serialize the database record into standard response payloads"""
        payload = {
            "status": self.status,
            "status_code": self.status_code,
            "cancelled_at": self.cancelled_at
        }
        if self.is_bulk_cancellation:
            payload["results"] = [
                {"sales_invoice": row.sales_invoice, "irn": row.irn, "status": row.status}
                for row in self.invoice_list
            ]
        return payload
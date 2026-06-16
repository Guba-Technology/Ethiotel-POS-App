# Copyright (c) 2026, Guba Technology and contributors
# For license information, please see license.txt

import json
import requests
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime
from ethiotel_pos.eims_connector import EIMSConnector


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
        """Dispatches cancellation commands to MoR node and updates local state fields"""
        if not self.irn:
            frappe.throw(_("Please provide an Invoice Reference Number (IRN) before attempting cancellation."))
            
        if not getattr(self, "remark", None):
            frappe.throw(_("A cancellation remark must be specified before dispatching protocol context."))

        connector = EIMSConnector()
        
        try:
            token = connector.get_valid_token()
            base_url = connector.settings.base_url.strip().replace('"', '').replace("'", "").rstrip('/')
            url = f"{base_url}/v1/cancel"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "apikey": connector.settings.get_password("api_key"),
                "Content-Type": "application/json",
                "Accept": "*/*",
                "User-Agent": "PostmanRuntime/7.32.3",
                "Connection": "keep-alive"
            }

            # MoR expects payload variables to be capitalized precisely ("Irn", "ReasonCode", "Remark")
            payload_data = json.dumps({
                "Irn": self.irn.strip(),
                "ReasonCode": "1",
                "Remark": self.remark.strip()
            })
            
            response = requests.post(url, data=payload_data, headers=headers, timeout=15)

            try:
                res_data = response.json()
            except ValueError:
                # Fallback handler for non-JSON returns
                err_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                self.map_failure(err_msg)
                self.cancelled_at = now_datetime()
                self.save()
                frappe.db.commit()
                return self.get_return_payload()

            # Process responses dynamically based on MoR gateway status codes
            if response.status_code == 200 and res_data.get("statusCode") == 200:
                self.status = "Cancelled"
                # Store the exact cancellation date string passed back by the gateway node
                body = res_data.get("body", {})
                self.status_code = f"Success: Cancelled on {body.get('cancellationDate', 'Unknown Date')}"
            
            else:
                # Parse out API Gateway errors cleanly based on response schema signatures
                self.status = "Failed"
                body_content = res_data.get("body")
                msg_header = res_data.get("message", "Processing_Error")

                if isinstance(body_content, dict) and "msg" in body_content:
                    # Case 1: Processing Error e.g., {"msg": "IRN already Canceled."}
                    self.status_code = f"[{msg_header}] {body_content.get('msg')}"
                
                elif isinstance(body_content, list) and len(body_content) > 0:
                    first_item = body_content[0]
                    if isinstance(first_item, dict) and "message" in first_item:
                        # Case 2: Schema Error validations
                        self.status_code = f"[{msg_header}] {first_item.get('message')}"
                    else:
                        # Case 3: Rule Validation Exception lists
                        self.status_code = f"[{msg_header}] {str(first_item)}"
                
                else:
                    # Case 4: General fallback catch-all
                    self.status_code = f"[{msg_header}] {json.dumps(res_data)}"

        except requests.exceptions.RequestException as e:
            self.map_failure(f"Network transport level connection exception: {str(e)}")

        # Timestamp tracking updates and write back properties straight to DB layout row
        self.cancelled_at = now_datetime()
        self.save()
        frappe.db.commit()

        return self.get_return_payload()

    def get_return_payload(self):
        """Helper to safely serialize the database record into standard response payloads"""
        return {
            "status": self.status,
            "status_code": self.status_code,
            "cancelled_at": self.cancelled_at
        }
# Copyright (c) 2026, Guba Technology and contributors
# For license information, please see license.txt

import json
import requests
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import global_date_format, fmt_money, now_datetime
from ethiotel_pos.eims_connector import EIMSConnector


class EIMSInvoiceVerification(Document):
    def before_save(self):
        # Prevent manual edits to already-verified records
        if self.verification_status == "Verified" and not self.is_new():
            existing_status = frappe.db.get_value("EIMS Invoice Verification", self.name, "verification_status")
            if existing_status == "Verified":
                frappe.throw(_("Verified EIMS audit records are immutable and cannot be manually altered."))

    @frappe.whitelist()
    def trigger_remote_verification(self):
        """Executes verification payload against MoR by reusing the EIMSConnector structure"""
        if not self.irn:
            frappe.throw(_("Please provide an Invoice Reference Number (IRN) before verifying."))

        connector = EIMSConnector()
        html_dashboard = ""

        try:
            token = connector.get_valid_token()
            base_url = connector.settings.base_url.strip().replace('"', '').replace("'", "").rstrip('/')
            url = f"{base_url}/v1/verify"

            headers = {
                "Authorization": f"Bearer {token}",
                "apikey": connector.settings.get_password("api_key"),
                "Content-Type": "application/json",
                "Accept": "*/*",
                "User-Agent": "PostmanRuntime/7.32.3",
                "Connection": "keep-alive"
            }

            payload_data = json.dumps({"irn": self.irn.strip()})
            response = requests.post(url, data=payload_data, headers=headers, timeout=15)

            try:
                res_data = response.json()
            except ValueError:
                # Non-JSON response handling
                err_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                self.map_failure(err_msg)
                self.verified_at = now_datetime()
                self.save()
                frappe.db.commit()
                
                return {
                    "verification_status": self.verification_status,
                    "error_logs": self.error_logs,
                    "verified_at": self.verified_at,
                    "verification_summary": f"""
                        <div class="alert alert-danger text-center" style="margin-top: 15px; padding: 15px; border-radius: 4px;">
                            <i class="fa fa-exclamation-triangle"></i> <b>Verification Check Failed:</b> {err_msg}
                        </div>
                    """
                }

            if response.status_code == 200 and res_data.get("statusCode") == 200:
                body = res_data.get("body", {})
                self.map_indexable_fields(body)
                html_dashboard = self.compile_html_dashboard(body)
                self.report_data = html_dashboard
            else:
                reason = res_data.get("message")
                if isinstance(res_data.get("details"), list) and len(res_data.get("details")) > 0:
                    reason = res_data["details"][0].get("errorMessage", reason)

                reason = reason or "Gateway routing rejected verification parameters."
                self.map_failure(reason)
                html_dashboard = f"""
                    <div class="alert alert-danger text-center" style="margin-top: 15px; padding: 15px; border-radius: 4px;">
                        <i class="fa fa-exclamation-triangle"></i> <b>Verification Check Failed:</b> {reason}
                    </div>
                """

        except requests.exceptions.RequestException as e:
            reason = f"Network transport level connection exception: {str(e)}"
            self.map_failure(reason)
            html_dashboard = f"""
                <div class="alert alert-danger text-center" style="margin-top: 15px; padding: 15px; border-radius: 4px;">
                    <i class="fa fa-exclamation-triangle"></i> <b>Verification Check Failed:</b> {reason}
                </div>
            """

        # stamp verification time and persist structural values
        self.verified_at = now_datetime()
        self.save()
        frappe.db.commit()

        # Build a safe data payload including our calculated HTML string
        return {
            "verification_status": self.verification_status,
            "mor_doc_number": self.mor_doc_number,
            "buyer_tin": self.buyer_tin,
            "total_value": self.total_value,
            "error_logs": self.error_logs,
            "verified_at": self.verified_at,
            "verification_summary": html_dashboard
        }

    def map_indexable_fields(self, body):
        """Extracts and stores critical top-level metadata for standard reports"""
        self.verification_status = "Verified"
        self.error_logs = ""  # Clear historical exception traces on fresh success

        self.mor_doc_number = body.get("DocumentDetails", {}).get("DocumentNumber")
        self.buyer_tin = body.get("BuyerDetails", {}).get("Tin")
        self.total_value = body.get("ValueDetails", {}).get("TotalValue", 0.0)

    def map_failure(self, failure_reason):
        """Cleans state fields on verification failure"""
        reason_str = str(failure_reason)
        self.verification_status = "Not Registered" if "not registered" in reason_str.lower() else "Failed"

        self.error_logs = reason_str
        self.mor_doc_number = None
        self.buyer_tin = None
        self.total_value = 0

    def compile_html_dashboard(self, body):
        seller = body.get("SellerDetails", {})
        buyer = body.get("BuyerDetails", {})
        vals = body.get("ValueDetails", {})
        items = body.get("ItemList", [])

        item_rows = ""
        for item in items:
            item_rows += f"""
                <tr>
                    <td class="text-center">{item.get('LineNumber', '')}</td>
                    <td><b>{item.get('ItemCode', '')}</b><br><small class="text-muted">{item.get('ProductDescription', '')}</small></td>
                    <td class="text-right">{item.get('Quantity', 0)} {item.get('Unit', 'PCS')}</td>
                    <td class="text-right">{fmt_money(item.get('UnitPrice', 0), currency=vals.get('InvoiceCurrency', 'ETB'))}</td>
                    <td class="text-center"><span class="label label-info">{item.get('TaxCode', '')}</span></td>
                    <td class="text-right">{fmt_money(item.get('TaxAmount', 0), currency=vals.get('InvoiceCurrency', 'ETB'))}</td>
                    <td class="text-right font-weight-bold">{fmt_money(item.get('TotalLineAmount', 0), currency=vals.get('InvoiceCurrency', 'ETB'))}</td>
                </tr>
            """

        # Inline CSS for screen and print. Print CSS preserves colors and layout.
        # The print button has id "eims-print-btn" and the printable container has id "eims-verified-container".
        html = f"""
        <div id="eims-verified-wrapper" style="font-family: 'Helvetica Neue', Arial, sans-serif;">
            <div style="display:flex; justify-content:flex-end; margin-bottom:8px;">
                <button id="eims-print-btn" style="background:#28a745; color:#fff; border:none; padding:8px 14px; border-radius:4px; cursor:pointer; font-weight:600;">
                    <i class="fa fa-print" style="margin-right:6px;"></i> Print Receipt
                </button>
            </div>

            <div id="eims-verified-container" class="eims-verified-container" style="background-color: #fff; border: 1px solid #d1d8dd; border-radius: 6px; padding: 20px; margin-top: 10px; font-family: inherit; color: #1f2d3d;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #28a745; padding-bottom: 12px; margin-bottom: 20px;">
                    <div>
                        <h3 style="margin: 0; color: #1f2d3d; font-weight: 600;">EIMS INVOICE VERIFICATION</h3>
                        <small class="text-muted">Type: <b>{body.get('TransactionType', 'B2C')}</b> | Document Ref: #{body.get('DocumentDetails', {}).get('DocumentNumber', 'N/A')}</small>
                    </div>
                    <div style="background-color: #28a745; color: white; padding: 6px 16px; border-radius: 20px; font-weight: bold; font-size: 13px; letter-spacing: 0.5px;">
                        <i class="fa fa-check-circle"></i> MoR AUTHENTICATED
                    </div>
                </div>
                <div class="row" style="margin-bottom: 20px;">
                    <div class="col-sm-6" style="border-right: 1px dashed #d1d8dd;">
                        <h6 class="text-muted" style="text-transform: uppercase; font-weight: bold; margin-bottom: 6px;">Supplier/Seller</h6>
                        <p style="margin: 0; font-size: 14px;"><b>{seller.get('LegalName', '')}</b></p>
                        <p style="margin: 0; font-size: 13px;" class="text-muted">TIN: {seller.get('Tin', 'N/A')} | VAT: {seller.get('VatNumber', 'N/A')}</p>
                        <p style="margin: 0; font-size: 13px;" class="text-muted">Tel: {seller.get('Phone', 'N/A')} | {seller.get('Email', '')}</p>
                    </div>
                    <div class="col-sm-6" style="padding-left: 25px;">
                        <h6 class="text-muted" style="text-transform: uppercase; font-weight: bold; margin-bottom: 6px;">Purchaser/Buyer</h6>
                        <p style="margin: 0; font-size: 14px;"><b>{buyer.get('LegalName', 'Cash Customer / Unregistered')}</b></p>
                        <p style="margin: 0; font-size: 13px;" class="text-muted">TIN: {buyer.get('Tin', 'N/A')} | ID Type: {buyer.get('IdType', 'N/A')}</p>
                        <p style="margin: 0; font-size: 13px;" class="text-muted">Contact: {buyer.get('Phone', 'N/A')}</p>
                    </div>
                </div>
                <div class="table-responsive" style="margin-bottom: 20px;">
                    <table class="table table-bordered table-condensed" style="font-size: 13px; width:100%; border-collapse:collapse;">
                        <thead>
                            <tr style="background-color: #f8f9fa;">
                                <th class="text-center" style="width: 40px; padding:8px; border:1px solid #e9ecef;">#</th>
                                <th style="padding:8px; border:1px solid #e9ecef;">Description / Code</th>
                                <th class="text-right" style="width: 100px; padding:8px; border:1px solid #e9ecef;">Qty</th>
                                <th class="text-right" style="width: 120px; padding:8px; border:1px solid #e9ecef;">Rate</th>
                                <th class="text-center" style="width: 90px; padding:8px; border:1px solid #e9ecef;">Tax Type</th>
                                <th class="text-right" style="width: 110px; padding:8px; border:1px solid #e9ecef;">Tax Amt</th>
                                <th class="text-right" style="width: 130px; padding:8px; border:1px solid #e9ecef;">Net Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            {item_rows}
                        </tbody>
                    </table>
                </div>
                <div style="display: flex; justify-content: flex-end;">
                    <div style="width: 320px; background: #f8f9fa; border: 1px solid #d1d8dd; border-radius: 4px; padding: 12px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 13px;">
                            <span class="text-muted">Pre-Tax Value:</span>
                            <span>{fmt_money(vals.get('TotalValue', 0) - vals.get('TaxValue', 0), currency=vals.get('InvoiceCurrency', 'ETB'))}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 13px; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px;">
                            <span class="text-muted">Assessed Value Add Tax (VAT):</span>
                            <span class="text-danger">+{fmt_money(vals.get('TaxValue', 0), currency=vals.get('InvoiceCurrency', 'ETB'))}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; font-weight: bold; font-size: 15px; color: #111;">
                            <span>Grand Total:</span>
                            <span class="text-success">{fmt_money(vals.get('TotalValue', 0), currency=vals.get('InvoiceCurrency', 'ETB'))}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        """
        return html
import json
import requests
import frappe
from datetime import datetime
from frappe import _
from frappe.model.document import Document
from frappe.utils import fmt_money
from ethiotel_pos.eims_connector import EIMSConnector
# import now_datetime
from frappe.utils import now_datetime
class EIMSInvoiceReceipt(Document):
    def before_save(self):
        if self.eims_status == "Active" and not self.is_new():
            existing_status = frappe.db.get_value("EIMS Invoice Receipt", self.name, "eims_status")
            if existing_status == "Active":
                frappe.throw(_("Authenticated MoR EIMS receipts are immutable and cannot be altered."))\
        # auto-increement receipt_counter
        if self.receipt_counter == 0:
            # get maximum receipt counter
            max_counter = frappe.db.get_value("EIMS Invoice Receipt", None, "max(receipt_counter)", as_dict=1)
            self.receipt_counter = max_counter.get("max(receipt_counter)") + 1 if max_counter else 1
    @frappe.whitelist()
    def fetch_payment_entry_details(self):
        if not self.payment_entry:
            return

        pe = frappe.get_doc("Payment Entry", self.payment_entry)
        eims_settings = frappe.get_single("EIMS Setting")
        
        self.party_type = pe.party_type
        self.party = pe.party
        self.party_name = pe.party_name
        self.mode_of_payment = pe.mode_of_payment.upper()
        self.collected_amount = pe.paid_amount
        self.currency = pe.paid_from_account_currency
        self.receipt_date = pe.posting_date
        self.transaction_number = pe.reference_no or ""
        self.account_number = pe.bank_account_no or ""
        self.payment_provider = pe.bank or "Bank"
        self.collector_name = pe.owner
        self.seller_tin = eims_settings.seller_tin
        self.source_system_type = eims_settings.system_type
        self.source_system_no = eims_settings.system_number

        self.invoices_covered = []
        for ref in pe.references:
            if ref.reference_doctype == "Sales Invoice":
                inv_doc = frappe.get_doc("Sales Invoice", ref.reference_name)
                if not inv_doc or not inv_doc.custom_irn:
                    frappe.throw(_("Sales Invoice {0} does not have an EIMS IRN (custom_irn) identifier.").format(ref.reference_name))
                
                self.eims_rrn = inv_doc.custom_irn
                self.append("invoices_covered", {
                    "invoice_irn": inv_doc.custom_irn,
                    "payment_coverage": "FULL" if ref.allocated_amount >= ref.total_amount else "PARTIAL",
                    "invoice_paid_amount": ref.allocated_amount,
                    "discount_amount": 0.0,
                    "remaining_amount": ref.outstanding_amount,
                    "total_amount": ref.total_amount
                })

    @frappe.whitelist()
    def trigger_remote_receipt_generation(self):
        if self.eims_status == "Active":
            frappe.throw(_("This transaction receipt has already been successfully authorized by MoR."))

        self.fetch_payment_entry_details()
        connector = EIMSConnector()
        
        try:
            token = connector.get_valid_token()
            base_url = connector.settings.base_url.strip().replace('"', '').replace("'", "").rstrip('/')
            url = f"{base_url}/v1/receipt/sales"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "apikey": connector.settings.get_password("api_key"),
                "Content-Type": "application/json",
                "Accept": "*/*"
            }

            invoice_payload = []
            for item in self.invoices_covered:
                invoice_payload.append({
                    "InvoiceIRN": item.invoice_irn,
                    "PaymentCoverage": item.payment_coverage,
                    "InvoicePaidAmount": float(item.invoice_paid_amount),
                    "DiscountAmount": float(item.discount_amount) if item.discount_amount else None,
                    "RemainingAmount": float(item.remaining_amount) if item.remaining_amount else None,
                    "TotalAmount": float(item.total_amount)
                })

            payload_data = json.dumps({
                "ReceiptNumber": self.receipt_number,
                "ReceiptType": self.receipt_type or "Sales Receipts",
                "Reason": self.remark or "Payment for goods purchased",
				"ReceiptDate": now_datetime().replace(microsecond=0).isoformat() + "Z",               
    			"ReceiptCounter": str(self.receipt_counter or 1),
                "ManualReceiptNumber": str(self.receipt_counter or 1),
                "SourceSystemType": self.source_system_type,
                "SourceSystemNumber": self.source_system_no,
                "ReceiptCurrency": self.receipt_currency or "ETB",
                "ExchangeRate": None,
                "CollectedAmount": float(self.collected_amount),
                "SellerTIN": self.seller_tin,
                "Invoices": invoice_payload,
                "TransactionDetails": {
                    "ModeOfPayment": self.mode_of_payment or "CASH",
                    "ChequeNumber": getattr(self, "cheque_number", None),
                    "CPONumber": getattr(self, "cpo_number", None),
                    "DocumentNumber": None,
                    "CollectorName": self.collector_name or "Cashier",
                    "PaymentServiceProvider": self.payment_provider or "Bank",
                    "AccountNumber": self.account_number,
                    "TransactionNumber": self.transaction_number
                }
            })

            response = requests.post(url, data=payload_data, headers=headers, timeout=15)
            res_data = response.json()

            if response.status_code == 200 and res_data.get("statusCode") == 200:
                body = res_data.get("body", {})
                api_status = body.get("status")
                
                if api_status == "A":
                    self.eims_status = "Active"
                else:
                    self.eims_status = api_status or "Active"

                self.eims_rrn = body.get("rrn")
                self.qr_code_base64 = body.get("qr")
                self.response_log = json.dumps(res_data, indent=4)
                
                self.save()
                frappe.db.commit()
                
                return {
                    "success": True,
                    "status": self.eims_status,
                    "rrn": self.eims_rrn,
                    "html": self.compile_receipt_html()
                }
            else:
                self.response_log = json.dumps(res_data, indent=4)
                self.save()
                frappe.db.commit()
                return {
                    "success": False,
                    "message": res_data.get("message", "Gateway rejection.")
                }

        except Exception as e:
            frappe.log_error(message=frappe.get_traceback(), title="EIMS Receipt Dispatch Failure")
            frappe.throw(_(f"Critical System Processing Exception: {str(e)}"))

    @frappe.whitelist()
    def compile_receipt_html(self):
        """
        Return a complete, self-contained HTML fragment for the receipt.
        All attributes are read via getattr with safe defaults to avoid undeclared names.
        """
        # Safe money formatter: use existing fmt_money if present, otherwise fallback.
        fmt_money_fn = globals().get("fmt_money")
        if not callable(fmt_money_fn):
            def fmt_money_fn(amount, currency="ETB"):
                try:
                    amt = float(amount or 0)
                except Exception:
                    amt = 0.0
                return f"{currency} {amt:,.2f}"

        # Safely read attributes from self with defaults
        currency = getattr(self, "currency", None) or "ETB"
        qr_code_base64 = getattr(self, "qr_code_base64", "") or ""
        receipt_number = getattr(self, "receipt_number", "N/A")
        receipt_counter = getattr(self, "receipt_counter", "N/A")
        seller_tin = getattr(self, "seller_tin", "N/A")
        source_system_no = getattr(self, "source_system_no", "N/A")
        source_system_type = getattr(self, "source_system_type", "N/A")
        party_name = getattr(self, "party_name", None) or "Unregistered Walk-in Client"
        party = getattr(self, "party", None) or "N/A"
        mode_of_payment = getattr(self, "mode_of_payment", "N/A")
        payment_provider = getattr(self, "payment_provider", None) or "N/A"
        account_number = getattr(self, "account_number", None) or "N/A"
        transaction_number = getattr(self, "transaction_number", None) or "N/A"
        collector_name = getattr(self, "collector_name", None) or "System Cashier"
        eims_rrn = getattr(self, "eims_rrn", "N/A")
        collected_amount = getattr(self, "collected_amount", 0.0)

        # invoices_covered: ensure it's iterable
        invoices_covered = getattr(self, "invoices_covered", []) or []

        # If no QR code, return a minimal message (explicit)
        if not qr_code_base64:
            return (
                "<div style='font-family: Arial, Helvetica, sans-serif; padding:20px;'>"
                "<strong>No QR code available for this receipt.</strong>"
                "</div>"
            )

        # Build invoice rows safely
        invoice_rows = ""
        for inv in invoices_covered:
            if isinstance(inv, dict):
                invoice_irn = inv.get("invoice_irn", "N/A")
                payment_coverage = inv.get("payment_coverage", "N/A")
                total_amount = inv.get("total_amount", 0.0)
                invoice_paid_amount = inv.get("invoice_paid_amount", 0.0)
            else:
                invoice_irn = getattr(inv, "invoice_irn", "N/A")
                payment_coverage = getattr(inv, "payment_coverage", "N/A")
                total_amount = getattr(inv, "total_amount", 0.0)
                invoice_paid_amount = getattr(inv, "invoice_paid_amount", 0.0)

            invoice_rows += f"""
                <tr>
                    <td style="padding:8px; border-bottom:1px solid #e2e8f0; font-family:monospace; font-size:11px;">{invoice_irn}</td>
                    <td style="padding:8px; border-bottom:1px solid #e2e8f0; text-align:center;">
                        <span style="display:inline-block; background:#e6ffed; color:#1f8a3d; padding:4px 8px; border-radius:12px; font-size:11px; font-weight:600;">
                            {payment_coverage}
                        </span>
                    </td>
                    <td style="padding:8px; border-bottom:1px solid #e2e8f0; text-align:right;">{fmt_money_fn(total_amount, currency=currency)}</td>
                    <td style="padding:8px; border-bottom:1px solid #e2e8f0; text-align:right; font-weight:700;">{fmt_money_fn(invoice_paid_amount, currency=currency)}</td>
                </tr>
            """

        # Timestamp (safe access to frappe.utils.now_datetime)
        generated_timestamp = ""
        if "frappe" in globals() and getattr(frappe, "utils", None):
            try:
                generated_timestamp = frappe.utils.now_datetime()
            except Exception:
                generated_timestamp = ""

        # Compose full HTML fragment (no popup toolbar here; popup will add toolbar)
        html = f"""
        <div id="receipt-root" style="font-family: Arial, Helvetica, sans-serif; color:#1f2d3d; max-width:900px; margin:0 auto; padding:18px;">
        <style>
            /* Basic styling */
            #receipt-root h3 {{ margin:0 0 6px 0; font-size:20px; }}
            #receipt-root h6 {{ margin:0 0 6px 0; font-size:12px; color:#718096; text-transform:uppercase; letter-spacing:0.6px; }}
            #receipt-root p {{ margin:0 0 6px 0; font-size:13px; color:#2d3748; }}
            #receipt-root table {{ width:100%; border-collapse:collapse; font-size:13px; }}
            #receipt-root th, #receipt-root td {{ padding:8px; border:1px solid #cbd5e0; }}
            #receipt-root thead tr {{ background:#edf2f7; }}
        </style>

        <div style="background:#fff; border:1px solid #d1d8dd; border-radius:8px; padding:20px;">
            <!-- Header -->
            <div style="display:flex; justify-content:space-between; align-items:flex-start; border-bottom:3px solid #28a745; padding-bottom:12px; margin-bottom:16px;">
            <div>
                <h3 style="color:#1f2d3d; font-weight:700;">EIMS Electronic Official Receipt</h3>
                <div style="font-size:13px; color:#4a5568;">No: <strong>{receipt_number}</strong> &nbsp;|&nbsp; Counter Ref: <strong>#{receipt_counter}</strong></div>
            </div>
            <div style="text-align:right;">
                <div style="display:inline-block; background:#28a745; color:#fff; padding:6px 12px; border-radius:20px; font-weight:700; font-size:12px;">
                MoR SIGNED RECEIPT
                </div>
                <div style="font-size:11px; color:#718096; margin-top:6px;">Status Reference: Active</div>
            </div>
            </div>

            <!-- Issuer & Payer -->
            <div style="display:flex; gap:20px; margin-bottom:18px; background:#f8f9fa; padding:14px; border-radius:6px; border:1px solid #e2e8f0;">
            <div style="flex:1;">
                <h6>Issuer Identification</h6>
                <p><strong>Seller TIN:</strong> {seller_tin}</p>
                <p><strong>System Node:</strong> {source_system_no} ({source_system_type})</p>
            </div>
            <div style="flex:1; border-left:1px dashed #cbd5e0; padding-left:16px;">
                <h6>Payer Identification</h6>
                <p><strong>Customer:</strong> {party_name}</p>
                <p><strong>Account Reference:</strong> {party}</p>
            </div>
            </div>

            <!-- Allocated Settlement Breakdown -->
            <div style="margin-bottom:18px;">
            <h6>Allocated Settlement Breakdown</h6>
            <table aria-label="Allocated Settlement Breakdown">
                <thead>
                <tr>
                    <th style="text-align:left;">Target Invoice IRN Reference Link</th>
                    <th style="text-align:center; width:120px;">Coverage</th>
                    <th style="text-align:right; width:140px;">Invoice Total</th>
                    <th style="text-align:right; width:140px;">Paid Settlement</th>
                </tr>
                </thead>
                <tbody>
                {invoice_rows if invoice_rows else '<tr><td colspan="4" style="padding:12px; text-align:center; color:#718096;">No invoices allocated</td></tr>'}
                </tbody>
            </table>
            </div>

            <!-- Channel Processing & Summary -->
            <div style="display:flex; justify-content:space-between; align-items:flex-end; gap:20px; background:#fafafa; border:1px solid #e2e8f0; padding:14px; border-radius:6px;">
            <div style="flex:1;">
                <h6>Channel Processing Details</h6>
                <p><strong>Payment Gateway Mode:</strong> {mode_of_payment}</p>
                <p><strong>Merchant Intermediary Provider:</strong> {payment_provider}</p>
                <p><strong>Bank Account Ref / Trans ID:</strong> {account_number} / {transaction_number}</p>
                <p><strong>Authorized Operator:</strong> {collector_name}</p>
                <div style="margin-top:10px; font-size:11px; font-family:monospace; color:#4a5568; word-break:break-all; max-width:480px;">
                <strong>RRN Hash:</strong> {eims_rrn}
                </div>
            </div>

            <div style="width:220px; text-align:right;">
                <div style="border:1px solid #cbd5e0; padding:8px; background:#fff; border-radius:6px; display:inline-block;">
                <img src="data:image/png;base64,{qr_code_base64}" alt="MoR EIMS Sign Verification QR" style="width:110px; height:110px; display:block;" />
                </div>
                <div style="margin-top:8px; font-size:12px; color:#718096;">Total Funds Cleared</div>
                <div style="font-size:20px; font-weight:800; color:#28a745;">{fmt_money_fn(collected_amount, currency=currency)}</div>
            </div>
            </div>

            <!-- Footer -->
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:18px;">
            <div style="font-size:12px; color:#718096;">
                <div>Receipt generated by EIMS</div>
                <div style="margin-top:6px;">Generated on: <strong>{generated_timestamp}</strong></div>
            </div>
            </div>
        </div>
        </div>
        """

        return html


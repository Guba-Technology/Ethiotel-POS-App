import json

import requests

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt
from frappe.utils import get_datetime

from ethiotel_pos.eims_connector import EIMSConnector, resolve_mor_payment_mode
from ethiotel_pos.eims.payload import sum_withholding


class WithholdingReceipt(Document):

    def validate(self):
        # Withholding values are never negative on submission.
        for fld in ("withholding_rate", "pre_tax_amount", "withholding_amount", "exchange_rate"):
            val = self.get(fld)
            if val is None:
                continue
            try:
                if float(val) < 0:
                    setattr(self, fld, abs(float(val)))
            except (TypeError, ValueError):
                pass

    def before_save(self):
        if not self.eims_status:
            self.eims_status = "Pending"
        if not self.receipt_number:
            self.receipt_number = f"WHT-{self.name or ''}"
        if not self.receipt_date:
            self.receipt_date = frappe.utils.now_datetime().replace(microsecond=0)

    def _settings(self):
        return frappe.get_single("EIMS Setting")

    @frappe.whitelist()
    def populate_from_purchase_invoice(self, purchase_invoice):
        """Fill the withholding receipt from a Purchase Invoice.

        On the purchase side the roles are reversed:
          * Withholding Agent (your info) = this Company (the buyer).
          * Seller / Withholdee = the Supplier being paid.

        The MoR InvoiceIRN and the Withheld Amount are provided by the
        seller, so they are deliberately NOT derived here — the user enters
        them on the receipt (the JS then back-calculates the gross supply /
        pre-tax amount from the withheld amount)."""
        pi = frappe.get_doc("Purchase Invoice", purchase_invoice)
        if pi.docstatus != 1:
            frappe.throw(_("Purchase Invoice {0} is not submitted.").format(purchase_invoice))

        self.invoice_number = pi.name or ""
        self.invoice_date = getattr(pi, "posting_date", None)
        self.currency = pi.currency or "ETB"
        self.exchange_rate = pi.conversion_rate

        settings = self._settings()

        # ---- Withholding Agent = this Company (buyer) ----------------------
        company = frappe.get_doc("Company", pi.company) if pi.company else None
        if company:
            self.agent_name = (
                company.get("custom_seller_legal_name") or company.get("company_name") or ""
            )
            self.agent_tin = (settings.get("seller_tin") or company.get("tax_id") or "").strip()
            addr_parts = [
                str(company.get(k) or "").strip()
                for k in ("custom_city", "custom_sub_city", "custom_zone", "custom_kebele", "custom_house_number", "custom_country")
            ]
            self.agent_address = ", ".join([p for p in addr_parts if p])
        else:
            self.agent_name = ""
            self.agent_tin = ""
            self.agent_address = ""

        # ---- Seller / Withholdee = Supplier --------------------------------
        self.seller_name = pi.supplier_name or pi.supplier or ""
        supplier_tin = ""
        if pi.supplier:
            supplier_tin = frappe.db.get_value("Supplier", pi.supplier, "tax_id") or ""
        self.seller_tin = str(supplier_tin or "").strip()

        # ---- Source system ------------------------------------------------
        default_client = settings.get("client_data_list") or []
        if default_client:
            client = default_client[0]
            self.source_system_type = (client.get("system_type") or "POS").strip()
            self.source_system_number = (client.get("system_number") or "").strip()

        # ---- Withholding type / rate from the purchase tax table -----------
        transaction_wht, income_wht = sum_withholding(pi, "")
        rate = transaction_wht or income_wht
        self.withholding_type = (
            "TWTH" if transaction_wht else ("IWTH" if income_wht else (self.withholding_type or "TWTH"))
        )
        self.withholding_rate = abs(float(rate or 0.0))

        # Gross supply = net total. The IRN and the withheld amount are left
        # blank for the seller to provide; entering the withheld amount on the
        # form back-calculates the pre-tax figure.
        self.pre_tax_amount = abs(float(pi.net_total or 0.0))
        self.reason = _("Withholding on purchase invoice {0}").format(pi.name)
        self.receipt_number = f"WHT-P-{pi.name}"

        # Auto-link the Payment Entry that settled this purchase invoice and
        # pull the payment reference details (most recent one wins).
        pe_rows = frappe.db.get_all(
            "Payment Entry Reference",
            filters={"reference_doctype": "Purchase Invoice", "reference_name": pi.name},
            fields=["parent", "creation"],
            order_by="creation desc",
            limit=1,
        )
        if pe_rows:
            pe_name = pe_rows[0].parent
            self.payment_entry = pe_name
            self.populate_from_payment_entry(pe_name)
        return True

    @frappe.whitelist()
    def populate_from_payment_entry(self, payment_entry):
        """Pull payment reference details from a Payment Entry (optional).
        Returns the populated values so the client can refresh them."""
        if not payment_entry:
            self.payment_entry = ""
            return {"payment_entry": "", "paid_amount": 0, "mode_of_payment": "", "payment_date": None, "payment_reference": "", "collector_name": ""}
        pe = frappe.get_doc("Payment Entry", payment_entry)
        self.payment_entry = pe.name
        self.paid_amount = pe.paid_amount
        self.mode_of_payment = resolve_mor_payment_mode(pe.mode_of_payment) or pe.mode_of_payment
        self.payment_date = getattr(pe, "posting_date", None)
        self.payment_reference = pe.reference_no or ""
        self.collector_name = pe.party_name or pe.party or ""
        return {
            "payment_entry": self.payment_entry,
            "paid_amount": self.paid_amount,
            "mode_of_payment": self.mode_of_payment,
            "payment_date": str(self.payment_date or ""),
            "payment_reference": self.payment_reference,
            "collector_name": self.collector_name,
        }

    @frappe.whitelist()
    def fetch_default_payment_entry(self):
        """Locate the Payment Entry that settled the linked purchase invoice
        (invoice_number), populate and persist the payment reference fields."""
        pi_name = (self.invoice_number or "").strip()
        if not pi_name or not frappe.db.exists("Purchase Invoice", pi_name):
            return {"status": "no_invoice"}
        if self.payment_entry:
            self.populate_from_payment_entry(self.payment_entry)
            self.save(ignore_permissions=True)
            return {"status": "ok", "payment_entry": self.payment_entry}
        pe_rows = frappe.db.get_all(
            "Payment Entry Reference",
            filters={"reference_doctype": "Purchase Invoice", "reference_name": pi_name},
            fields=["parent", "creation"],
            order_by="creation desc",
            limit=1,
        )
        if not pe_rows:
            return {"status": "no_payment_entry"}
        self.populate_from_payment_entry(pe_rows[0].parent)
        self.save(ignore_permissions=True)
        return {"status": "ok", "payment_entry": self.payment_entry}

    @frappe.whitelist()
    def trigger_remote_withholding_receipt(self):
        """Transmit the withholding receipt to MoR
        (POST /v1/receipt/withholding). Payload uses the confirmed working
        MoR format (ReceiptNumber, Reason, ReceiptCounter, ManualReceiptNumber,
        SourceSystemType/Number, InvoiceDetail, WithholdDetail). Optional
        fields (ExchangeRate, Rate) are sent as null when absent."""
        if self.eims_status == "Active":
            frappe.throw(_("This withholding receipt has already been authorized by MoR."))

        # The Invoice IRN and the Withheld Amount are provided by the seller —
        # they are optional on the form (so the receipt can be created earlier),
        # but BOTH are required before the receipt can be authorized.
        if not (self.invoice_irn or "").strip():
            frappe.throw(_("The seller-provided Invoice IRN must be entered before authorizing."))
        if not flt(self.withholding_amount):
            frappe.throw(_("The seller-provided Withheld Amount must be entered before authorizing."))

        connector = EIMSConnector()
        try:
            token = connector.get_valid_token()
            base_url = connector.settings.base_url.strip().replace('"', "").replace("'", "").rstrip("/")
            url = f"{base_url}/v1/receipt/withholding"

            headers = {
                "Authorization": f"Bearer {token}",
                "apikey": connector.settings.get_password("api_key"),
                "Content-Type": "application/json",
                "Accept": "*/*",
            }

            receipt_number = self.receipt_number or f"WHT-{self.name}"

            self.receipt_date = frappe.utils.now_datetime().replace(microsecond=0)

            payload = {
                "ReceiptNumber": receipt_number,
                "Reason": self.reason or "Withholding payment",
                "ReceiptCounter": str(self.receipt_counter or ""),
                "ManualReceiptNumber": self.manual_receipt_number or "",
                "SourceSystemType": self.source_system_type or "POS",
                "SourceSystemNumber": self.source_system_number or "",
                "InvoiceDetail": {
                    "InvoiceIRN": self.invoice_irn,
                    "Currency": self.currency or "ETB",
                    "ExchangeRate": abs(float(self.exchange_rate)) if self.exchange_rate else None,
                },
                "WithholdDetail": {
                    "Type": self.withholding_type or "TWTH",
                    "Rate": abs(float(self.withholding_rate)) if self.withholding_rate else None,
                    "PreTaxAmount": abs(float(self.pre_tax_amount or 0.0)),
                    "WithholdingAmount": abs(float(self.withholding_amount or 0.0)),
                },
            }
            payload_data = json.dumps(payload, separators=(",", ":"))

            is_https = url.lower().startswith("https://")
            if is_https:
                request_body = connector._build_signed_envelope(
                    payload_data, connector.get_default_client_data()
                )
                self.request_payload = request_body
            else:
                request_body = payload_data
                self.request_payload = payload_data
            response = requests.post(url, data=request_body.encode("utf-8"), headers=headers, timeout=15)
            res_data = response.json()

            if response.status_code == 200 and res_data.get("statusCode") == 200:
                body = res_data.get("body", {}) or {}
                api_status = body.get("status") or "Active"
                self.eims_status = "Active" if api_status == "A" else api_status
                self.mor_receipt_id = body.get("id") or self.mor_receipt_id
                self.rrn = body.get("rrn") or self.rrn
                self.returned_rnn = body.get("rrn") or self.returned_rnn
                self.qr_code_base64 = body.get("qr") or self.qr_code_base64
                self.response_log = json.dumps(res_data, indent=4)
                self.save()
                frappe.db.commit()
                return {
                    "success": True,
                    "status": self.eims_status,
                    "rrn": self.rrn,
                    "html": self.compile_receipt_html(),
                }

            self.response_log = json.dumps(res_data, indent=4)
            detail = json.dumps(res_data, indent=2)
            duplicate_msg = "Receipt generated for the Invoice IRN given" in detail

            # Only a genuine success response (statusCode 200) that reports the
            # receipt already exists is healed to Active. A 406 rejection keeps
            # the receipt Failed so real validation errors are never hidden.
            if response.status_code == 200 and duplicate_msg and self.eims_status != "Active":
                self.eims_status = "Active"
                self.response_log = (self.response_log or "") + "\n[auto-heal] duplicate-receipt response marked Active"
                self.save()
                frappe.db.commit()
                return {
                    "success": True,
                    "status": self.eims_status,
                    "healed_duplicate": True,
                    "rrn": self.rrn or "",
                    "html": self.compile_receipt_html(),
                }

            self.eims_status = "Failed"
            if duplicate_msg:
                self.response_log = (self.response_log or "") + (
                    "\n[note] MoR reports a withholding receipt already exists for this Invoice IRN —"
                    " check for an existing Active receipt instead of re-authorizing."
                )
            self.save()
            frappe.db.commit()
            return {"success": False, "message": f"Error {response.status_code}: {detail}", "html": None}
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "EIRMS Withholding Receipt Dispatch Failure")
            frappe.throw(_(f"Critical System Processing Exception: {str(e)}"))

    @frappe.whitelist()
    def compile_receipt_html(self):

        receipt_date = self.receipt_date
        if receipt_date:
            try:
                if isinstance(receipt_date, str):
                    receipt_date = get_datetime(receipt_date)
                receipt_date = receipt_date.strftime("%d %B %Y, %H:%M")
            except Exception:
                receipt_date = str(receipt_date)

        qr = self.qr_code_base64 or ""
        qr_html = (
            f'<div style="text-align:center;margin-top:12px;">'
            f'<img src="data:image/png;base64,{qr}" style="width:140px;height:140px;"/></div>'
            if qr
            else ""
        )

        # Fixed-width card. Long values (notably the Invoice IRN hash) are
        # wrapped mid-word (word-break) inside the constrained value column so
        # they never stretch the receipt wider than the card.
        def fmt_amount(val):
            try:
                return f"{float(val or 0.0):,.2f}"
            except (TypeError, ValueError):
                return "0.00"

        invoice_date = self.invoice_date
        if invoice_date:
            try:
                if isinstance(invoice_date, str):
                    invoice_date = get_datetime(invoice_date)
                invoice_date = invoice_date.strftime("%d %B %Y")
            except Exception:
                invoice_date = str(invoice_date)

        qr_html = (
            f'<div style="text-align:center;margin-top:14px;">'
            f'<img src="data:image/png;base64,{self.qr_code_base64}" '
            f'style="width:150px;height:150px;"/></div>'
            if self.qr_code_base64
            else ""
        )

        payment_reference_html = ""
        if self.payment_entry:
            payment_reference_html = (
                '<div class="wr-sec">Payment Reference</div>'
                '<table class="wr-table">'
                '<tr><td class="wr-k">Payment Entry</td><td class="wr-v">%s</td></tr>'
                '<tr><td class="wr-k">Paid Amount</td><td class="wr-v">%s %s</td></tr>'
                '<tr><td class="wr-k">Mode of Payment</td><td class="wr-v">%s</td></tr>'
                '<tr><td class="wr-k">Payment Date</td><td class="wr-v">%s</td></tr>'
                '<tr><td class="wr-k">Reference</td><td class="wr-v">%s</td></tr>'
                '<tr><td class="wr-k">Collector</td><td class="wr-v">%s</td></tr>'
                '</table>'
            ) % (
                self.payment_entry or '',
                self.currency or '', fmt_amount(self.paid_amount),
                self.mode_of_payment or '',
                self.payment_date or '',
                self.payment_reference or '',
                self.collector_name or '',
            )

        return f"""
        <style>
            .wr-card {{ width: 380px; max-width: 100%; margin: 0 auto; font-family: Arial, sans-serif;
                border: 1px solid #d0d5dd; border-radius: 10px; overflow: hidden; }}
            .wr-head {{ background: #f8fafc; text-align: center; padding: 14px;
                border-bottom: 1px dashed #d0d5dd; }}
            .wr-head h3 {{ margin: 0 0 4px; font-size: 16px; }}
            .wr-head .wr-sub {{ color: #475569; font-size: 11px; }}
            .wr-body {{ padding: 12px 16px; }}
            .wr-sec {{ font-size: 10px; text-transform: uppercase; letter-spacing: .05em;
                color: #64748b; margin: 12px 0 4px; border-bottom: 1px solid #eef2f7; padding-bottom: 3px; }}
            .wr-table {{ width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 12px; }}
            .wr-table td {{ padding: 3px 0; vertical-align: top; }}
            .wr-table td.wr-k {{ color: #475569; width: 45%; padding-right: 8px; }}
            .wr-table td.wr-v {{ text-align: right; font-weight: 600; color: #0f172a;
                word-break: break-word; overflow-wrap: anywhere; }}
            .wr-table td.wr-v .wr-mono {{ font-family: monospace; font-size: 10.5px; word-break: break-all; }}
            .wr-sign {{ margin-top: 20px; border-top: 1px dashed #d0d5dd; padding-top: 10px; }}
            .wr-sign .wr-line {{ border-top: 1px solid #94a3b8; width: 60%; margin: 4px auto 4px; }}
            .wr-foot {{ text-align: center; padding: 6px 16px 12px; color: #94a3b8; font-size: 10px; }}
        </style>

        <div class="wr-card">
            <div class="wr-head">
                <h3>Withholding Tax Receipt</h3>
                <div class="wr-sub">Receipt No: {self.receipt_number or self.name}</div>
                <div class="wr-sub">Issued: {receipt_date or ''}</div>
            </div>
            <div class="wr-body">
                <div class="wr-sec">Withholding Agent</div>
                <table class="wr-table">
                    <tr><td class="wr-k">Company Name</td><td class="wr-v">{self.agent_name or ''}</td></tr>
                    <tr><td class="wr-k">TIN</td><td class="wr-v">{self.agent_tin or ''}</td></tr>
                    <tr><td class="wr-k">Address</td><td class="wr-v">{self.agent_address or ''}</td></tr>
                </table>

                <div class="wr-sec">Seller (Withholdee)</div>
                <table class="wr-table">
                    <tr><td class="wr-k">Trading Name</td><td class="wr-v">{self.seller_name or ''}</td></tr>
                    <tr><td class="wr-k">TIN</td><td class="wr-v">{self.seller_tin or ''}</td></tr>
                </table>

                <div class="wr-sec">Transaction Detail</div>
                <table class="wr-table">
                    <tr><td class="wr-k">Tax Invoice No.</td><td class="wr-v">{self.invoice_number or ''}</td></tr>
                    <tr><td class="wr-k">Tax Invoice Date</td><td class="wr-v">{invoice_date or ''}</td></tr>
                    <tr><td class="wr-k">Invoice IRN</td>
                        <td class="wr-v"><span class="wr-mono">{self.invoice_irn or ''}</span></td></tr>
                </table>

                <div class="wr-sec">Withhold Detail</div>
                <table class="wr-table">
                    <tr><td class="wr-k">Type</td><td class="wr-v">{self.withholding_type or ''}</td></tr>
                    <tr><td class="wr-k">Rate</td><td class="wr-v">{self.withholding_rate or 0}%</td></tr>
                    <tr><td class="wr-k">Gross Supply Amount</td>
                        <td class="wr-v">{self.currency or ''} {fmt_amount(self.pre_tax_amount)}</td></tr>
                    <tr><td class="wr-k">Withheld Amount</td>
                        <td class="wr-v">{self.currency or ''} {fmt_amount(self.withholding_amount)}</td></tr>
                    <tr><td class="wr-k">Reason</td><td class="wr-v">{self.reason or ''}</td></tr>
                </table>

                <div class="wr-sec">Status</div>
                <table class="wr-table">
                    <tr><td class="wr-k">Status</td><td class="wr-v">{self.eims_status or ''}</td></tr>
                    <tr><td class="wr-k">MoR ID</td><td class="wr-v">{self.mor_receipt_id or ''}</td></tr>
                    <tr><td class="wr-k">RRN</td><td class="wr-v">{self.rrn or ''}</td></tr>
                </table>

                {payment_reference_html}
                {qr_html}

                <div class="wr-sign">
                    <table class="wr-table">
                        <tr><td class="wr-k">Signed By</td><td class="wr-v">{self.signatory_name or ''}</td></tr>
                        <tr><td class="wr-k">Title</td><td class="wr-v">{self.signatory_title or ''}</td></tr>
                    </table>
                    <div style="text-align:center;margin-top:10px;">
                        <div style="font-size:11px;color:#475569;">Authorized Signatory, Seal &amp; Stamp</div>
                        <div class="wr-line"></div>
                        <div style="font-size:10px;color:#94a3b8;">{self.seal_notes or ''}</div>
                    </div>
                </div>
            </div>
            <div class="wr-foot">Verified via Ethiopian MoR EIMS</div>
        </div>
        """


@frappe.whitelist()
def create_withholding_receipt_for_purchase(purchase_invoice):
    """Create (or return) a Withholding Receipt pre-populated from a submitted
    Purchase Invoice. The MoR InvoiceIRN and the Withheld Amount are provided
    by the seller and must be entered on the receipt before authorizing."""
    try:
        pi = frappe.get_doc("Purchase Invoice", purchase_invoice)
        if pi.docstatus != 1:
            return {"status": "error", "message": _("Purchase Invoice {0} is not submitted.").format(purchase_invoice)}

        # Reuse an existing draft for the same purchase invoice if present.
        existing = frappe.get_all(
            "Withholding Receipt",
            filters={"invoice_number": pi.name, "docstatus": 0},
            fields=["name"],
            order_by="creation desc",
            limit=1,
        )
        if existing:
            doc = frappe.get_doc("Withholding Receipt", existing[0].name)
            if not doc.eims_status:
                doc.eims_status = "Pending"
            return {"status": "ok", "receipt_name": doc.name, "already_created": doc.eims_status == "Active"}

        doc = frappe.new_doc("Withholding Receipt")
        doc.eims_status = "Pending"
        doc.populate_from_purchase_invoice(purchase_invoice)
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return {"status": "ok", "receipt_name": doc.name, "already_created": False}
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Create purchase withholding receipt error")
        return {"status": "error", "message": str(e)}

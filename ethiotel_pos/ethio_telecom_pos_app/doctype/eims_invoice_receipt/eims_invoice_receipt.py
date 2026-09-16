import json
import requests
import frappe
from datetime import datetime
from frappe import _
from frappe.model.document import Document
from frappe.utils import fmt_money, flt
from ethiotel_pos.eims_connector import EIMSConnector, resolve_mor_payment_mode
import base64
from frappe.utils import money_in_words
from frappe.utils import now_datetime
class EIMSInvoiceReceipt(Document):
    def validate(self):
        
        if self.mode_of_payment and not resolve_mor_payment_mode(self.mode_of_payment):
            frappe.throw(_(
                "Invalid Mode of Payment. Must be one of: CASH, CHEQUE, CPO, "
                "Local Bank Transfer, SWIFT, Wire Transfer, Letter of Credit, Card."
            ))

    def before_save(self):
   
        # if self.eims_status == "Active" and not self.is_new():
        #     existing_status = frappe.db.get_value("EIMS Invoice Receipt", self.name, "eims_status")
        #     if existing_status == "Active":
        #         frappe.throw(_("Authenticated MoR EIRMS receipts are immutable and cannot be altered."))
        # # auto-increement receipt_counter
        # if self.receipt_counter == 0:
        #     # get maximum receipt counter
        #     max_counter = frappe.db.get_value("EIMS Invoice Receipt", None, "max(receipt_counter)", as_dict=1)
        #     self.receipt_counter = max_counter.get("max(receipt_counter)") + 1 if max_counter else 1
        pass

    def get_default_client_data(self, doc):
        """Helper to get the active default row from the child table"""
        if not doc.client_data_list:
            frappe.throw("No client configuration found in EIMS Settings.")
            
        for row in doc.client_data_list:
            if row.is_default == 1:
                return frappe.get_doc(row.doctype, row.name)
                
        frappe.throw("No default configuration row selected in EIMS Settings.")
    @frappe.whitelist()
    def fetch_payment_entry_details(self):
        if not self.payment_entry:
            return

        pe = frappe.get_doc("Payment Entry", self.payment_entry)
        eims_settings = frappe.get_single("EIMS Setting")
        default_client = self.get_default_client_data(eims_settings)
        self.party_type = pe.party_type
        self.party = pe.party
        self.party_name = pe.party_name
        self.mode_of_payment = resolve_mor_payment_mode(pe.mode_of_payment) or "CASH"
        self.collected_amount = pe.paid_amount
        self.currency = pe.paid_from_account_currency
        self.receipt_date = pe.posting_date
        self.transaction_number = pe.reference_no or ""
        self.account_number = pe.bank_account_no or ""
        self.payment_provider = pe.bank or "Bank"
        self.collector_name = pe.owner
        self.seller_tin = eims_settings.seller_tin
        self.source_system_type = default_client.system_type
        self.source_system_no = default_client.system_number

        self.invoices_covered = []
        # MoR validates receipt amounts against the EXACT totals stored at
        # registration time — those can carry sub-cent decimals (VAT
        # division), while Payment Entry reference amounts are rounded to
        # currency precision. Sending the rounded figures triggers
        # "Invoice total amount mismatch". Always use the registered value.
        from ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos import (
            _mor_registered_total,
        )

        for ref in pe.references:
            if ref.reference_doctype == "Sales Invoice":
                inv_doc = frappe.get_doc("Sales Invoice", ref.reference_name)
                if not inv_doc or not inv_doc.custom_irn:
                    frappe.throw(_("Sales Invoice {0} does not have an EIRMS IRN (custom_irn) identifier.").format(ref.reference_name))

                self.eims_rrn = inv_doc.custom_irn
                self.receipt_counter = inv_doc.custom_document_number
                coverage = "FULL" if flt(ref.allocated_amount) >= flt(ref.total_amount) else "PARTIAL"
                exact_total = _mor_registered_total(inv_doc)
                self.append("invoices_covered", {
                    "sales_invoice": ref.reference_name,
                    "invoice_irn": inv_doc.custom_irn,
                    "payment_coverage": coverage,
                    "invoice_paid_amount": exact_total if coverage == "FULL" else ref.allocated_amount,
                    "discount_amount": float(inv_doc.discount_amount or 0.0),
                    "remaining_amount": 0.0 if coverage == "FULL" else ref.outstanding_amount,
                    "total_amount": exact_total,
                    "taxable_amount": float(inv_doc.net_total or 0.0),
                })

        # Keep the receipt-level collected amount consistent with the exact
        # rows above instead of the rounded PE paid_amount.
        self.collected_amount = flt(
            sum(flt(row.invoice_paid_amount) for row in self.invoices_covered)
        )

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
                # MoR rejects the receipt with NOT_ACCEPTABLE when numeric
                # fields arrive as null — always send numbers.
                invoice_payload.append({
                    "InvoiceIRN": item.invoice_irn,
                    "PaymentCoverage": item.payment_coverage or "FULL",
                    # Amounts must match the registered invoice totals
                    # exactly — do NOT round them here.
                    "InvoicePaidAmount": float(item.invoice_paid_amount or 0.0),
                    "DiscountAmount": float(item.discount_amount or 0.0),
                    "RemainingAmount": float(item.remaining_amount or 0.0),
                    "TotalAmount": float(item.total_amount or 0.0)
                })

            # ReceiptDate in the format MoR expects (ISO-8601 with
            # milliseconds and timezone offset, e.g.
            # 2026-08-21T10:00:00.123+03:00).
            receipt_date_str = datetime.now().astimezone().isoformat(timespec="milliseconds")

            payload_data = json.dumps({
                "ReceiptNumber": self.receipt_number,
                "ReceiptType": self.receipt_type or "Sales Receipts",
                "Reason": self.remark or "Payment for goods purchased",
                "ReceiptDate": receipt_date_str,
                "ReceiptCounter": self.receipt_counter,
                "SourceSystemType": self.source_system_type,
                "SourceSystemNumber": self.source_system_no,
                "ReceiptCurrency": self.currency or "ETB",
                "CollectedAmount": float(self.collected_amount or 0.0),
                "SellerTIN": self.seller_tin,
                "Invoices": invoice_payload,
                "TransactionDetails": {
                    "ModeOfPayment": resolve_mor_payment_mode(self.mode_of_payment) or "CASH",
                    "CollectorName": self.collector_name or "Cashier",
                    "PaymentServiceProvider": self.payment_provider or "Bank",
                    "TransactionNumber": self.transaction_number
                }
            }, separators=(",", ":"))

            self.request_payload = payload_data
            request_body = connector._build_signed_envelope(
                payload_data, connector.get_default_client_data()
            )
            self.request_payload = request_body
            response = requests.post(url, data=request_body.encode("utf-8"), headers=headers, timeout=15)
            res_data = response.json()
            if response.status_code == 200 and res_data.get("statusCode") == 200:
                body = res_data.get("body", {})
                api_status = body.get("status")
                
                if api_status == "A":
                    self.eims_status = "Active"
                else:
                    self.eims_status = api_status or "Active"

                self.eims_rrn = body.get("rrn") or self.eims_rrn
                self.returned_rnn = body.get("rrn") or ""
                self.qr_code_base64 = body.get("qr") or body.get("signedQR") or body.get("qrCode") or self.qr_code_base64

                # Persist the returned RNN on every covered Sales Invoice —
                # MoR does not support duplicate receipt generation, so any
                # later re-fetch must look the receipt up BY RNN instead of
                # re-submitting.
                for row in self.invoices_covered or []:
                    if row.sales_invoice:
                        frappe.db.set_value(
                            "Sales Invoice", row.sales_invoice, "custom_mor_rrn", self.returned_rnn
                        )
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
                detail = json.dumps(res_data, indent=2)

                # Idempotent duplicate-receipt healing: MoR rejects a retry
                # with "Receipt generated for the Invoice IRN given" when a
                # receipt ALREADY exists remotely (a previous attempt reached
                # MoR but its response was lost locally). Retrying would fail
                # forever — mark this receipt Active instead.
                if "Receipt generated for the Invoice IRN given" in detail:
                    if self.eims_status != "Active":
                        self.eims_status = "Active"
                        self.response_log = (
                            f"{self.response_log or ''}\n[auto-heal] duplicate-receipt rejection marked Active"
                        )
                        self.save()
                        frappe.db.commit()
                    return {
                        "success": True,
                        "status": self.eims_status,
                        "healed_duplicate": True,
                        "rrn": self.eims_rrn or "",
                        "html": self.compile_receipt_html(),
                    }

                return {
                    "success": False,
                    "message": f"Error {response.status_code}: {detail}",
                    "html": None
                }

        except Exception as e:
            frappe.log_error(message=frappe.get_traceback(), title="EIRMS Receipt Dispatch Failure")
            frappe.throw(_(f"Critical System Processing Exception: {str(e)}"))

    @frappe.whitelist()
    def compile_receipt_html(self):
        self.fetch_payment_entry_details()

        # Safe attribute extraction from document instance fields
        currency = getattr(self, "currency", "ETB") or "ETB"
        qr_code_base64 = getattr(self, "qr_code_base64", "")
        mode_of_payment = getattr(self, "mode_of_payment", "CASH")
        collector_name = getattr(self, "collector_name", "System Cashier")
        eims_rrn = getattr(self, "eims_rrn", "N/A")
        collected_amount = float(getattr(self, "collected_amount", 0.0) or 0.0)
        receipt_counter = getattr(self, "receipt_counter")
        receipt_time = getattr(self, "receipt_time", "00:00:00")

        # Load global system configurations
        eims_settings = frappe.get_single("EIMS Setting")
        company_doc = None
        if getattr(self, "company", None):
            try:
                company_doc = frappe.get_doc("Company", self.company)
            except Exception:
                pass

        # Seller Dynamic Values from Document, EIMS Setting or Company Profile
        seller_name = getattr(self, "company", None) or (company_doc.company_name if company_doc else "Guba Technology Plc")
        seller_tin = getattr(self, "seller_tin", None) or getattr(eims_settings, "seller_tin", "0075951845")
        seller_vat_no = getattr(self, "seller_vat_no", None) or (company_doc.tax_id if company_doc else "43256663343256663322")
        seller_phone = getattr(self, "seller_phone", None) or (company_doc.phone_no if company_doc else "0923525754")
        source_system_no = getattr(self, "source_system_no", None) or getattr(eims_settings, "system_number", "FF14E23B6A")
        
        # Explicit broken-down address layout keys matching sample document
        seller_city = getattr(self, "seller_city", "Addis Ababa")
        seller_subcity = getattr(self, "seller_subcity", "N/A")
        seller_woreda = getattr(self, "seller_woreda", "13")
        seller_kebele = getattr(self, "seller_kebele", "N/A")
        seller_hno = getattr(self, "seller_hno", "101")

        # Customer Dynamic Values from Document with fallback matching sample
        customer_name = getattr(self, "party_name", "N/A")
        customer_tin = getattr(self, "party_tin", "N/A")
        customer_vat_no = getattr(self, "party_vat_no", "N/A")
        customer_city = getattr(self, "customer_city", "이")
        customer_subcity = getattr(self, "customer_subcity", "N/A")
        customer_woreda = getattr(self, "customer_woreda", "574")
        customer_kebele = getattr(self, "customer_kebele", "N/A")
        customer_hno = getattr(self, "customer_hno", "NEW")

        # Attempt to dynamically parse official QR code metadata payload if active
        qr_data = {}
        if qr_code_base64:
            try:
                b64_str = qr_code_base64.split(",")[-1] if "," in qr_code_base64 else qr_code_base64
                decoded_bytes = base64.b64decode(b64_str)
                decoded_str = decoded_bytes.decode("utf-8")
                qr_data = json.loads(decoded_str)
            except Exception:
                qr_data = {}

        if qr_data:
            receipt_counter = qr_data.get("ReceiptNumber") or qr_data.get("ReceiptCounter") or receipt_counter
            source_system_no = qr_data.get("SourceSystemNumber") or source_system_no
            eims_rrn = qr_data.get("RRN") or eims_rrn
            collected_amount = qr_data.get("CollectedAmount") or collected_amount
            currency = qr_data.get("ReceiptCurrency") or currency

        # Sourced posting timeline
        posting_date_str = ""
        if qr_data.get("ReceiptDate"):
            try:
                dt = datetime.strptime(qr_data.get("ReceiptDate").replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
                posting_date_str = dt.strftime("%d-%m-%Y")
            except Exception:
                posting_date_str = qr_data.get("ReceiptDate")
        elif getattr(self, "receipt_date", None):
            try:
                posting_date_str = self.receipt_date.strftime("%d-%m-%Y")
            except Exception:
                posting_date_str = str(self.receipt_date)
        else:
            posting_date_str = "11-06-2026"

        # Dynamically fetch breakdown item lines from linked Sales Invoices to fulfill missing details
        invoice_rows = ""
        idx = 1
        invoices_covered = getattr(self, "invoices_covered", []) or []

        discount_amount = float(getattr(self, "discount_amount", 0.0) or 0.0)
        taxable_total = float(getattr(self, "taxable_amount", 0.0) or getattr(self, "taxable_total", 0.0) or 0.0)
        excise_tax = float(getattr(self, "excise_tax_amount", 0.0) or getattr(self, "excise_tax", 0.0) or 0.0)
        total_vat_taxable = float(getattr(self, "total_vat_taxable_amount", 0.0) or taxable_total)
        vat_amount = float(getattr(self, "vat_amount", 0.0) or 0.0)
        total_amounts = 0.0
        for inv in invoices_covered:
            is_dict = isinstance(inv, dict)
            invoice_irn = inv.get("invoice_irn") if is_dict else getattr(inv, "invoice_irn", None)
            if not invoice_irn:
                continue
            discount_amount = float(inv.get("discount_amount", 0.0) if is_dict else getattr(inv, "discount_amount", 0.0) or 0.0)
            taxable_total = float(inv.get("taxable_amount", 0.0) if is_dict else getattr(inv, "taxable_amount", 0.0) or getattr(inv, "taxable_total", 0.0) or 0.0)
            excise_tax = float(inv.get("excise_tax_amount", 0.0) if is_dict else getattr(inv, "excise_tax_amount", 0.0) or getattr(inv, "excise_tax", 0.0) or 0.0)
            total_vat_taxable = float(inv.get("total_vat_taxable_amount", 0.0) if is_dict else getattr(inv, "total_vat_taxable_amount", 0.0) or taxable_total)
            vat_amount = float(inv.get("vat_amount", 0.0) if is_dict else getattr(inv, "vat_amount", 0.0) or 0.0)
            receipt_counter = inv.get("receipt_counter") if is_dict else getattr(inv, "receipt_counter", receipt_counter)
            si_name = frappe.db.get_value("Sales Invoice", {"custom_irn": invoice_irn}, "name")
            source_doctype = "Sales Invoice"
            if not si_name:
                # POS-first flow: the invoice was registered directly as a
                # POS Invoice and never converted to a Sales Invoice.
                si_name = frappe.db.get_value("POS Invoice", {"custom_irn": invoice_irn}, "name")
                source_doctype = "POS Invoice"
            if si_name:
                si_doc = frappe.get_doc(source_doctype, si_name)
                
                # Extract missing customer metadata directly from source invoice
                if not getattr(self, "party_tin", None):
                    customer_tin = getattr(si_doc, "tax_id", customer_tin)
                if not getattr(self, "party_vat_no", None):
                    customer_vat_no = getattr(si_doc, "customer_vat_no", customer_vat_no)
                
                # Extract address components from source invoice if available
                customer_city = getattr(si_doc, "customer_city", customer_city)
                customer_subcity = getattr(si_doc, "customer_subcity", customer_subcity)
                customer_woreda = getattr(si_doc, "customer_woreda", customer_woreda)
                customer_kebele = getattr(si_doc, "customer_kebele", customer_kebele)
                customer_hno = getattr(si_doc, "customer_hno", customer_hno)
                
                # Gather totals exactly without reprocessing raw division formulas
                if taxable_total == 0.0:
                    taxable_total = float(getattr(si_doc, "taxable_amount", 0.0) or getattr(si_doc, "base_net_total", 0.0) or 0.0)
                if vat_amount == 0.0:
                    vat_amount = float(getattr(si_doc, "total_taxes_and_charges", 0.0) or 0.0)
                
                for item in si_doc.items:
                    item_desc = item.description or item.item_name or item.item_code
                    nature = "goods" if item.actual_qty > 0 else "services"
                    uom = item.uom or "PCS"
                    qty = item.qty
                    rate = item.net_rate
                    item_tax_code = "VAT15"
                    if hasattr(item, "item_tax_template") and item.item_tax_template:
                        item_tax_code = item.item_tax_template.split(" - ")[0]
                    
                    item_excise = float(getattr(item, "excise_tax", 0.0))
                    item_total = item.net_amount
                    total_amounts += item_total
                    
                    invoice_rows += f"""
                    <tr>
                        <td style="text-align:center;">{idx}</td>
                        <td style="text-align:left;">{item_desc}</td>
                        <td style="text-align:center;">{nature}</td>
                        <td style="text-align:center;">{uom}</td>
                        <td style="text-align:center;">{qty}</td>
                        <td style="text-align:right;">{rate:,.2f}</td>
                        <td style="text-align:center;">{item_tax_code}</td>
                        <td style="text-align:right;">{item_excise:,.2f}</td>
                        <td style="text-align:right;">{item_total:,.2f}</td>
                    </tr>
                    """
                    idx += 1

      

        if total_vat_taxable == 0.0:
            total_vat_taxable = taxable_total

        total_inc_tax = float(getattr(self, "collected_amount", 0.0) or (taxable_total + vat_amount))

        try:
            amt_in_words = money_in_words(total_inc_tax, currency).lower()
        except Exception:
            amt_in_words = "one thousand, one hundred fifty birr"

        # Generate HTML matching the official standard layout structure
        html = f"""
        <div id="eims-receipt-container" style="font-family: 'Courier New', Courier, monospace; color:#000; max-width:780px; margin:0 auto; padding:10px; background:#fff; line-height:1.3; font-size:12px;">
            <style>
                #eims-receipt-container .header-title {{ text-align: center; font-weight: bold; font-size: 16px; margin: 0; font-family: Arial, sans-serif; }}
                #eims-receipt-container .header-subtitle {{ text-align: center; font-weight: bold; font-size: 13px; margin: 3px 0 15px 0; font-family: Arial, sans-serif; }}
                #eims-receipt-container .meta-table, #eims-receipt-container .grid-table {{ width: 100%; border-collapse: collapse; margin-bottom: 10px; }}
                #eims-receipt-container .meta-table td {{ border: none; padding: 3px 5px; vertical-align: top; }}
                #eims-receipt-container .grid-table th, #eims-receipt-container .grid-table td {{ border: 1px solid #000; padding: 5px; font-size: 11px; }}
                #eims-receipt-container .grid-table th {{ background: #f2f2f2; font-weight: bold; text-align: center; }}
                #eims-receipt-container .totals-row {{ font-weight: bold; }}
                #eims-receipt-container .inline-print-btn {{ background-color: #17a2b8; color: white; padding: 6px 12px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; font-family: Arial, sans-serif; margin-bottom: 10px; }}
                @media print {{ .inline-print-btn {{ display: none !important; }} }}
            </style>

            

            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 5px;">
                <div style="width: 120px;">
                    {"<img src='data:image/png;base64," + qr_code_base64 + "' alt='Verification QR' style='width:110px; height:110px; display:block;' />" if qr_code_base64 else "<div style='width:110px; height:110px; border:1px solid #ccc; text-align:center; line-height:110px; font-size:10px;'>QR Code Placeholder</div>"}
                </div>
                <div style="flex: 1; text-align: center; padding-right: 20px;">
                    <h2 class="header-title">{seller_name}</h2>
                    <p style="margin: 2px 0; font-size: 11px;">ስልክ ቁጥር / Phone No: {seller_phone}</p>
                    <h3 class="header-subtitle">የእጅ በእጅ ሽያጭ ደረሰኝ / ተ.እ.ታ / ኤክሳይዝ ታክስ<br/>Cash sales invoice / VAT/Excise Tax</h3>
                </div>
            </div>

            <div style="word-break: break-all; font-size: 10px; margin-bottom: 10px; border-bottom: 1px dashed #000; padding-bottom: 5px;">
                <strong>IRN:</strong> {eims_rrn}
            </div>

            <table class="meta-table" aria-label="Receipt Metadata Info">
                <tr>
                    <td style="width: 55%;"><strong>የሲስተም ቁጥር / System Number:</strong> {source_system_no}</td>
                    <td style="width: 45%;"><strong>የደረሰኝ ቁጥር / Document No:</strong> {receipt_counter}</td>
                </tr>
                <tr>
                    <td><strong>ቀን / Date:</strong> {posting_date_str} &nbsp;&nbsp; <strong>Time:</strong> {receipt_time}</td>
                    <td><strong>የክፍያ ሁኔታ / Mode of Payment:</strong> {mode_of_payment}</td>
                </tr>
            </table>

            <table style="width: 100%; border: 1px solid #000; font-size: 11px; border-collapse: collapse; margin-bottom: 10px;" aria-label="Address Matrix Info Table">
                <tr>
                    <td style="width: 50%; border-right: 1px solid #000; padding: 5px; vertical-align: top; line-height: 1.4;">
                        <div style="font-weight: bold; border-bottom: 1px solid #000; padding-bottom: 2px; margin-bottom: 3px;">ከሻጭ / From</div>
                        <strong>ስም / Name:</strong> {seller_name}<br/>
                        <strong>ከተማ / City:</strong> {seller_city}<br/>
                        <strong>ክፍለ ከተማ / Subcity:</strong> {seller_subcity}<br/>
                        <strong>ወረዳ / Woreda:</strong> {seller_woreda}<br/>
                        <strong>ቀበሌ / Kebele:</strong> {seller_kebele}<br/>
                        <strong>የቤት ቁጥር / H.No:</strong> {seller_hno}<br/>
                        <strong>የግብር ከፋይ መለያ ቁጥር / Seller's TIN:</strong> {seller_tin}<br/>
                        <strong>የተ.እ.ታ ቁጥር / Seller's VAT Reg.No:</strong> {seller_vat_no}
                    </td>
                    <td style="width: 50%; padding: 5px; vertical-align: top; line-height: 1.4;">
                        <div style="font-weight: bold; border-bottom: 1px solid #000; padding-bottom: 2px; margin-bottom: 3px;">ለገዢ / To</div>
                        <strong>ስም / Name:</strong> {customer_name}<br/>
                        <strong>ከተማ / City:</strong> {customer_city}<br/>
                        <strong>ክፍለ ከተማ / Subcity:</strong> {customer_subcity}<br/>
                        <strong>ወረዳ / Woreda:</strong> {customer_woreda}<br/>
                        <strong>ቀበሌ / Kebele:</strong> {customer_kebele}<br/>
                        <strong>የቤት ቁጥር / H.No:</strong> {customer_hno}<br/>
                        <strong>የግብር ከፋይ መለያ ቁጥር / Customer's TIN:</strong> {customer_tin}<br/>
                        <strong>የተ.እ.ታ ቁጥር / Customer's VAT Reg.No:</strong> {customer_vat_no}
                    </td>
                </tr>
            </table>

            <table class="grid-table" aria-label="Product tracking Grid Table">
                <thead>
                    <tr>
                        <th style="width: 4%;">No.</th>
                        <th style="width: 34%;">አይነት<br/>Product/Service Description</th>
                        <th style="width: 10%;">ምድብ<br/>Nature</th>
                        <th style="width: 8%;">መለኪያ<br/>UoM</th>
                        <th style="width: 6%;">ብዛት<br/>Qty</th>
                        <th style="width: 11%;">የአንዱ ዋጋ<br/>Unit Price</th>
                        <th style="width: 9%;">ታክስ ኮድ<br/>Tax Code</th>
                        <th style="width: 8%;">ኤክሳይዝ<br/>Excise</th>
                        <th style="width: 10%;">ጠቅላላ ዋጋ<br/>Total</th>
                    </tr>
                </thead>
                <tbody>
                    {invoice_rows}
                </tbody>
            </table>

            <div style="display: flex; justify-content: flex-end;">
                <table style="width: 60%; border-collapse: collapse; font-size: 11px;" aria-label="Tax Accumulation Aggregates Table">
                    <tr>
                        <td style="padding: 3px; text-align: left;">ድምር {self.currency} / Total {self.currency}:</td>
                        <td style="padding: 3px; text-align: right; width: 35%;">{total_amounts:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 3px; text-align: left;">የቅናሽ መጠን / Discount Amount:</td>
                        <td style="padding: 3px; text-align: right; width: 35%;">{discount_amount:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 3px; text-align: left;">ታክስ የሚከፈልበት ድምር / Taxable Total:</td>
                        <td style="padding: 3px; text-align: right;">{taxable_total:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 3px; text-align: left;">ኤክሳይዝ ታክስ / Excise Tax:</td>
                        <td style="padding: 3px; text-align: right;">{excise_tax:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 3px; text-align: left;">ተ.እ.ታ የሚከፈልበት ድምር / Total VAT Taxable Amount:</td>
                        <td style="padding: 3px; text-align: right;">{total_vat_taxable:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 3px; text-align: left;">VAT 15% ታክስ መጠን / VAT15 Tax Amount:</td>
                        <td style="padding: 3px; text-align: right; border-bottom: 1px solid #000;">{vat_amount:,.2f}</td>
                    </tr>
                    <tr class="totals-row">
                        <td style="padding: 5px 3px; text-align: left; font-size: 12px;">ጠቅላላ ድምር / Total Including Tax ({currency}):</td>
                        <td style="padding: 5px 3px; text-align: right; font-size: 12px; border-bottom: 3px double #000;">{total_inc_tax:,.2f}</td>
                    </tr>
                </table>
            </div>

            <div style="margin-top: 10px; padding: 5px; border: 1px solid #000; background: #fafafa; font-size: 11px;">
                <strong>ጠቅላላ ዋጋ በፊደል / Total Including Tax (in words):</strong><br/>
                {amt_in_words}.
            </div>

            <table class="meta-table" style="margin-top: 20px;" aria-label="Receiver Footer Block Table">
                <tr>
                    <td style="text-align: left; width: 50%;"><strong>የተቀባይ ስምና ፊርማ / Receiver Name & Signature:</strong><br/>{collector_name}</td>
                    <td style="text-align: right; width: 50%; vertical-align: bottom;"><strong>ፊርማ / Signature:</strong> ______________________</td>
                </tr>
            </table>
            
            <div style="text-align: center; font-size: 9px; color: #555; margin-top: 25px; border-top: 1px dashed #ccc; padding-top: 5px;">
                Certified Official Document transmitted securely to Ministry of Revenues EIRMS system Hub endpoint.
            </div>
        </div>
        """
        return html

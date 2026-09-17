import base64
import json
import re
import time

import requests

from frappe.utils import get_datetime, now_datetime

from .audit import log_audit
from .constants import EIMS_MIN_BULK_SIZE
from .logging_setup import eims_logger
from .sanitize import redact_payload
from ethiotel_pos.notify import _enqueue, send_registered_receipt

import frappe


class EIMSConnectorSubmit:
    def _resolve_invoice_doctype(self, invoice_name):
        """Return the doctype of the invoice: 'Sales Invoice' when the name
        is a Sales Invoice, otherwise 'POS Invoice'. Sales Invoices and POS
        Invoices are separate EIMS registrations that share one document
        number source (EIMS Setting.last_document_number). but here withholding related
        things are don in the sales invoice side. tasactions like b2b, b2g,or g2g are 
        more likely being done in the salesss invoice side."""
        if frappe.db.exists("Sales Invoice", invoice_name):
            return "Sales Invoice"
        if frappe.db.exists("POS Invoice", invoice_name):
            return "POS Invoice"
        frappe.throw(f"Invoice {invoice_name} not found (neither Sales Invoice nor POS Invoice).")

    @staticmethod
    def _ensure_service_active():
        """Refuse new EIRMS registrations once the taxpayer service has been
        terminated (Directive Art 8 service termination). Existing registered
        invoices and the audit trail remain readable for the retention window.
        this was supposed to be for multi tenant system"""
        if frappe.db.get_single_value("EIMS Setting", "service_terminated"):
            frappe.throw(
                "EIMS registration is disabled for this taxpayer: the service has been "
                "terminated. Export your data from EIMS Setting > Data Management first.",
                frappe.PermissionError,
            )

    def _resolve_note_override(self, doc):
        """
        Decide the MoR document Type ('INV', 'CRE' or 'DEB')
        inv is for invoice, cre is for credite note and deb id for debit note in the sales invoice.
        check (Is Return (Credit Note)) for CRE and
        check (Is Rate Adjustment Entry (Debit Note)) for DEB in the sales invoice
        """
        if getattr(doc, "is_debit_note", 0):
            note_type = "DEB"
        elif getattr(doc, "is_return", 0):
            note_type = "CRE"
        else:
            note_type = "INV"

        if note_type not in ("CRE", "DEB"):
            return note_type, None

        original_name = doc.get("return_against") or None
        ref_irn = self._lookup_irn_for_invoice(original_name) if original_name else None
        if not ref_irn:
            frappe.throw(
                f"Validation Error on Invoice ({doc.name}):<br><br>"
                f"<b>{note_type}</b> notes must reference an EIRMS-registered original invoice. "
                f"Set <b>Return Against</b> to an invoice whose <b>custom_irn</b> is already "
                f"populated, then try again.",
                title="EIMS Schema Error: Missing Original Invoice IRN",
            )
        return note_type, ref_irn

    def submit_single_invoice(self, invoice_name):
        try:
            self._ensure_service_active()
            doctype = self._resolve_invoice_doctype(invoice_name)
            doc = frappe.get_doc(doctype, invoice_name)

            existing_doc_num = doc.get("custom_document_number")
            if existing_doc_num:
                # reuse the number already assigned to this invoice if it exists
                doc_num = int(existing_doc_num)
                is_resend = True
            else:
                doc_num = self._peek_next_document_number()
                is_resend = False

            token = self.get_valid_token()
            default_client = self.get_default_client_data()

            note_type, note_ref_irn = self._resolve_note_override(doc)

            clean_url = self.settings.base_url.strip().rstrip('/')
            register_url = f"{clean_url}/v1/register"
            is_https = register_url.lower().startswith("https://")
            attempts = 0
            while True:
                attempts += 1
                invoice_payload = self.build_invoice_payload(
                    doc,
                    override_doc_num=doc_num,
                    override_note_type=note_type,
                    override_note_ref_irn=note_ref_irn,
                )

                auth_headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                    "apikey": self.settings.get_password("api_key"),
                }

                json_string_payload = json.dumps(invoice_payload, separators=(",", ":"))
                if is_https:
                    request_body = self._build_signed_envelope(json_string_payload, default_client)
                else:
                    request_body = json_string_payload

                response = self._post_with_retry(
                    register_url,
                    request_body,
                    auth_headers,
                    timeout=15
                )

                if response.status_code == 401:
                    token = self.get_valid_token(force_refresh=True)
                    auth_headers["Authorization"] = f"Bearer {token}"
                    response = self._post_with_retry(
                        register_url,
                        request_body,
                        auth_headers,
                        timeout=15
                    )

                if response.status_code in (200, 201):
                    res_json = response.json()
                    body_data = res_json.get("body", {})
                    irn = body_data.get("irn")
                    signed_qr_base64 = body_data.get("signedQR")

                    qr_code_url = self._save_qr_file(invoice_name, signed_qr_base64, doctype)

                    frappe.db.set_value(doctype, invoice_name, self._filter_known_fields(doctype, {
                        "custom_irn": irn,
                        "custom_qr_code_url": qr_code_url,
                        "custom_eims_status": "Registered",
                        "custom_document_number": doc_num,
                       
                        "custom_mor_total_value": invoice_payload["ValueDetails"]["TotalValue"],
                    }), update_modified=True)

                    # Only persist the counter after MoR confirms success.
                    if doc_num > int(self.settings.last_document_number or 0):
                        self._commit_document_number(doc_num)

                    frappe.db.commit()
                    # Log the successful registration in the EIMS Audit Trail
                    log_audit(
                        "Invoice Registration",
                        invoice_type=doctype,
                        invoice=invoice_name,
                        eims_status="Registered",
                        document_number=doc_num,
                        success=True,
                        description="Invoice registered with EIRMS",
                        request_brief=(request_body if isinstance(request_body, str) else json.dumps(request_body, separators=(",", ":")))[:2000],
                        response_brief=response.text[:2000],
                    )
                    #notify
                    _enqueue(send_registered_receipt, invoice_name=invoice_name, doctype=doctype)
                    return {"status": "Transmitted", "message": f"Successfully registered. IRN: {irn}"}

                # use the expected number from MoR when the first fails and retry the next.
                # self-healing code to recover from a lost response
                expected_num = self._parse_expected_doc_num(response.text)
                
                # ER-GE-1 (Internal Server Error) -this late errore encountered from MoR system.
                # I don't really know what it means but the issue was about document number.
                # It often indicates document number mismatch
                # even when MoR doesn't return the "expected : NNN" pattern.
                # If we get ER-GE-1, try auto-advancing to the next sequence number.
                """commonly it happens whenever you switch between the system number (cliesnt)"""
                is_erge1 = '"1":"Internal Server Error, ER-GE-1"' in (response.text or "")
                if is_erge1 and attempts < 2:
                    # Auto-advance: use the next number from our authoritative counter
                    next_num = self._peek_next_document_number()
                    if next_num != doc_num:
                        frappe.logger().info(
                            f"ER-GE-1 received for doc {doc_num}, auto-advancing to {next_num}"
                        )
                        self._commit_document_number(next_num - 1)
                        doc_num = next_num
                        frappe.db.set_value(
                            doctype, invoice_name, "custom_document_number", doc_num,
                            update_modified=True,
                        )
                        frappe.db.commit()
                        continue

                if expected_num is not None and expected_num != doc_num and attempts < 2:
                    self._commit_document_number(expected_num - 1)
                    doc_num = expected_num
                    frappe.db.set_value(
                        doctype, invoice_name, "custom_document_number", doc_num,
                        update_modified=True,
                    )
                    frappe.db.commit()
                    continue

                # idempotent resend.
                if expected_num is not None and expected_num == doc_num and is_resend:
                    irn = self._lookup_irn_for_doc_num(doc_num)
                    if irn:
                        frappe.db.set_value(doctype, invoice_name, self._filter_known_fields(doctype, {
                            "custom_irn": irn,
                            "custom_eims_status": "Registered",
                            "custom_document_number": doc_num,
                        }), update_modified=True)
                        if doc_num > int(self.settings.last_document_number or 0):
                            self._commit_document_number(doc_num)
                        frappe.db.commit()
                        log_audit(
                            "Invoice Registration",
                            invoice_type=doctype,
                            invoice=invoice_name,
                            eims_status="Registered",
                            document_number=doc_num,
                            success=True,
                            description="Already registered with EIRMS (idempotent resend)",
                        )
                        return {"status": "Transmitted", "message": f"Already registered. IRN: {irn}"}

                # Max 2 attempts reached or non-retryable error - fail with full context
                frappe.db.set_value(doctype, invoice_name, "custom_eims_status", "Failed", update_modified=True)
                frappe.db.commit()

                error_msg = (
                    f"Error {response.status_code}: {redact_payload(response.text)} "
                    f"(attempted doc_num={doc_num}, invoice={invoice_name})"
                )
                frappe.log_error(message=error_msg, title=f"EIMS submission rejected: {invoice_name}")
                log_audit(
                    "Invoice Registration",
                    invoice_type=doctype,
                    invoice=invoice_name,
                    eims_status="Failed",
                    document_number=doc_num,
                    success=False,
                    description="EIRMS rejected the submission",
                    request_brief=(request_body if isinstance(request_body, str) else json.dumps(request_body, separators=(",", ":")))[:2000],
                    response_brief=response.text[:2000],
                )
                return {"status": "Rule Error", "message": error_msg}

        except frappe.ValidationError:
            raise
        except Exception as e:
            frappe.log_error(message=frappe.get_traceback(), title=f"EIMS System Crash: {invoice_name}")
            log_audit(
                "Invoice Registration",
                invoice_type=doctype,
                invoice=invoice_name,
                eims_status="Failed",
                success=False,
                description=f"EIMS system crash during submission: {self._friendly_network_error(e)}",
            )
            return {"status": "Rule Error", "message": self._friendly_network_error(e)}

    @staticmethod
    def _put_if_present(target_dict, key, value):
        if value is not None and str(value).strip() != "":
            target_dict[key] = value

    def build_manual_invoice_payload(self, doc, override_doc_num):
        """Build an EIRMS /v1/register payload for an EIRMS Manual Invoice
        (invoices issued during an EIRMS outage, registered within the 72-hour
        window). Uses SourceSystemType MAN and the same schema as point-of-sale
        invoices, per the confirmed MoR register spec."""
        company = frappe.get_doc("Company", doc.company)
        company_link = f"/app/company/{company.name}"
        default_client = self.get_default_client_data()

        tin = re.sub(r"\D", "", doc.buyer_tin or "")
        transaction_type = "B2B" if tin else "B2C"

        seller = {
            "Tin": self.settings.seller_tin,
            "LegalName": company.custom_seller_legal_name or company.company_name,
            "Email": self._require(company.email, "Email", company.name, company_link),
            "Phone": self._require(company.phone_no, "Phone", company.name, company_link),
            "Region": self._require(company.custom_seller_region_code, "Seller Region Code", company.name, company_link),
            "Wereda": self._require(company.custom_seller_woreda_code, "Seller Wereda Code", company.name, company_link),
            "City": self._require(company.custom_city, "City", company.name, company_link),
        }
        self._put_if_present(seller, "VatNumber", company.custom_vat_number)
        self._put_if_present(seller, "HouseNumber", company.custom_house_number)
        self._put_if_present(seller, "TradeName", company.custom_trade_name)
        self._put_if_present(seller, "SubTin", company.custom_sub_tin)
        self._put_if_present(seller, "Country", company.custom_country)
        self._put_if_present(seller, "Zone", company.custom_zone)
        self._put_if_present(seller, "SubCity", company.custom_sub_city)
        self._put_if_present(seller, "Kebele", company.custom_kebele)
        self._put_if_present(seller, "Locality", company.custom_locality)

        item_list = []
        for idx, row in enumerate(doc.items, start=1):
            qty = float(row.quantity or 1)
            unit_price = float(row.unit_price or 0)
            discount = float(row.discount_amount or 0)
            pre_tax = round(qty * unit_price - discount, 2)
            if pre_tax < 0:
                frappe.throw(
                    f"Manual invoice line '{row.item_description}': pre-tax value cannot be negative."
                )
            tax_rate = float(row.tax_rate or 0)
            tax_amount = round(pre_tax * tax_rate / 100.0, 2)
            line_item = {
                "LineNumber": idx,
                "ItemCode": row.item_description or str(idx),
                "ProductDescription": row.item_description or "string",
                "NatureOfSupplies": "goods",
                "Quantity": qty,
                "UnitPrice": round(unit_price, 6),
                "PreTaxValue": pre_tax,
                "TaxCode": (row.tax_code or "VAT15").strip(),
                "TaxAmount": tax_amount,
                "Unit": "PCS",
                "TotalLineAmount": round(pre_tax + tax_amount, 2),
                "ExciseTaxValue": 0.0,
            }
            if discount:
                line_item["Discount"] = round(discount, 2)
            item_list.append(line_item)

        if not item_list:
            frappe.throw("Manual invoice must contain at least one item line.")

        payload = {
            "Version": "1",
            "TransactionType": transaction_type,
            "DocumentDetails": {
                "DocumentNumber": str(override_doc_num),
                "Date": doc.invoice_date.strftime("%d-%m-%YT00:00:00"),
                "Type": "INV",
            },
            "SellerDetails": seller,
            "SourceSystem": {
                "SystemType": (doc.source_system_type or "MAN").strip(),
                "SystemNumber": default_client.system_number,
                "InvoiceCounter": override_doc_num,
            },
            "PaymentDetails": {
                "Mode": "CASH",
                "PaymentTerm": "IMMEDIATE",
            },
            "ValueDetails": {
                "InvoiceCurrency": doc.currency or "ETB",
                "TaxValue": round(sum(i["TaxAmount"] for i in item_list), 2),
                "TotalValue": round(sum(i["TotalLineAmount"] for i in item_list), 2),
            },
            "ReferenceDetails": {},
            "ItemList": item_list,
        }

        buyer = {}
        if transaction_type == "B2B":
            buyer["Tin"] = tin
        self._put_if_present(buyer, "LegalName", doc.buyer_name)
        self._put_if_present(buyer, "Email", doc.buyer_email)
        self._put_if_present(buyer, "Phone", doc.buyer_phone)
        self._put_if_present(buyer, "IdType", doc.buyer_id_type, )
        self._put_if_present(buyer, "IdNumber", doc.buyer_id_number)
        if buyer:
            payload["BuyerDetails"] = buyer

        return payload

    def submit_manual_invoice(self, manual_invoice_name):
        """Register an EIMS Manual Invoice (72-hour outage backfill) with MoR."""
        doc = frappe.get_doc("EIMS Manual Invoice", manual_invoice_name)
        if doc.status == "Registered":
            return {"status": "Registered", "message": f"Already registered. IRN: {doc.custom_irn}"}

        try:
            self._ensure_service_active()

            existing_num = doc.custom_document_number
            if existing_num:
                doc_num = int(existing_num)
                is_resend = True
            else:
                doc_num = self._peek_next_document_number()
                is_resend = False

            token = self.get_valid_token()
            default_client = self.get_default_client_data()

            clean_url = self.settings.base_url.strip().rstrip('/')
            register_url = f"{clean_url}/v1/register"
            is_https = register_url.lower().startswith("https://")

            response = None
            while True:
                invoice_payload = self.build_manual_invoice_payload(doc, override_doc_num=doc_num)
                auth_headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                    "apikey": self.settings.get_password("api_key"),
                }
                json_string_payload = json.dumps(invoice_payload, separators=(",", ":"))
                if is_https:
                    request_body = self._build_signed_envelope(json_string_payload, default_client)
                else:
                    request_body = json_string_payload

                response = self._post_with_retry(register_url, request_body, auth_headers, timeout=15)
                if response.status_code == 401:
                    token = self.get_valid_token(force_refresh=True)
                    auth_headers["Authorization"] = f"Bearer {token}"
                    response = self._post_with_retry(register_url, request_body, auth_headers, timeout=15)

                if response.status_code in (200, 201):
                    res_json = response.json()
                    body_data = res_json.get("body", {})
                    irn = body_data.get("irn")
                    qr_code_url = self._save_qr_file(
                        manual_invoice_name, body_data.get("signedQR"), "EIMS Manual Invoice"
                    )
                    frappe.db.set_value("EIMS Manual Invoice", manual_invoice_name, {
                        "status": "Registered",
                        "custom_irn": irn,
                        "custom_qr_code_url": qr_code_url,
                        "custom_document_number": doc_num,
                        "registered_at": now_datetime(),
                        "error_log": "",
                    }, update_modified=True)
                    if doc_num > int(self.settings.last_document_number or 0):
                        self._commit_document_number(doc_num)
                    frappe.db.commit()
                    log_audit(
                        "Manual Invoice Registration",
                        invoice_type="EIMS Manual Invoice",
                        invoice=manual_invoice_name,
                        eims_status="Registered",
                        document_number=doc_num,
                        success=True,
                        description="Outage/manual invoice registered with EIRMS",
                        request_brief=(request_body if isinstance(request_body, str) else json.dumps(request_body, separators=(",", ":")))[:2000],
                        response_brief=response.text[:2000],
                    )
                    return {"status": "Registered", "message": f"Manual invoice registered. IRN: {irn}"}

                expected_num = self._parse_expected_doc_num(response.text)

                # ER-GE-1 auto-advance for manual invoices too
                is_erge1 = '"1":"Internal Server Error, ER-GE-1"' in (response.text or "")
                if is_erge1:
                    next_num = self._peek_next_document_number()
                    if next_num != doc_num:
                        frappe.logger().info(
                            f"ER-GE-1 (manual) for doc {doc_num}, auto-advancing to {next_num}"
                        )
                        self._commit_document_number(next_num - 1)
                        doc_num = next_num
                        frappe.db.set_value(
                            "EIMS Manual Invoice", manual_invoice_name,
                            "custom_document_number", doc_num, update_modified=True,
                        )
                        frappe.db.commit()
                        continue

                if expected_num is not None and expected_num != doc_num:
                    self._commit_document_number(expected_num - 1)
                    doc_num = expected_num
                    frappe.db.set_value(
                        "EIMS Manual Invoice", manual_invoice_name,
                        "custom_document_number", doc_num, update_modified=True,
                    )
                    frappe.db.commit()
                    continue

                if expected_num is not None and expected_num == doc_num and is_resend and doc.custom_irn:
                    frappe.db.set_value("EIMS Manual Invoice", manual_invoice_name, {
                        "status": "Registered",
                        "error_log": "",
                    }, update_modified=True)
                    frappe.db.commit()
                    return {"status": "Registered", "message": f"Already registered. IRN: {doc.custom_irn}"}
                break

            error_msg = (
                f"Error {response.status_code}: {redact_payload(response.text)} "
                f"(attempted doc_num={doc_num}, manual_invoice={manual_invoice_name})"
            ) if response else "No response"
            frappe.db.set_value("EIMS Manual Invoice", manual_invoice_name, {
                "status": "Failed",
                "error_log": redact_payload(response.text) if response else redact_payload(error_msg),
            }, update_modified=True)
            frappe.db.commit()
            frappe.log_error(message=error_msg, title=f"EIMS manual submission rejected: {manual_invoice_name}")
            log_audit(
                "Manual Invoice Registration",
                invoice_type="EIMS Manual Invoice",
                invoice=manual_invoice_name,
                eims_status="Failed",
                document_number=doc_num,
                success=False,
                description="EIRMS rejected the manual invoice submission",
                response_brief=redact_payload(response.text) if response else redact_payload(error_msg),
            )
            return {"status": "Failed", "message": error_msg}

        except frappe.ValidationError:
            raise
        except Exception as e:
            frappe.log_error(message=frappe.get_traceback(), title=f"EIMS Manual Submission Crash: {manual_invoice_name}")
            log_audit(
                "Manual Invoice Registration",
                invoice_type="EIMS Manual Invoice",
                invoice=manual_invoice_name,
                eims_status="Failed",
                success=False,
                description=f"EIMS system crash during manual submission: {self._friendly_network_error(e)}",
            )
            return {"status": "Failed", "message": self._friendly_network_error(e)}

    @staticmethod
    def _filter_known_fields(doctype, updates):
        """Drop any key the target doctype doesn't have as a field.
        Registration must survive a missing optional tracking column
        (e.g. custom_mor_total_value on an environment where the patch
        has not run yet) instead of crashing with a DB 1054 error."""
        try:
            meta = frappe.get_meta(doctype)
            return {k: v for k, v in updates.items() if meta.has_field(k)}
        except Exception:
            return updates

    def _save_qr_file(self, invoice_name, signed_qr_base64, doctype="Sales Invoice"):
        qr_code_url = ""
        if not signed_qr_base64:
            return qr_code_url
        try:
            file_name = f"qr_{invoice_name}.png"
            old_file_id = frappe.db.get_value("File", {
                "attached_to_doctype": doctype,
                "attached_to_name": invoice_name,
                "file_name": file_name
            }, "name")
            if old_file_id:
                frappe.delete_doc("File", old_file_id, ignore_permissions=True)

            qr_file = frappe.get_doc({
                "doctype": "File",
                "file_name": file_name,
                "attached_to_doctype": doctype,
                "attached_to_name": invoice_name,
                "content": base64.b64decode(signed_qr_base64),
                "is_private": 0
            })
            qr_file.insert(ignore_permissions=True)
            qr_code_url = qr_file.file_url
        except Exception as qr_err:
            frappe.log_error(message=str(qr_err), title="EIMS QR Image Processing Error")
        return qr_code_url

    def _post_with_retry(self, url, data, headers, timeout, max_retries=4):
        attempt = 0
        while True:
            response = requests.post(url, data=data, headers=headers, timeout=timeout)
            if response.status_code != 429:
                return response
            attempt += 1
            if attempt >= max_retries:
                return response
            wait_seconds = min(2 ** attempt, 30)
            time.sleep(wait_seconds)

    def _register_single_leftover(self, doc, assigned_num, prev_irn, default_client, token):

        payload = self.build_invoice_payload(
            doc, override_doc_num=assigned_num, override_prev_irn=prev_irn
        )
        clean_url = self.settings.base_url.strip().rstrip('/')
        register_url = f"{clean_url}/v1/register"
        is_https = register_url.lower().startswith("https://")

        json_string_payload = json.dumps(payload, separators=(",", ":"))
        if is_https:
            request_body = self._build_signed_envelope(json_string_payload, default_client)
        else:
            request_body = json_string_payload

        auth_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "apikey": self.settings.get_password("api_key"),
        }

        response = self._post_with_retry(register_url, request_body, auth_headers, 15)
        eims_logger.debug(
            "Single-invoice fallback for %s (DocNum %s) - status: %s body: %s",
            doc.name, assigned_num, response.status_code, redact_payload(response.text)
        )

        if response.status_code == 401:
            token = self.get_valid_token(force_refresh=True)
            auth_headers["Authorization"] = f"Bearer {token}"
            response = self._post_with_retry(register_url, request_body, auth_headers, 15)

        return response

    def _friendly_network_error(self, e):
        """Map connection-level failures to a clean, actionable message that
        points the user at the EIMS Setting Base URL instead of dumping the
        raw requests traceback (e.g. 'System Crash Error: HTTPConnectionPool
        ... ConnectTimeoutError ...')."""
        clean_url = (self.settings.base_url or "").strip().rstrip("/")
        if isinstance(e, requests.exceptions.ConnectTimeout):
            return (
                f"Could not reach the EIRMS server at {clean_url} — the connection timed out. "
                f"Check that the Base URL in <b>EIMS Setting</b> is correct and that the EIRMS "
                f"server is reachable from this machine."
            )
        if isinstance(e, requests.exceptions.ConnectionError):
            return (
                f"Could not connect to the EIRMS server at {clean_url}. "
                f"Check that the Base URL in <b>EIMS Setting</b> is correct, the server is running, "
                f"and that this machine can reach it."
            )
        if isinstance(e, requests.exceptions.Timeout):
            return (
                f"The EIRMS server at {clean_url} did not respond in time. "
                f"Check your network connection and the Base URL in <b>EIMS Setting</b>."
            )
        return str(e)

    def submit_bulk_invoices(self, invoice_names):
        results_map = {}
        successes = 0
        failures = 0
        pending_count = 0
        logs = []

        try:
            token = self.get_valid_token()
        except Exception as e:
            eims_logger.error("Auth failed before bulk submission: %s", str(e))
            for name in invoice_names:
                results_map[name] = {"status": "Rule Error", "message": str(e)}
            return {
                "status": "Failed",
                "message": f"EIMS authentication failed before bulk submission: {str(e)}",
                "results": results_map
            }

        try:
            self._ensure_service_active()
        except frappe.PermissionError as e:
            for name in invoice_names:
                results_map[name] = {"status": "Rule Error", "message": str(e)}
            return {"status": "Failed", "message": str(e), "results": results_map}

        default_client = self.get_default_client_data()

        docs = []
        for name in invoice_names:
            try:
                doc = frappe.get_doc("Sales Invoice", name)
                docs.append(doc)
            except Exception as load_err:
                results_map[name] = {"status": "Rule Error", "message": str(load_err)}
                failures += 1
                logs.append(f"[{name}] Failed -> {str(load_err)}")

        docs.sort(key=lambda d: d.creation)
        pending = docs

        current_doc_num = self._peek_next_document_number()
        prev_irn = self._lookup_irn_for_doc_num(current_doc_num - 1)

        clean_url = self.settings.base_url.strip().rstrip('/')
        register_url = f"{clean_url}/v1/bulkRegister"
        is_https = register_url.lower().startswith("https://")

        eims_logger.debug("register_url=%s", register_url)

        while pending:

            if len(pending) < EIMS_MIN_BULK_SIZE:
                doc = pending[0]
                assigned_num = current_doc_num
                try:
                    response = self._register_single_leftover(
                        doc, assigned_num, prev_irn, default_client, token
                    )
                except frappe.ValidationError as ve:
                    results_map[doc.name] = {"status": "Rule Error", "message": str(ve)}
                    frappe.db.set_value("Sales Invoice", doc.name, "custom_eims_status", "Failed", update_modified=True)
                    frappe.db.commit()
                    failures += 1
                    logs.append(f"[{doc.name}] Failed -> {str(ve)}")
                    pending = []
                    break

                if response.status_code in (200, 201):
                    res_json = response.json()
                    body_data = res_json.get("body", {}) if isinstance(res_json, dict) else {}
                    irn = body_data.get("irn")
                    if irn:
                        signed_qr_base64 = body_data.get("signedQR")
                        qr_code_url = self._save_qr_file(doc.name, signed_qr_base64)
                        frappe.db.set_value("Sales Invoice", doc.name, {
                            "custom_irn": irn,
                            "custom_qr_code_url": qr_code_url,
                            "custom_eims_status": "Registered",
                            "custom_document_number": assigned_num
                        }, update_modified=True)
                        if assigned_num > int(self.settings.last_document_number or 0):
                            self._commit_document_number(assigned_num)
                        results_map[doc.name] = {"status": "Transmitted", "message": f"Successfully registered. IRN: {irn}"}
                        successes += 1
                        logs.append(f"[{doc.name}] Success -> IRN: {irn} (DocNum: {assigned_num}, via single-invoice fallback)")
                    else:
                        conversation_id = res_json.get("conversationId") if isinstance(res_json, dict) else None
                        frappe.db.set_value("Sales Invoice", doc.name, {
                            "custom_eims_status": "Pending",
                            "custom_document_number": assigned_num,
                            "custom_conversation_id": conversation_id
                        }, update_modified=True)
                        results_map[doc.name] = {
                            "status": "Pending",
                            "message": f"Submitted for async processing (conversationId: {conversation_id}). Awaiting confirmation callback."
                        }
                        pending_count += 1
                        logs.append(f"[{doc.name}] Pending -> submitted via single-invoice fallback, awaiting callback (DocNum {assigned_num})")
                else:
                    error_msg = f"Error {response.status_code}: {redact_payload(response.text)}"
                    frappe.db.set_value("Sales Invoice", doc.name, "custom_eims_status", "Failed", update_modified=True)
                    results_map[doc.name] = {"status": "Rule Error", "message": error_msg}
                    failures += 1
                    logs.append(f"[{doc.name}] Failed -> {error_msg}")

                frappe.db.commit()
                pending = []
                break

            batch_docs = []
            batch_payloads = []
            running_doc_num = current_doc_num
            running_prev_irn = prev_irn

            for doc in pending:
                try:
                    payload = self.build_invoice_payload(
                        doc, override_doc_num=running_doc_num, override_prev_irn=running_prev_irn
                    )
                    batch_payloads.append(payload)
                    batch_docs.append((doc, running_doc_num))
                except frappe.ValidationError as ve:
                    results_map[doc.name] = {"status": "Rule Error", "message": str(ve)}
                    frappe.db.set_value("Sales Invoice", doc.name, "custom_eims_status", "Failed", update_modified=True)
                    frappe.db.commit()
                    failures += 1
                    logs.append(f"[{doc.name}] Failed -> {str(ve)}")
                    continue
                running_doc_num += 1
                running_prev_irn = None

            if not batch_payloads:
                pending = []
                break

            try:
                auth_headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                    "apikey": self.settings.get_password("api_key"),
                }

                json_string_payload = json.dumps(batch_payloads, separators=(",", ":"))
                if is_https:
                    request_body = self._build_signed_envelope(json_string_payload, default_client)
                else:
                    request_body = json_string_payload

                response = self._post_with_retry(register_url, request_body, auth_headers, 30)

                eims_logger.debug("Response status: %s", response.status_code)
                eims_logger.debug("Response body (redacted): %s", redact_payload(response.text))

                if response.status_code == 401:
                    token = self.get_valid_token(force_refresh=True)
                    auth_headers["Authorization"] = f"Bearer {token}"
                    response = self._post_with_retry(register_url, request_body, auth_headers, 30)
                    eims_logger.debug("Retry after 401 - status: %s body: %s", response.status_code, redact_payload(response.text))

                if response.status_code not in (200, 201):
                    error_msg = f"Error {response.status_code}: {redact_payload(response.text)}"
                    frappe.log_error(message=error_msg, title="EIMS Bulk Submission Rejected")
                    eims_logger.error("Bulk submission rejected: %s", error_msg)
                    for doc, assigned_num in batch_docs:
                        results_map[doc.name] = {"status": "Rule Error", "message": error_msg}
                        frappe.db.set_value("Sales Invoice", doc.name, "custom_eims_status", "Failed", update_modified=True)
                        failures += 1
                        logs.append(f"[{doc.name}] Failed -> {error_msg}")
                    frappe.db.commit()
                    pending = []
                    break

                res_json = response.json()

                is_async_envelope = (
                    isinstance(res_json, dict)
                    and "body" not in res_json
                    and "data" not in res_json
                    and "conversationId" in res_json
                )

                if is_async_envelope:
                    conversation_id = res_json.get("conversationId")
                    for doc, assigned_num in batch_docs:
                        frappe.db.set_value("Sales Invoice", doc.name, {
                            "custom_eims_status": "Pending",
                            "custom_document_number": assigned_num,
                            "custom_conversation_id": conversation_id
                        }, update_modified=True)
                        results_map[doc.name] = {
                            "status": "Pending",
                            "message": f"Submitted for async processing (conversationId: {conversation_id}). Awaiting confirmation callback."
                        }
                        pending_count += 1
                        logs.append(f"[{doc.name}] Pending -> submitted, conversationId {conversation_id} (DocNum {assigned_num})")
                    frappe.db.commit()
                    pending = []
                    break

                if isinstance(res_json, dict):
                    res_items = res_json.get("body", res_json.get("data", [res_json]))
                else:
                    res_items = res_json

                if not isinstance(res_items, list):
                    res_items = [res_items]

                error_index = None
                last_committed_irn = prev_irn

                for idx, (doc, assigned_num) in enumerate(batch_docs):
                    if idx >= len(res_items):
                        error_index = idx
                        break

                    item = res_items[idx]
                    if not isinstance(item, dict):
                        error_index = idx
                        break

                    if ("conversionId" in item or "conversationId" in item) and "irn" not in item and "ruleError" not in item and item.get("status") != "ERROR":
                        error_index = idx
                        break

                    irn = item.get("irn")
                    item_status = item.get("status")

                    if irn and item_status == "A":
                        signed_qr_base64 = item.get("signedQR")
                        qr_code_url = self._save_qr_file(doc.name, signed_qr_base64)

                        frappe.db.set_value("Sales Invoice", doc.name, {
                            "custom_irn": irn,
                            "custom_qr_code_url": qr_code_url,
                            "custom_eims_status": "Registered",
                            "custom_document_number": assigned_num
                        }, update_modified=True)
                        if assigned_num > int(self.settings.last_document_number or 0):
                            self._commit_document_number(assigned_num)
                        results_map[doc.name] = {
                            "status": "Transmitted",
                            "message": f"Successfully registered. IRN: {irn}"
                        }
                        successes += 1
                        logs.append(f"[{doc.name}] Success -> IRN: {irn} (DocNum: {assigned_num})")
                        last_committed_irn = irn
                    else:
                        rule_error = item.get("ruleError")
                        if rule_error:
                            error_detail = redact_payload(json.dumps(rule_error))
                        else:
                            error_detail = redact_payload(json.dumps(item))

                        frappe.db.set_value("Sales Invoice", doc.name, "custom_eims_status", "Failed", update_modified=True)
                        results_map[doc.name] = {
                            "status": "Rule Error",
                            "message": f"Document number {assigned_num} rejected: {error_detail}"
                        }
                        failures += 1
                        logs.append(f"[{doc.name}] Failed -> {error_detail} (DocNum {assigned_num} recycled)")
                        error_index = idx
                        break

                frappe.db.commit()

                if error_index is None:
                    pending = []
                else:
                    remaining = [d for d, n in batch_docs[error_index + 1:]]
                    pending = remaining
                    current_doc_num = batch_docs[error_index][1]
                    prev_irn = last_committed_irn

            except Exception as batch_err:
                eims_logger.exception("Bulk submission system crash")
                friendly_msg = self._friendly_network_error(batch_err)
                for doc, assigned_num in batch_docs:
                    if doc.name not in results_map:
                        results_map[doc.name] = {"status": "Rule Error", "message": friendly_msg}
                        frappe.db.set_value("Sales Invoice", doc.name, "custom_eims_status", "Failed", update_modified=True)
                        failures += 1
                        logs.append(f"[{doc.name}] Failed -> {friendly_msg}")
                frappe.db.commit()
                pending = []

        if failures == 0 and pending_count == 0:
            overall_status = "Transmitted"
        elif failures == 0 and pending_count > 0:
            overall_status = "Pending" if successes == 0 else "Partially Transmitted"
        elif successes > 0 or pending_count > 0:
            overall_status = "Partially Transmitted"
        else:
            overall_status = "Failed"

        summary_text = (
            f"Bulk Processing Complete.\n"
            f"Total processed: {len(invoice_names)} | Success: {successes} | "
            f"Pending (awaiting callback): {pending_count} | Failures: {failures}\n\n"
            f"Execution Logs:\n" + "\n".join(logs)
        )

        log_audit(
            "Bulk Registration",
            eims_status=overall_status,
            success=failures == 0 and pending_count == 0,
            description=f"Bulk EIRMS submission: {len(invoice_names)} invoices. {successes} ok, {pending_count} pending, {failures} failed.",
        )

        return {
            "status": overall_status,
            "message": summary_text,
            "results": results_map
        }

import frappe
import requests
import re
import base64
import json
import logging
import os
from pathlib import Path
from frappe.utils import get_datetime, now_datetime
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding


def _get_eims_logger():
    logger = logging.getLogger("eims_connector")
    if not logger.handlers:
        log_dir = frappe.utils.get_site_path("logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "eims_connector.log")
        handler = logging.FileHandler(log_path)
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
    return logger


eims_logger = _get_eims_logger()

EIMS_MIN_BULK_SIZE = 2


class EIMSConnector:
    def __init__(self):
        self.settings = frappe.get_single("EIMS Setting")
        self.headers = {"Content-Type": "application/json"}

    def _require(self, value, field_label, doc_label, link=None, title="EIMS Schema Validation Error"):
        if value is None or str(value).strip() == "":
            location = f"<a href='{link}'>{doc_label}</a>" if link else f"<b>{doc_label}</b>"
            frappe.throw(
                f"Validation Error on {location}:<br><br>"
                f"<b>{field_label}</b> is required and cannot be empty for EIMS submission.",
                title=title
            )
        return value

    def get_default_client_data(self):
        if not self.settings.client_data_list:
            frappe.throw("No client configuration found in EIMS Settings.")

        for row in self.settings.client_data_list:
            if row.is_default == 1:
                return frappe.get_doc(row.doctype, row.name)

        frappe.throw("No default configuration row selected in EIMS Settings.")

    def _normalize_pem(self, raw_text, label):
        text = raw_text.strip()
        text = text.replace("\\n", "\n")
        begin_marker = f"-----BEGIN {label}-----"
        end_marker = f"-----END {label}-----"
        body = text.replace(begin_marker, "").replace(end_marker, "")
        body = body.replace("\n", " ")
        base64_chars = "".join(body.split())
        wrapped_lines = [base64_chars[i:i + 64] for i in range(0, len(base64_chars), 64)]
        rebuilt_pem = begin_marker + "\n" + "\n".join(wrapped_lines) + "\n" + end_marker + "\n"
        return rebuilt_pem

    def _sign_data(self, data_bytes, default_client):
        decrypted_private_key = default_client.get_password("private_key")
        certificate_text = default_client.public_certificate

        if not decrypted_private_key or not certificate_text:
            frappe.throw(
                "Private Key and Public Certificate must be configured on the "
                "default Client Data row to use HTTPS EIMS endpoints.",
                title="EIMS Configuration Error"
            )

        normalized_key_text = self._normalize_pem(decrypted_private_key, "PRIVATE KEY")

        try:
            private_key = serialization.load_pem_private_key(
                normalized_key_text.encode("utf-8"), password=None
            )
        except ValueError:
            frappe.throw(
                "Stored Private Key could not be parsed as a valid PEM key. "
                "Please re-paste the full key (including BEGIN/END lines) into "
                "the Private Key field on the default Client Data row.",
                title="EIMS Configuration Error"
            )

        signature = private_key.sign(
            data_bytes,
            padding.PKCS1v15(),
            hashes.SHA512()
        )
        signature_b64 = base64.b64encode(signature).decode()
        certificate_b64 = base64.b64encode(certificate_text.encode("utf-8")).decode()

        return signature_b64, certificate_b64

    def _build_signed_envelope(self, json_string, default_client):
        data_bytes = json_string.encode("utf-8")
        signature_b64, certificate_b64 = self._sign_data(data_bytes, default_client)

        envelope = {
            "request": json.loads(json_string),
            "signature": signature_b64,
            "certificate": certificate_b64
        }
        envelope_string = json.dumps(envelope, separators=(",", ":"), ensure_ascii=False)
        return envelope_string

    def _build_signed_item(self, payload_dict, default_client):
        json_string = json.dumps(payload_dict, separators=(",", ":"))
        data_bytes = json_string.encode("utf-8")
        signature_b64, certificate_b64 = self._sign_data(data_bytes, default_client)

        return {
            "request": json.loads(json_string),
            "signature": signature_b64,
            "certificate": certificate_b64
        }

    def get_valid_token(self, force_refresh=False):
        if (not force_refresh and self.settings.current_access_token
                and self.settings.token_expiry
                and get_datetime(self.settings.token_expiry) > now_datetime()):
            return self.settings.current_access_token

        default_client = self.get_default_client_data()

        decrypted_id = default_client.get_password("client_id")
        decrypted_secret = default_client.get_password("client_secret")
        decrypted_apikey = self.settings.get_password("api_key")

        payload = {
            "clientId": decrypted_id,
            "clientSecret": decrypted_secret,
            "apikey": decrypted_apikey,
            "tin": self.settings.seller_tin
        }

        clean_url = self.settings.base_url.strip().rstrip('/')
        login_url = f"{clean_url}/auth/login"

        json_string = json.dumps(payload, separators=(",", ":"))
        data_bytes = json_string.encode("utf-8")

        is_https = login_url.lower().startswith("https://")

        if is_https:
            envelope_string = self._build_signed_envelope(json_string, default_client)
            response = requests.post(
                login_url,
                data=envelope_string.encode("utf-8"),
                headers=self.headers,
                timeout=15,
                verify=False
            )
        else:
            response = requests.post(
                login_url,
                data=data_bytes,
                headers=self.headers,
                timeout=10
            )

        if response.status_code == 200:
            res_data = response.json()
            token = res_data.get("data", {}).get("accessToken")

            self.settings.current_access_token = token
            self.settings.token_expiry = frappe.utils.add_to_date(now_datetime(), minutes=60)
            self.settings.save(ignore_permissions=True)
            frappe.db.commit()

            return token
        else:
            frappe.throw(f"EIMS Authentication Failed (Status {response.status_code}): {response.text}")

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
        return ""

    def _get_max_document_number(self):
        row = frappe.db.sql(
            """SELECT MAX(CAST(custom_document_number AS UNSIGNED))
               FROM `tabSales Invoice`
               WHERE custom_document_number IS NOT NULL AND custom_document_number != '' AND custom_eims_status IN ('Registered', 'Pending')""",
        )
        return int(row[0][0]) if row and row[0][0] else 0

    def build_invoice_payload(self, invoice_doc, override_doc_num=None, override_prev_irn=None):
        company = frappe.get_doc("Company", invoice_doc.company)
        company_link = f"/app/company/{company.name}"

        customer_type = frappe.db.get_value("Customer", invoice_doc.customer, "customer_type")
        transaction_type = "B2B" if customer_type in ["Company", "Partnership"] else "B2C"

        if not frappe.db.exists("Customer Details", invoice_doc.customer):
            frappe.throw(
                f"Missing Record: Please create a <b>Customer Details</b> document for Customer "
                f"<b>{invoice_doc.customer}</b> before proceeding.",
                title="EIMS Schema Validation Error"
            )
        customer = frappe.get_doc("Customer", invoice_doc.customer)
        customer_link = f"/app/customer/{customer.name}"
        cust_details = frappe.get_doc("Customer Details", invoice_doc.customer)
        cust_link = f"/app/customer-details/{cust_details.name}"

        raw_tin = cust_details.tin_number or ""
        clean_tin = re.sub(r"\D", "", str(raw_tin))
        if not clean_tin or len(clean_tin) < 10 or len(clean_tin) > 20:
            frappe.throw(
                f"Validation Error on <a href='{cust_link}'>Customer Details ({cust_details.name})</a>:<br><br>"
                f"<b>TIN Number</b> must be purely numeric and between 10 and 20 digits long. Found: '{raw_tin}'",
                title="EIMS Schema Error: Invalid TIN"
            )

        buyer_email = (cust_details.email or "").strip()
        email_pattern = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$")
        if not buyer_email or len(buyer_email) < 6 or not email_pattern.match(buyer_email):
            frappe.throw(
                f"Validation Error on <a href='{cust_link}'>Customer Details ({cust_details.name})</a>:<br><br>"
                f"<b>Email</b> is invalid or too short. It must match a standard email format (e.g., info@domain.com). "
                f"Found: '{buyer_email}'",
                title="EIMS Schema Error: Invalid Email"
            )

        buyer_region = (cust_details.region or "").strip()
        if not buyer_region or not buyer_region.isdigit() or not (1 <= len(buyer_region) <= 3):
            frappe.throw(
                f"Validation Error on <a href='{cust_link}'>Customer Details ({cust_details.name})</a>:<br><br>"
                f"<b>Region</b> must be a numeric code string between 1 and 3 digits (e.g., '13'). "
                f"Found: '{buyer_region}'",
                title="EIMS Schema Error: Invalid Region Code"
            )

        seller_vat_number = self._require(company.custom_vat_number, "VAT Number", company.name, company_link)
        seller_email = self._require(company.email, "Email", company.name, company_link)
        seller_phone = self._require(company.phone_no, "Phone", company.name, company_link)
        seller_region = self._require(company.custom_seller_region_code, "Seller Region Code", company.name, company_link)
        seller_wereda = self._require(company.custom_seller_woreda_code, "Seller Wereda Code", company.name, company_link)
        seller_city = self._require(company.custom_city, "City", company.name, company_link)
        seller_house_number = self._require(company.custom_house_number, "House Number", company.name, company_link)

        buyer_city = self._require(cust_details.city, "City", cust_details.name, cust_link)
        buyer_country = self._require(cust_details.country, "Country", cust_details.name, cust_link)
        buyer_zone = self._require(cust_details.zone, "Zone", cust_details.name, cust_link)
        buyer_kebele = self._require(cust_details.kebele, "Kebele", cust_details.name, cust_link)
        buyer_woreda = self._require(cust_details.woreda, "Wereda", cust_details.name, cust_link)

        buyer_id_number = cust_details.id_number
        buyer_id_type = cust_details.id_type
        if transaction_type == "B2C":
            buyer_id_number = self._require(buyer_id_number, "ID Number", cust_details.name, cust_link)
            buyer_id_type = self._require(buyer_id_type, "ID Type", cust_details.name, cust_link)
        buyer_vat_number = frappe.db.get_value("Customer", invoice_doc.customer, "custom_vat_number")
        if not buyer_vat_number:
            frappe.throw(
                f"Validation Error on <a href='{customer_link}'>Customer ({customer.name})</a>:<br><br>"
                f"<b>VAT Number</b> is required for EIMS submission.",
                title="EIMS Schema Error: Missing VAT Number"
            )

        if override_doc_num is not None:
            doc_num = override_doc_num
        else:
            doc_num = int(invoice_doc.custom_document_number or 1)

        if override_prev_irn is not None:
            prev_irn = override_prev_irn
        else:
            prev_irn = self._lookup_irn_for_doc_num(doc_num - 1)

        cashier_name = "AAA"
        sales_team_entries = invoice_doc.get("sales_team")
        if sales_team_entries:
            cashier_name = sales_team_entries[0].sales_person or "AAA"

        payment_mode = "CASH"
        payment_entries = invoice_doc.get("payments")
        if payment_entries:
            payment_mode = payment_entries[0].mode_of_payment or "CASH"
        raw_phone = cust_details.phone or invoice_doc.contact_mobile
        clean_phone = raw_phone.replace("+251", "0").replace(" ", "")
        if not clean_phone.startswith("0"):
            clean_phone = "0" + clean_phone

        default_client = self.get_default_client_data()
        payload = {
            "Version": "1",
            "TransactionType": transaction_type,
            "DocumentDetails": {
                "DocumentNumber": str(doc_num),
                "Date": (get_datetime(invoice_doc.posting_date).strftime("%d-%m-%YT00:00:00")
                         if invoice_doc.posting_date else now_datetime().strftime("%d-%m-%YT00:00:00")),
                "Type": "INV"
            },
            "SellerDetails": {
                "Tin": self.settings.seller_tin,
                "VatNumber": seller_vat_number,
                "LegalName": company.custom_seller_legal_name or company.company_name,
                "Email": seller_email,
                "Phone": seller_phone,
                "Region": seller_region,
                "Wereda": seller_wereda,
                "City": seller_city,
                "HouseNumber": seller_house_number
            },
            "BuyerDetails": {
                "City": buyer_city,
                "Email": buyer_email,
                "HouseNumber": cust_details.house_number or "NEW",
                "IdNumber": buyer_id_number or "",
                "IdType": buyer_id_type or "",
                "Tin": clean_tin,
                "LegalName": cust_details.legal_name or invoice_doc.customer_name,
                "Phone": clean_phone,
                "Region": buyer_region,
                "Country": buyer_country,
                "Zone": buyer_zone,
                "Kebele": buyer_kebele,
                "VatNumber": buyer_vat_number,
                "Wereda": buyer_woreda
            },
            "SourceSystem": {
                "SystemType": default_client.system_type,
                "SystemNumber": default_client.system_number,
                "CashierName": cashier_name,
                "SalesPersonName": cashier_name,
                "InvoiceCounter": doc_num
            },
            "PaymentDetails": {
                "Mode": payment_mode.upper(),
                "PaymentTerm": "IMMEDIATE"
            },
            "ValueDetails": {
                "InvoiceCurrency": invoice_doc.currency or "ETB",
                "Discount": float(invoice_doc.discount_amount or 0.0),
                "ExciseValue": 0.0,
                "IncomeWithholdValue": 0.0,
                "TransactionWithholdValue": 0.0,
                "TaxValue": float(invoice_doc.total_taxes_and_charges or 0.0),
                "TotalValue": float(invoice_doc.grand_total or 0.0)
            },
            "ReferenceDetails": {
                "PreviousIrn": prev_irn,
                "RelatedDocument": None
            },
            "ItemList": []
        }

        tax_type = ""
        tax_rate = 0
        tax_entries = invoice_doc.get("taxes")
        if invoice_doc.taxes_and_charges and tax_entries:
            account = tax_entries[0].account_head
            tax_type = frappe.db.get_value("Account", account, "account_name")
            tax_rate = tax_entries[0].rate
        valid_units = {"LTR", "MTR", "101", "PCS", "ROL", "MTS", "PKG", "SET", "KLG"}

        for idx, item in enumerate(invoice_doc.items, start=1):
            base_rate = float(item.base_rate or 0.0)
            qty = float(item.qty or 0.0)

            line_net_amount = float(item.net_amount or 0.0)

            line_tax = round(line_net_amount * (tax_rate / 100), 2)

            raw_uom = str(item.uom or "PCS").strip().upper()

            payload["ItemList"].append({
                "LineNumber": idx,
                "ItemCode": item.item_code,
                "ProductDescription": item.description or item.item_name or "string",
                "NatureOfSupplies": "goods",
                "Quantity": qty,
                "UnitPrice": base_rate,
                "PreTaxValue": round(line_net_amount, 2),
                "TaxCode": tax_type,
                "TaxAmount": line_tax,
                "Discount": float(item.distributed_discount_amount or 0.0),
                "ExciseTaxValue": 0.0,
                "HarmonizationCode": None,
                "Unit": raw_uom if raw_uom in valid_units else "PCS",
                "TotalLineAmount": round(line_net_amount + line_tax, 2)
            })

        self._validate_payload_schema_rules(payload, invoice_doc)
        return payload

    def submit_single_invoice(self, invoice_name):
        try:
            token = self.get_valid_token()
            doc = frappe.get_doc("Sales Invoice", invoice_name)
            invoice_payload = self.build_invoice_payload(doc)

            default_client = self.get_default_client_data()

            auth_headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
                "apikey": self.settings.get_password("api_key"),
            }

            clean_url = self.settings.base_url.strip().rstrip('/')
            register_url = f"{clean_url}/v1/register"
            is_https = register_url.lower().startswith("https://")
            json_string_payload = json.dumps(invoice_payload, separators=(",", ":"))
            if is_https:
                request_body = self._build_signed_envelope(json_string_payload, default_client)
            else:
                request_body = json_string_payload

            response = requests.post(
                register_url,
                data=request_body,
                headers=auth_headers,
                timeout=15
            )

            if response.status_code == 401:
                token = self.get_valid_token(force_refresh=True)
                auth_headers["Authorization"] = f"Bearer {token}"
                response = requests.post(
                    register_url,
                    data=request_body,
                    headers=auth_headers,
                    timeout=15
                )

            if response.status_code in (200, 201):
                res_json = response.json()
                body_data = res_json.get("body", {})
                irn = body_data.get("irn")
                signed_qr_base64 = body_data.get("signedQR")

                qr_code_url = ""
                if signed_qr_base64:
                    try:
                        file_name = f"qr_{invoice_name}.png"
                        old_file_id = frappe.db.get_value("File", {
                            "attached_to_doctype": "Sales Invoice",
                            "attached_to_name": invoice_name,
                            "file_name": file_name
                        }, "name")
                        if old_file_id:
                            frappe.delete_doc("File", old_file_id, ignore_permissions=True)

                        qr_file = frappe.get_doc({
                            "doctype": "File",
                            "file_name": file_name,
                            "attached_to_doctype": "Sales Invoice",
                            "attached_to_name": invoice_name,
                            "content": base64.b64decode(signed_qr_base64),
                            "is_private": 0
                        })
                        qr_file.insert(ignore_permissions=True)
                        qr_code_url = qr_file.file_url
                    except Exception as qr_err:
                        frappe.log_error(message=str(qr_err), title="EIMS QR Image Processing Error")

                frappe.db.set_value("Sales Invoice", invoice_name, {
                    "custom_irn": irn,
                    "custom_qr_code_url": qr_code_url,
                    "custom_eims_status": "Registered"
                }, update_modified=True)

                frappe.db.commit()
                return {"status": "Transmitted", "message": f"Successfully registered. IRN: {irn}"}
            else:
                frappe.db.set_value("Sales Invoice", invoice_name, "custom_eims_status", "Failed", update_modified=True)
                frappe.db.commit()

                error_msg = f"Error {response.status_code}: {response.text}"
                frappe.log_error(message=error_msg, title=f"EIMS submission rejected: {invoice_name}")
                return {"status": "Rule Error", "message": error_msg}

        except frappe.ValidationError:
            raise
        except Exception as e:
            frappe.log_error(message=frappe.get_traceback(), title=f"EIMS System Crash: {invoice_name}")
            return {"status": "Rule Error", "message": f"System Crash Error: {str(e)}"}

    def _save_qr_file(self, invoice_name, signed_qr_base64):
        qr_code_url = ""
        if not signed_qr_base64:
            return qr_code_url
        try:
            file_name = f"qr_{invoice_name}.png"
            old_file_id = frappe.db.get_value("File", {
                "attached_to_doctype": "Sales Invoice",
                "attached_to_name": invoice_name,
                "file_name": file_name
            }, "name")
            if old_file_id:
                frappe.delete_doc("File", old_file_id, ignore_permissions=True)

            qr_file = frappe.get_doc({
                "doctype": "File",
                "file_name": file_name,
                "attached_to_doctype": "Sales Invoice",
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
        import time
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
            doc.name, assigned_num, response.status_code, response.text
        )

        if response.status_code == 401:
            token = self.get_valid_token(force_refresh=True)
            auth_headers["Authorization"] = f"Bearer {token}"
            response = self._post_with_retry(register_url, request_body, auth_headers, 15)

        return response

    def submit_bulk_invoices(self, invoice_names):
        results_map = {}
        successes = 0
        failures = 0
        pending_count = 0
        logs = []

        # eims_logger.debug("=== submit_bulk_invoices START === invoice_names=%s", invoice_names)

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

        current_doc_num = self._get_max_document_number() + 1
        prev_irn = self._lookup_irn_for_doc_num(current_doc_num - 1)

        clean_url = self.settings.base_url.strip().rstrip('/')
        register_url = f"{clean_url}/v1/bulkRegister"
        is_https = register_url.lower().startswith("https://")

        eims_logger.debug("register_url=%s is_https=%s", register_url, is_https)

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
                        results_map[doc.name] = {"status": "Transmitted", "message": f"Successfully registered. IRN: {irn}"}
                        successes += 1
                        logs.append(f"[{doc.name}] Success -> IRN: {irn} (DocNum: {assigned_num}, via single-invoice fallback)")
                    else:
                        # Accepted asynchronously - final result arrives via eims_callback
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
                    error_msg = f"Error {response.status_code}: {response.text}"
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

                if is_https:
                    json_string_payload = json.dumps(batch_payloads, separators=(",", ":"))
                    request_body = self._build_signed_envelope(json_string_payload, default_client)
                else:
                    request_body = json.dumps(batch_payloads, separators=(",", ":"))

                # eims_logger.debug("Batch payloads (unsigned): %s", json.dumps(batch_payloads, indent=2))
                # eims_logger.debug("Request body sent: %s", request_body)
                # eims_logger.debug("Auth headers (apikey redacted): %s", {
                #     k: (v if k != "apikey" else "***redacted***") for k, v in auth_headers.items()
                # })

                response = self._post_with_retry(register_url, request_body, auth_headers, 30)

                eims_logger.debug("Response status: %s", response.status_code)
                eims_logger.debug("Response body: %s", response.text)

                if response.status_code == 401:
                    token = self.get_valid_token(force_refresh=True)
                    auth_headers["Authorization"] = f"Bearer {token}"
                    response = self._post_with_retry(register_url, request_body, auth_headers, 30)
                    eims_logger.debug("Retry after 401 - status: %s body: %s", response.status_code, response.text)

                if response.status_code not in (200, 201):
                    error_msg = f"Error {response.status_code}: {response.text}"
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
                            error_detail = json.dumps(rule_error)
                        else:
                            error_detail = json.dumps(item)

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
                # frappe.log_error(message=frappe.get_traceback(), title="EIMS Bulk Submission System Crash")
                eims_logger.exception("Bulk submission system crash")
                for doc, assigned_num in batch_docs:
                    if doc.name not in results_map:
                        results_map[doc.name] = {"status": "Rule Error", "message": f"System Crash Error: {str(batch_err)}"}
                        frappe.db.set_value("Sales Invoice", doc.name, "custom_eims_status", "Failed", update_modified=True)
                        failures += 1
                        logs.append(f"[{doc.name}] Failed -> System Crash Error: {str(batch_err)}")
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

        # eims_logger.debug("=== submit_bulk_invoices END === %s", summary_text)

        return {
            "status": overall_status,
            "message": summary_text,
            "results": results_map
        }

    def _validate_payload_schema_rules(self, payload, invoice_doc):
        invoice_link = f"/app/sales-invoice/{invoice_doc.name}"

        tax_value = payload["ValueDetails"]["TaxValue"]
        if tax_value < 0:
            frappe.throw(
                f"Validation Error on <a href='{invoice_link}'>Sales Invoice ({invoice_doc.name})</a>:<br><br>"
                f"<b>Total Tax Value</b> cannot be negative for EIMS submission. Found: {tax_value}. "
                f"This usually means the invoice's tax/charges total is negative (e.g. a discount applied "
                f"as a negative tax line). Please review the Taxes and Charges table on this invoice.",
                title="EIMS Schema Error: Negative Tax Value"
            )

        for item in payload["ItemList"]:
            tax_amount = item["TaxAmount"]
            if tax_amount < 0:
                frappe.throw(
                    f"Validation Error on <a href='{invoice_link}'>Sales Invoice ({invoice_doc.name})</a>:<br><br>"
                    f"<b>Tax Amount</b> for item <b>{item['ItemCode']}</b> (line {item['LineNumber']}) "
                    f"cannot be negative for EIMS submission. Found: {tax_amount}. "
                    f"This usually means the invoice's overall tax total is negative, which gets distributed "
                    f"proportionally across line items. Please review the Taxes and Charges table on this invoice.",
                    title="EIMS Schema Error: Negative Tax Amount"
                )

            nature = item["NatureOfSupplies"]
            if nature not in ("goods", "service"):
                frappe.throw(
                    f"Validation Error on <a href='{invoice_link}'>Sales Invoice ({invoice_doc.name})</a>:<br><br>"
                    f"<b>NatureOfSupplies</b> for item <b>{item['ItemCode']}</b> (line {item['LineNumber']}) "
                    f"must be either 'goods' or 'service'. Found: '{nature}'.",
                    title="EIMS Schema Error: Invalid Nature Of Supplies"
                )

            pre_tax_value = item["PreTaxValue"]
            if pre_tax_value < 0:
                frappe.throw(
                    f"Validation Error on <a href='{invoice_link}'>Sales Invoice ({invoice_doc.name})</a>:<br><br>"
                    f"<b>Pre-Tax Value</b> for item <b>{item['ItemCode']}</b> (line {item['LineNumber']}) "
                    f"cannot be negative for EIMS submission. Found: {pre_tax_value}.",
                    title="EIMS Schema Error: Negative Pre-Tax Value"
                )

        discount = payload["ValueDetails"]["Discount"]
        if discount < 0:
            frappe.throw(
                f"Validation Error on <a href='{invoice_link}'>Sales Invoice ({invoice_doc.name})</a>:<br><br>"
                f"<b>Discount</b> cannot be negative for EIMS submission. Found: {discount}.",
                title="EIMS Schema Error: Negative Discount"
            )

        total_value = payload["ValueDetails"]["TotalValue"]
        if total_value < 0:
            frappe.throw(
                f"Validation Error on <a href='{invoice_link}'>Sales Invoice ({invoice_doc.name})</a>:<br><br>"
                f"<b>Total Value</b> cannot be negative for EIMS submission. Found: {total_value}.",
                title="EIMS Schema Error: Negative Total Value"
            )


@frappe.whitelist()
def submit_invoice(invoice_name):
    if not invoice_name:
        frappe.throw("Parameter 'invoice_name' is required.")

    if not frappe.has_permission("Sales Invoice", "submit", doc=invoice_name) \
            and not frappe.has_permission("Sales Invoice", "write", doc=invoice_name):
        frappe.throw("Not permitted to submit this Sales Invoice to EIMS.", frappe.PermissionError)

    connector = EIMSConnector()
    result = connector.submit_single_invoice(invoice_name)
    return result


@frappe.whitelist()
def submit_invoices(invoice_names):
    if not invoice_names:
        frappe.throw("Parameter 'invoice_names' is required.")

    if isinstance(invoice_names, str):
        try:
            invoice_names = json.loads(invoice_names)
        except Exception:
            frappe.throw("Parameter 'invoice_names' must be a JSON array or list of invoice names.")

    if not isinstance(invoice_names, list) or not invoice_names:
        frappe.throw("Parameter 'invoice_names' must be a non-empty list of invoice names.")

    for name in invoice_names:
        if not frappe.has_permission("Sales Invoice", "write", doc=name):
            frappe.throw(f"Not permitted to submit invoice '{name}' to EIMS.", frappe.PermissionError)

    connector = EIMSConnector()
    result = connector.submit_bulk_invoices(invoice_names)
    return result


@frappe.whitelist()
def get_eims_status(invoice_name):
    if not invoice_name:
        frappe.throw("Parameter 'invoice_name' is required.")

    if not frappe.has_permission("Sales Invoice", "read", doc=invoice_name):
        frappe.throw("Not permitted to view this Sales Invoice.", frappe.PermissionError)

    status_data = frappe.db.get_value(
        "Sales Invoice",
        invoice_name,
        ["custom_eims_status", "custom_irn", "custom_qr_code_url"],
        as_dict=True
    )

    if not status_data:
        frappe.throw(f"Sales Invoice '{invoice_name}' not found.")

    return status_data


@frappe.whitelist(allow_guest=True)
def eims_callback():
    try:
        raw_body = frappe.request.get_data(as_text=True)
        eims_logger.debug("Callback received: %s", raw_body)

        if not raw_body or not raw_body.strip():
            eims_logger.debug("Empty callback body received - ignoring.")
            frappe.response["http_status_code"] = 200
            return {"status": "ignored_empty_body"}

        # frappe.log_error(message=raw_body, title="EIMS Callback Received")

        try:
            payload = json.loads(raw_body)
        except (ValueError, TypeError):
            eims_logger.exception("Callback body was not valid JSON")
            frappe.response["http_status_code"] = 400
            return {"status": "invalid_json"}

        items = payload if isinstance(payload, list) else payload.get("body", [payload])
        if not isinstance(items, list):
            items = [items]

        connector = EIMSConnector()
        processed, skipped, failed = 0, 0, 0
        last_doc_num = connector._get_max_document_number()

        for item in items:
            if not isinstance(item, dict):
                skipped += 1
                continue

            doc_no = item.get("documentNumber") or item.get("docNo")
            if not doc_no:
                skipped += 1
                continue

            invoice_name = frappe.db.get_value(
                "Sales Invoice", {"custom_document_number": doc_no}, "name"
            )
            if not invoice_name:
                eims_logger.warning("No Sales Invoice found for doc_no=%s", doc_no)
                skipped += 1
                continue

            irn = item.get("irn")
            item_status = item.get("status")

            try:
                if irn and item_status == "A":
                    signed_qr_base64 = item.get("signedQR")
                    qr_code_url = connector._save_qr_file(invoice_name, signed_qr_base64)

                    frappe.db.set_value("Sales Invoice", invoice_name, {
                        "custom_irn": irn,
                        "custom_qr_code_url": qr_code_url,
                        "custom_eims_status": "Registered",
                        "custom_conversation_id": item.get("conversationId") or item.get("conversionId"),
                        "custom_document_number": doc_no,
                    }, update_modified=True)

                    try:
                        last_doc_num = max(last_doc_num, int(doc_no))
                    except (TypeError, ValueError):
                        pass

                    child_name = frappe.db.get_value(
                        "Invoice List",
                        {"sales_invoice": invoice_name, "parenttype": "Invoice Registration"},
                        "name",
                    )
                    if child_name:
                        frappe.db.set_value(
                            "Invoice List", child_name, "status", "Transmitted",
                            update_modified=True,
                        )
                    else:
                        eims_logger.warning(
                            "No Invoice List row found for Sales Invoice %s (doc_no=%s)",
                            invoice_name, doc_no,
                        )

                    processed += 1

                else:
                    rule_error = item.get("ruleError")
                    error_detail = json.dumps(rule_error) if rule_error else json.dumps(item)

                    last_doc_num += 1
                    frappe.db.set_value("Sales Invoice", invoice_name, {
                        "custom_eims_status": "Failed",
                        "custom_document_number": last_doc_num,
                    }, update_modified=True)
                    frappe.log_error(message=error_detail, title=f"EIMS Callback Rejection: {invoice_name}")
                    failed += 1

            except Exception:
                frappe.log_error(
                    message=frappe.get_traceback(),
                    title=f"EIMS Callback Item Error: {invoice_name}",
                )
                failed += 1
                continue

        frappe.db.commit()
        eims_logger.debug(
            "Callback processed: %d ok, %d skipped, %d failed", processed, skipped, failed
        )
        frappe.response["http_status_code"] = 200
        return {"status": "received", "processed": processed, "skipped": skipped, "failed": failed}

    except Exception:
        frappe.db.rollback()
        frappe.log_error(message=frappe.get_traceback(), title="EIMS Callback Processing Error")
        eims_logger.exception("Callback processing error")
        frappe.response["http_status_code"] = 500
        return {"status": "error"}
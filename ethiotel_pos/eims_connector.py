# ethio_telecom_pos_app/eims_connector.py
import frappe
import requests
import re
import base64  
from frappe.utils import get_datetime, now_datetime
import json

class EIMSConnector:
    def __init__(self):
        self.settings = frappe.get_single("EIMS Setting")
        self.headers = {"Content-Type": "application/json"}
        
    def get_valid_token(self, force_refresh=False):
        """Fetches a cached JWT token or renews it if expired or forced"""
        if not force_refresh and self.settings.current_access_token and self.settings.token_expiry and get_datetime(self.settings.token_expiry) > now_datetime():
            return self.settings.current_access_token
            
        decrypted_secret = self.settings.get_password("client_secrete")
        decrypted_apikey = self.settings.get_password("api_key")
        
        payload = {
            "clientId": self.settings.client_id,
            "clientSecret": decrypted_secret,
            "apikey": decrypted_apikey,
            "tin": self.settings.seller_tin
        }
        
        clean_url = self.settings.base_url.strip().rstrip('/')
        response = requests.post(f"{clean_url}/auth/login", json=payload, headers=self.headers, timeout=10)
        
        if response.status_code == 200:
            res_data = response.json()
            token = res_data.get("data", {}).get("accessToken")
            
            self.settings.current_access_token = token
            self.settings.token_expiry = frappe.utils.add_to_date(now_datetime(), minutes=15)
            self.settings.save(ignore_permissions=True)
            frappe.db.commit()
            
            return token
        else:
            frappe.throw(f"EIMS Authentication Failed (Status {response.status_code}): {response.text}")

    def build_invoice_payload(self, invoice_doc):
        """Maps an ERPNext standard invoice document into the working verified JSON format."""
        company = frappe.get_doc("Company", invoice_doc.company)
        customer_type = frappe.db.get_value("Customer", invoice_doc.customer, "customer_type")
        transaction_type = "B2B" if customer_type in ["Company", "Partnership"] else "B2C"

        raw_tin = invoice_doc.tax_id or frappe.db.get_value("Customer", invoice_doc.customer, "tax_id") or ""
        clean_tin = re.sub(r"\D", "", str(raw_tin))
        if not clean_tin or len(clean_tin) < 10:
            clean_tin = "0000034558"

        custom_detail_link = frappe.db.get_value("Customer", invoice_doc.customer, "custom_customer_detail")
        cust_details = None
        if custom_detail_link:
            cust_details = frappe.get_doc("Customer Details", custom_detail_link)
        is_det = True if cust_details else False

        doc_num = int(invoice_doc.custom_document_number or 1)
        prev_doc = doc_num - 1
        prev_irn = ""
        if prev_doc > 0:
            db_res = frappe.db.sql(
                """SELECT custom_irn FROM `tabSales Invoice` WHERE custom_document_number = %s AND docstatus = 1 LIMIT 1""", 
                prev_doc, as_dict=1
            )
            if db_res:
                prev_irn = db_res[0].get("custom_irn") or ""

        cashier_name = "AAA"
        sales_team_entries = invoice_doc.get("sales_team")
        if sales_team_entries and len(sales_team_entries) > 0:
            cashier_name = sales_team_entries[0].sales_person or "AAA"

        payment_mode = "CASH"
        payment_entries = invoice_doc.get("payments")
        if payment_entries and len(payment_entries) > 0:
            payment_mode = payment_entries[0].mode_of_payment or "CASH"

        raw_phone = cust_details.phone if (is_det and cust_details.phone) else (invoice_doc.contact_mobile or "0912345678")
        clean_phone = raw_phone.replace("+251", "0").replace(" ", "")
        if not clean_phone.startswith("0"):
            clean_phone = "0" + clean_phone

        payload = {
            "Version": "1",
            "TransactionType": transaction_type,
            "DocumentDetails": {
                "DocumentNumber": str(doc_num),
                "Date": get_datetime(invoice_doc.posting_date).strftime("%d-%m-%YT00:00:00") if invoice_doc.posting_date else now_datetime().strftime("%d-%m-%YT00:00:00"),
                "Type": "INV"
            },
            "SellerDetails": {
                "Tin": self.settings.seller_tin,
                "VatNumber": company.custom_vat_number,
                "LegalName": company.custom_seller_legal_name or company.company_name,
                "Email": company.email or "info@company.com",
                "Phone": company.phone_no or "0911000000",
                "Region": company.custom_seller_region_code or "13",
                "Wereda": company.custom_seller_woreda_code or "574",
                "City": company.custom_city or "0",
                "HouseNumber": company.custom_house_number or "NEW"
            },
            "BuyerDetails": {
                "City": cust_details.city if (is_det and cust_details.city) else "0",
                "Email": cust_details.email if (is_det and cust_details.email) else "user804346@gmail.com",
                "HouseNumber": cust_details.house_number if (is_det and cust_details.house_number) else "NEW",
                "IdNumber": cust_details.id_number if (is_det and cust_details.id_number) else "11122222222222222",
                "IdType": cust_details.id_type if (is_det and cust_details.id_type) else "KID",
                "Tin": clean_tin,
                "LegalName": cust_details.legal_name if (is_det and cust_details.legal_name) else (invoice_doc.customer_name or "ABC Trading"),
                "Phone": clean_phone,
                "Region": cust_details.region if (is_det and cust_details.region) else "13",
                "Country": cust_details.country if (is_det and cust_details.country) else "70",
                "Zone": cust_details.zone if (is_det and cust_details.zone) else "SHA",
                "Kebele": cust_details.kebele if (is_det and cust_details.kebele) else "03",
                "VatNumber": "123475885858",
                "Wereda": cust_details.woreda if (is_det and cust_details.woreda) else "574"          
            },
            "SourceSystem": {
                "SystemType": self.settings.system_type or "POS",
                "SystemNumber": self.settings.system_number or "677C38CEC1",
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
                "Discount": float(invoice_doc.discount_amount) if invoice_doc.discount_amount else None,
                "ExciseValue": float(0.0),
                "IncomeWithholdValue": float(0.0),
                "TransactionWithholdValue": float(0.0),
                "TaxValue": float(invoice_doc.total_taxes_and_charges or 0.0),
                "TotalValue": float(invoice_doc.grand_total or 0.0)
            },
            "ReferenceDetails": {
                "PreviousIrn": prev_irn if prev_irn else "",
                "RelatedDocument": None
            },
            "ItemList": []
        }

        tax_type = ""
        tax_entries = invoice_doc.get("taxes")
        if invoice_doc.taxes_and_charges and tax_entries and len(tax_entries) > 0:
            account = tax_entries[0].account_head
            tax_type = frappe.db.get_value("Account", account, "account_name")

        total_items_pretax = sum(float(item.net_amount or 0.0) for item in invoice_doc.items)
        invoice_tax_total = float(invoice_doc.total_taxes_and_charges or 0.0)

        for idx, item in enumerate(invoice_doc.items, start=1):
            pre_tax = float(item.net_amount or 0.0)
            line_tax_share = round((pre_tax / total_items_pretax) * invoice_tax_total, 2) if total_items_pretax > 0 else 0.0
            current_tax_code = tax_type if line_tax_share > 0 else "VATEX"
            raw_uom = str(item.uom or "PCS").strip().upper()

            payload["ItemList"].append({
                "LineNumber": idx,
                "ItemCode": item.item_code or "1111",
                "ProductDescription": item.description or item.item_name or "string",
                "NatureOfSupplies": "goods",
                "Quantity": float(item.qty or 1),
                "UnitPrice": float(item.rate or 0.0),
                "PreTaxValue": pre_tax,
                "TaxCode": current_tax_code,
                "TaxAmount": line_tax_share,
                "Discount": float(item.discount_amount or 0.0),
                "ExciseTaxValue": float(0.0),
                "HarmonizationCode": None,
                "Unit": raw_uom if raw_uom in ["LTR", "MTR", "101", "PCS", "ROL", "MTS", "PKG", "SET", "KLG"] else "PCS",
                "TotalLineAmount": pre_tax + line_tax_share
            })
        return payload

    def submit_single_invoice(self, invoice_name):
        """Dispatches an absolute synchronous transmission with strict header and string serialization"""
        try:
            token = self.get_valid_token()
            doc = frappe.get_doc("Sales Invoice", invoice_name)
            invoice_payload = self.build_invoice_payload(doc)
            
            auth_headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
                "apikey": self.settings.get_password("api_key"),
            }

            clean_url = self.settings.base_url.strip().rstrip('/')
            json_string_payload = json.dumps(invoice_payload)
            
            response = requests.post(
                f"{clean_url}/v1/register", 
                data=json_string_payload, 
                headers=auth_headers, 
                timeout=15
            )
            
            if response.status_code == 401:
                token = self.get_valid_token(force_refresh=True)
                auth_headers["Authorization"] = f"Bearer {token}"
                response = requests.post(
                    f"{clean_url}/v1/register", 
                    data=json_string_payload, 
                    headers=auth_headers, 
                    timeout=15
                )

            if response.status_code in [200, 201]:
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
                
        except Exception as e:
            frappe.log_error(message=frappe.get_traceback(), title=f"EIMS System Crash: {invoice_name}")
            return {"status": "Rule Error", "message": f"System Crash Error: {str(e)}"}

    def submit_bulk_invoices(self, invoice_names):
        """Sequential loop execution with strict ordering and anti-429 artificial pacing delays"""
        import time
        results_map = {}
        successes = 0
        failures = 0
        logs = []

        for idx, name in enumerate(invoice_names):
            # Introduce a short 2-second cooling delay between consecutive dispatches to prevent 429 errors
            if idx > 0:
                time.sleep(2.0)

            res = self.submit_single_invoice(name)
            status = res.get("status", "Rule Error")
            msg = res.get("message", "Unknown submission execution exception")
            
            results_map[name] = {
                "status": status,
                "message": msg
            }
            
            if status == "Transmitted":
                successes += 1
                logs.append(f"[{name}] Success -> {msg}")
            else:
                failures += 1
                logs.append(f"[{name}] Failed -> {msg}")

        overall_status = "Transmitted" if failures == 0 else ("Partially Transmitted" if successes > 0 else "Failed")
        summary_text = f"Iterative Batch Processing Complete.\nTotal processed: {len(invoice_names)} | Success: {successes} | Failures: {failures}\n\nExecution Logs:\n" + "\n".join(logs)
        
        return {
            "status": overall_status,
            "message": summary_text,
            "results": results_map
        }
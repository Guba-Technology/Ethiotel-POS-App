import json
import re

import requests

import frappe

from ethiotel_pos.eims.audit import log_audit
from ethiotel_pos.eims.constants import WALK_IN_CUSTOMER

RATE_LIMIT_KEY = "eims_public_verify:{0}"
RATE_LIMIT_MAX = 20
RATE_LIMIT_WINDOW = 3600

RECEIPT_RATE_LIMIT_KEY = "eims_public_receipt:{0}"
RECEIPT_RATE_LIMIT_MAX = 40
RECEIPT_RATE_LIMIT_WINDOW = 3600


def _rate_limited(key, limit, window):
    count = int(frappe.cache().get_value(key) or 0)
    if count >= limit:
        return True
    frappe.cache().set_value(key, count + 1, expires_in_sec=window)
    return False

def _extract_irn(irn=None, qr_payload=None):
    irn = (irn or "").strip()
    if irn:
        return irn
    payload = (qr_payload or "").strip()
    if not payload:
        return ""
    match = re.search(r"[A-Za-z0-9]{10,40}", payload)
    if match:
        return match.group(0)
    # Last URL path segment (typical MoR QR payloads encode a verify URL).
    return payload.rstrip("/").split("/")[-1].strip()


def _safe_local(invoice):
    """Reduce a local invoice to public-safe fields only (no buyer/items)."""
    status = invoice.get("custom_eims_status") or "Not Submitted"
    return {
        "verification_status": "Verified" if status == "Registered" else status,
        "status": status,
        "verified": status == "Registered",
        "cancelled": status == "Cancelled",
        "invoice_name": invoice.get("name"),
        "document_number": invoice.get("custom_document_number"),
        "irn": invoice.get("custom_irn"),
        "seller_legal_name": invoice.get("_seller_legal_name"),
        "document_date": invoice.get("posting_date"),
        "total_value": invoice.get("grand_total"),
    }


def _lookup_local(irn):
    company_name = None
    for doctype in ("Sales Invoice", "POS Invoice"):
        
        row = frappe.db.get_value(
                doctype,
                {"custom_irn": irn},
                [
                    "name",
                    "custom_document_number",
                    "custom_irn",
                    "custom_eims_status",
                    "custom_qr_code_url",
                    "company",
                    "customer",
                    "customer_name",
                    "posting_date",
                    "posting_time",
                    "currency",
                    "net_total",
                    "total_taxes_and_charges",
                    "discount_amount",
                    "grand_total",
                ],
                as_dict=True,
            )
        if row:
            company = row.get("company")
            if company:
                company_name = frappe.db.get_value("Company", company, "custom_seller_legal_name") \
                    or company
            row["_seller_legal_name"] = company_name
            row["_invoice_doctype"] = doctype
            return row
    return None


def _verify_remote(irn):
    from ethiotel_pos.eims_connector import EIMSConnector

    connector = EIMSConnector()
    token = connector.get_valid_token()
    base_url = connector.settings.base_url.strip().replace('"', "").replace("'", "").rstrip("/")
    url = f"{base_url}/v1/verify"
    default_client = connector.get_default_client_data()
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": connector.settings.get_password("api_key"),
        "Content-Type": "application/json",
        "Accept": "*/*",
    }
    json_payload = json.dumps({"irn": irn}, separators=(",", ":"))
    is_https = url.lower().startswith("https://")
    if is_https:
        request_body = connector._build_signed_envelope(json_payload, default_client)
    else:
        request_body = json_payload
    response = requests.post(url, data=request_body.encode("utf-8"), headers=headers, timeout=15)
    if response.status_code == 200:
        try:
            body = response.json().get("body", {})
        except (ValueError, AttributeError):
            return None
        seller = body.get("SellerDetails", {})
        vals = body.get("ValueDetails", {})
        # Public-safe subset: no buyer TIN, no item-level detail.
        return {
            "verification_status": "Verified",
            "verified": True,
            "cancelled": False,
            "irn": irn,
            "seller_legal_name": seller.get("LegalName"),
            "document_date": body.get("DocumentDetails", {}).get("Date", {}).get("date")
            if isinstance(body.get("DocumentDetails", {}).get("Date"), dict)
            else body.get("DocumentDetails", {}).get("Date"),
            "total_value": vals.get("TotalValue"),
        }
    return None


@frappe.whitelist(allow_guest=True)
def verify_public(irn=None, qr_payload=None):
    """Public, abuse-limited invoice verification.

    Returns only safe fields (seller legal name, document date, total, status).
    Never exposes buyer TIN/phone/ID or item-level detail to guests."""
    if not frappe.db.get_single_value("EIMS Setting", "public_verify_enabled"):
        frappe.throw(
            "Public invoice verification is disabled by the supplier.",
            frappe.PermissionError,
        )

    irn = _extract_irn(irn, qr_payload)
    if not irn:
        frappe.throw("Provide an IRN (or a QR payload containing one) to verify.")

    ip = getattr(frappe.local, "request_ip", None) or "unknown"
    if _rate_limited(RATE_LIMIT_KEY.format(ip), RATE_LIMIT_MAX, RATE_LIMIT_WINDOW):
        frappe.throw(
            "Too many verification requests from this address. Please try again later.",
            frappe.PermissionError,
        )

    local = _lookup_local(irn)
    if local:
        log_audit("Verification", success=local.get("custom_eims_status") == "Registered",
                  description=f"Public verification (local lookup) of IRN {irn}")
        return _safe_local(local)

    settings = frappe.get_doc("EIMS Setting")
    if settings.get("remote_verify_from_mor"):
        try:
            remote = _verify_remote(irn)
        except Exception:
            remote = None
            frappe.log_error(frappe.get_traceback(), "EIMS public verify remote failed")
        if remote:
            log_audit("Verification", success=True,
                      description=f"Public verification (MoR lookup) of IRN {irn}")
            return remote

    return {
        "verification_status": "Not Registered",
        "verified": False,
        "cancelled": False,
        "status": "Not Registered",
        "irn": irn,
    }


def _numeric(value, default=""):
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return default


def _seller_details(invoice):
    """Seller block for the public receipt, from the Company registry.
    Mirrors the register payload's SellerDetails sourcing."""
    company_name = invoice.get("company")
    company = None
    if company_name:
        company = frappe.get_doc("Company", company_name)
    if not company:
        return {"legal_name": company_name or "Ethio Telecom"}
    seller = {
        "legal_name": company.custom_seller_legal_name or company.company_name,
        "tin": frappe.db.get_single_value("EIMS Setting", "seller_tin") or "",
        "email": company.email or "",
        "phone": company.phone_no or "",
        "city": company.custom_city or "",
        "region": company.custom_seller_region_code or "",
        "wereda": company.custom_seller_woreda_code or "",
    }
    for key, attr in (
        ("vat_number", "custom_vat_number"),
        ("trade_name", "custom_trade_name"),
        ("house_number", "custom_house_number"),
        ("locality", "custom_locality"),
        ("sub_city", "custom_sub_city"),
        ("kebele", "custom_kebele"),
    ):
        value = getattr(company, attr, None)
        if value:
            seller[key] = value
    return seller


def _buyer_details(invoice):
    """Buyer block for the public receipt — sourced from Customer Details
    (the same registry the registration payload validates against)."""
    customer = invoice.get("customer") or ""
    is_walk_in = customer == WALK_IN_CUSTOMER
    buyer = {
        "legal_name": invoice.get("customer_name") or (customer or WALK_IN_CUSTOMER),
    }
    if customer and not is_walk_in and frappe.db.exists("Customer Details", customer):
        row = frappe.db.get_value(
            "Customer Details",
            customer,
            [
                "legal_name", "tin_number", "email", "phone", "region", "city",
                "woreda", "id_type", "id_number", "country", "zone",
                "sub_city", "kebele", "house_number", "locality",
            ],
            as_dict=True,
        )
        if row:
            for key, value in row.items():
                if value not in (None, ""):
                    buyer[key] = value
            buyer.setdefault("legal_name", invoice.get("customer_name") or customer)
    else:
        # No registered Customer Details record: allow EIMS Manual Invoice's
        # manual buyer fields to populate the same receipt keys used for
        # standard invoices (preserve legal_name behavior above).
        # Map manual fields onto the same keys as Customer Details.
        manual_tin = invoice.get("manual_buyer_tin")
        manual_email = invoice.get("manual_buyer_email")
        manual_phone = invoice.get("manual_buyer_phone")
        manual_id = invoice.get("manual_buyer_id")
        if manual_tin:
            buyer.setdefault("tin_number", manual_tin)
        if manual_email:
            buyer.setdefault("email", manual_email)
        if manual_phone:
            buyer.setdefault("phone", manual_phone)
        if manual_id:
            buyer.setdefault("id_number", manual_id)
        buyer.setdefault("legal_name", invoice.get("customer_name") or (customer or WALK_IN_CUSTOMER))
    return buyer


def _receipt_items(invoice):
    doctype = invoice.get("_invoice_doctype")
    name = invoice.get("name")
    if not doctype or not frappe.db.exists(doctype, name):
        return []
    doc = frappe.get_doc(doctype, name)
    items = []
    for it in doc.get("items") or []:
        amount = it.get("base_net_amount") or it.get("net_amount") or it.get("amount")
        rate = it.get("base_rate") or it.get("rate")
        items.append({
            "item_code": it.get("item_code"),
            "description": it.get("description") or it.get("item_name") or it.get("item_code"),
            "quantity": it.get("qty"),
            "uom": it.get("uom") or "",
            "tax_code": it.get("item_tax_template") or "",
            "discount_amount": it.get("discount_amount") or 0.0,
            "rate": rate,
            "amount": amount,
        })
    return items


def _safe_receipt_local(invoice):
    status = invoice.get("custom_eims_status") or "Not Submitted"
    currency = invoice.get("currency") or "ETB"
    tax_total = _numeric(invoice.get("total_taxes_and_charges"), 0.0)
    net_total = _numeric(invoice.get("net_total"), 0.0)
    discount = _numeric(invoice.get("discount_amount"), 0.0)
    grand_total = _numeric(invoice.get("grand_total"), 0.0)
    payed = grand_total - _numeric(invoice.get("outstanding_amount"), 0.0)
    if not net_total and isinstance(grand_total, (int, float)) and isinstance(tax_total, (int, float)):
                net_total = round(grand_total - tax_total, 2)
    settings = frappe.get_doc("EIMS Setting")
    sysem_number = settings.get("default_system_number") or ""
    return {
        "verified": status == "Registered",
        "cancelled": status == "Cancelled",
        "status": status,
        "invoice_name": invoice.get("name"),
        "document_number": invoice.get("custom_document_number"),
        "document_date": invoice.get("posting_date"),
       
        "posting_time": invoice.get("posting_time"),
        "irn": invoice.get("custom_irn"),
        "system_number": sysem_number,
        "sale_type": invoice.get("custom_transaction_type") or "",
        "qr_code_url": invoice.get("custom_qr_code_url"),
        "currency": currency,
        "seller": _seller_details(invoice),
        "buyer": _buyer_details(invoice),
        "items": _receipt_items(invoice),
        "totals": {
            "net_total": net_total,
            "tax_total": tax_total,
            "discount": discount,
            "grand_total": grand_total,
            "paid_amount": payed,
            "outstanding_amount": _numeric(invoice.get("outstanding_amount"), 0.0),
        },
    }


@frappe.whitelist(allow_guest=True)
def receipt_public(irn=None, qr_payload=None):
    if not frappe.db.get_single_value("EIMS Setting", "public_verify_enabled"):
        frappe.throw(
            "Public invoice receipt is disabled by the supplier.",
            frappe.PermissionError,
        )

    irn = _extract_irn(irn, qr_payload)
    if not irn:
        frappe.throw("Provide an IRN (or a QR payload containing one) to view the receipt.")

    ip = getattr(frappe.local, "request_ip", None) or "unknown"
    if _rate_limited(RECEIPT_RATE_LIMIT_KEY.format(ip), RECEIPT_RATE_LIMIT_MAX, RECEIPT_RATE_LIMIT_WINDOW):
        frappe.throw(
            "Too many receipt requests from this address. Please try again later.",
            frappe.PermissionError,
        )

    local = _lookup_local(irn)
    if local:
        log_audit("Receipt Authorization", success=local.get("custom_eims_status") == "Registered",
                  description=f"Public receipt (local lookup) of IRN {irn}")
        print("Safe receipt local:", _safe_receipt_local(local))
        return _safe_receipt_local(local)

    settings = frappe.get_doc("EIMS Setting")
    if settings.get("remote_verify_from_mor"):
        try:
            remote = _verify_remote(irn)
        except Exception:
            remote = None
            frappe.log_error(frappe.get_traceback(), "EIMS public receipt remote failed")
        if remote:
            log_audit("Receipt Authorization", success=True,
                      description=f"Public receipt (MoR lookup) of IRN {irn}")
            return remote

    return {
        "verified": False,
        "cancelled": False,
        "status": "Not Registered",
        "irn": irn,
    }
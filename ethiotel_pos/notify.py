import frappe
import requests

BRAND_COLOR = "#0057A3"
BRAND_COLOR_DARK = "#003E75"


def _settings():
    settings = frappe.get_doc("EIMS Setting")
    return {
        "email": bool(settings.get("email_receipt_delivery")),
        "sms": bool(settings.get("sms_enabled")),
    }


def _buyer_contact(invoice_doc):
    """Resolve buyer email + phone for a registered invoice.
    Precedence: Customer Details -> Customer custom_eims_* -> invoice
    contact/buyer fields (works for Sales Invoice and EIMS Manual Invoice)."""
    email = None
    phone = None
    customer = invoice_doc.get("customer")
    if customer:
        if frappe.db.exists("Customer Details", customer):
            row = frappe.db.get_value(
                "Customer Details", customer, ["email", "phone"], as_dict=True
            )
            email = (row or {}).get("email") or None
            phone = (row or {}).get("phone") or None
    if not email:
        email = invoice_doc.get("contact_email") or invoice_doc.get("buyer_email")
    if not phone:
        phone = invoice_doc.get("contact_mobile") or invoice_doc.get("buyer_phone")
    return email, phone


def _enqueue(method, **kwargs):
    frappe.enqueue(
        method,
        queue="short",
        timeout=300,
        now=frappe.flags.in_test,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# HTML email template
# ---------------------------------------------------------------------------
# Email clients strip <style> blocks unpredictably (Outlook/older Gmail in
# particular), so layout uses tables and every element carries its own
# inline style rather than relying on a shared stylesheet.

def _e(value):
    """HTML-escape a value for safe embedding in the email body."""
    if value is None:
        return ""
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _email_shell(preheader, body_html, org="Ethio Telecom"):
    """Wrap body_html in the shared header/footer chrome. 600px, table based,
    fully inline-styled so it survives Gmail/Outlook stripping.

    Follows the MoR AddisFaktur invoice email: white card with an Organization
    header, the supplied body, then a Website/Contact footer."""
    return f"""
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{preheader}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
       style="background:#f2f4f7;padding:24px 0;font-family:'Segoe UI',Arial,sans-serif;">
  <tr>
    <td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0"
             style="background:#ffffff;border-radius:8px;overflow:hidden;border:1px solid #e6e9ee;">
        <tr>
          <td style="padding:22px 28px;border-bottom:1px solid #eef0f3;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="font-size:18px;font-weight:bold;color:{BRAND_COLOR};">
                  {_e(org)}
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:28px;">
            {body_html}
          </td>
        </tr>
        <tr>
          <td style="background:#f8f9fb;padding:18px 28px;border-top:1px solid #e6e9ee;">
            <div style="color:#8a94a6;font-size:11px;line-height:1.6;">
              <a href="{frappe.utils.get_url()}" style="color:#0a6ed1;text-decoration:none;">Website</a>
              &nbsp;&bull;&nbsp;
              <a href="mailto:support@ethiotelecom.et" style="color:#0a6ed1;text-decoration:none;">Contact&nbsp;Us</a>
            </div>
            <div style="color:#8a94a6;font-size:11px;margin-top:8px;">
              &copy; {frappe.utils.nowdate()[:4]} {_e(org)}. All rights reserved.
            </div>
          </td>
        </tr>
      </table>
      <div style="color:#adb5bd;font-size:10px;margin-top:12px;">
        Electronic Invoicing Management System &mdash; Directive No. 1142/2026
      </div>
    </td>
  </tr>
</table>
""".strip()


def _summary_card(rows):
    """rows: list of (label, value) tuples rendered as a bordered key/value table.

    Mirrors the MoR invoice details table: a light-grey label column with a
    bold, left-aligned value column."""
    body_rows = "".join(
        f"""
        <tr>
          <td style="padding:8px 14px;font-size:12px;color:#6c757d;background:#f8f9fa;border-bottom:1px solid #e9ecef;white-space:nowrap;">{_e(label)}</td>
          <td style="padding:8px 14px;font-size:13px;color:#212529;border-bottom:1px solid #e9ecef;word-break:break-word;">{_e(value)}</td>
        </tr>"""
        for label, value in rows
    )
    return f"""
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
       style="border:1px solid #e9ecef;border-collapse:collapse;margin:10px 0 18px;">
  {body_rows}
</table>
""".strip()


def _button(label, href):
    return f"""
<table role="presentation" cellpadding="0" cellspacing="0" style="margin:16px 0 20px;">
  <tr>
    <td style="border-radius:6px;background:#0a6ed1;">
      <a href="{_e(href)}" target="_blank"
         style="display:inline-block;padding:12px 30px;color:#ffffff;font-size:14px;font-weight:bold;text-decoration:none;">
        {_e(label)}
      </a>
    </td>
  </tr>
</table>
""".strip()


def _invoice_summary_rows(doc, irn):
    payment_terms = doc.get("payment_terms") or doc.get("terms") or "N/A"
    payment_method = doc.get("mode_of_payment") or doc.get("payment_method") or "N/A"
    post_date = doc.get("posting_date") or doc.get("invoice_date")
    return [
        ("Invoice Number", doc.get("name")),
        ("Invoice Reference (IRN)", irn or "-"),
        ("Document Type", "Tax Invoice"),
        ("Payment Terms", payment_terms),
        ("Payment Method", payment_method),
        ("Date", frappe.utils.format_datetime(post_date) if post_date else "-"),
    ]


def _build_registered_email(doc, invoice_name, irn, receipt_url):
    org = doc.get("company") or "Ethio Telecom"
    buyer_name = doc.get("customer_name") or doc.get("buyer_name") or doc.get("customer") or "customer"
    amount = frappe.utils.fmt_money(doc.get("grand_total"), currency=doc.get("currency"))
    body = f"""
<p style="font-size:11px;color:#6a6d70;letter-spacing:1.5px;font-weight:bold;text-transform:uppercase;margin:0 0 6px;">
  REGISTERED WITH THE MINISTRY OF REVENUE
</p>
<h1 style="font-size:22px;color:#32363a;margin:0 0 14px;">Your Invoice</h1>
<div style="font-size:14px;color:#212529;line-height:1.6;">
  Dear {_e(buyer_name)},<br/>
  {_e(org)} has issued you an <b>Invoice</b>, and it has been registered with
  the Ministry of Revenue. Its details are below.
</div>
<p style="font-size:11px;color:#6a6d70;letter-spacing:1.5px;font-weight:bold;text-transform:uppercase;margin:20px 0 2px;">
  Total Amount
</p>
<div style="font-size:30px;color:#0a6ed1;font-weight:bold;margin:0 0 10px;">{_e(amount)}</div>
{_summary_card(_invoice_summary_rows(doc, irn))}
<p style="font-size:11px;color:#6a6d70;letter-spacing:1.5px;font-weight:bold;text-transform:uppercase;margin:18px 0 8px;">
  Verify this document with the Ministry of Revenue using the IRN above
</p>
{_button("View Your Invoice", receipt_url)}
<p style="font-size:12px;color:#6c757d;line-height:1.6;">
  This message confirms that the document has been registered. It is not a
  receipt for payment &mdash; you will receive a separate confirmation once a
  payment against it has been recorded. Please keep this email for your
  records. If you were not expecting this Invoice, contact {_e(org)} directly.
</p>
"""
    return _email_shell(
        preheader=f"Your invoice {invoice_name} has been registered with the Ministry of Revenue.",
        body_html=body,
        org=org,
    )


def _build_cancellation_email(doc, invoice_name, irn):
    org = doc.get("company") or "Ethio Telecom"
    body = f"""
<p style="font-size:11px;color:#c0392b;letter-spacing:1.5px;font-weight:bold;text-transform:uppercase;margin:0 0 6px;">
  CANCELLED &mdash; REGISTERED WITH THE MINISTRY OF REVENUE
</p>
<h1 style="font-size:22px;color:#32363a;margin:0 0 14px;">Your Invoice has been cancelled</h1>
<div style="font-size:14px;color:#212529;line-height:1.6;">
  Dear customer,<br/>
  The tax invoice below has been <b>cancelled</b> in accordance with Ethiopia's
  Electronic Invoicing System directive.
</div>
{_summary_card(_invoice_summary_rows(doc, irn))}
<div style="font-size:12px;color:#6c757d;line-height:1.6;">
  If you believe this was in error, or have questions about this cancellation,
  please contact the merchant directly.
</div>
<div style="font-size:14px;color:#212529;margin-top:22px;">Regards,<br/>{_e(org)}</div>
"""
    return _email_shell(
        preheader=f"Your tax invoice {invoice_name} was cancelled.",
        body_html=body,
        org=org,
    )


# ---------------------------------------------------------------------------
# Outbound notifications
# ---------------------------------------------------------------------------

def _build_registered_sms(doc, invoice_name, irn, amount):
    org = doc.get("company") or "Ethio Telecom"
    customer = doc.get("customer_name") or doc.get("buyer_name") or doc.get("customer") or "customer"
    check_url = "{0}/invoice_receipt?irn={1}".format(
        frappe.utils.get_url().rstrip("/"), irn
    )
    post_date = doc.get("posting_date") or doc.get("invoice_date")
    inv_date = frappe.utils.format_date(post_date) if post_date else "-"
    try:
        amount_txt = f"{float(amount):,.2f}"
    except (TypeError, ValueError):
        amount_txt = str(amount)
    return (
        f"Dear {customer}, your Invoice #{invoice_name} with Total amount "
        f"{amount_txt} {doc.get('currency') or ''} has been registered with MoR.\n"
        f"IRN: {irn}\n"
        f"You can check it here: {check_url}\n"
        f"Invoice Date: {inv_date}\n"
        f"Status: Registered\n\n"
        f"We honor working with us {org}."
    )


def _build_cancellation_sms(doc, invoice_name, irn):
    org = doc.get("company") or "Ethio Telecom"
    customer = doc.get("customer_name") or doc.get("buyer_name") or doc.get("customer") or "customer"
    return (
        f"Dear {customer}, your tax invoice {invoice_name} (IRN {irn}) has been "
        "cancelled in Ethiopia's Electronic Invoicing System. "
        "Please contact the merchant if this was not expected."
    )


def send_registered_receipt(invoice_name, doctype="Sales Invoice"):
    """Notify the buyer that their invoice was registered with MoR.
    Sends email (if email_receipt_delivery is on) and/or SMS (if
    sms_enabled + AfroMessage is configured)."""
    flags = _settings()
    results = {"email": {"sent": False}, "sms": {"sent": False}}
    try:
        doc = frappe.get_doc(doctype, invoice_name)
        email, phone = _buyer_contact(doc)
        irn = doc.get("custom_irn")
        grand_total = doc.get("grand_total")

        if flags["email"]:
            if not email:
                results["email"] = {"sent": False, "reason": "no_buyer_email"}
            else:
                receipt_url = "{0}/invoice_receipt?irn={1}".format(
                    frappe.utils.get_url().rstrip("/"), irn
                )
                frappe.sendmail(
                    recipients=[email],
                    subject=f"Your Tax Invoice {invoice_name} - IRN {irn}",
                    message=_build_registered_email(doc, invoice_name, irn, receipt_url),
                    reference_doctype=doctype,
                    reference_name=invoice_name,
                )
                frappe.msgprint("Registered invoice email sent.")
                results["email"] = {"sent": True}

        if flags["sms"] and phone:
            results["sms"] = send_sms(phone, _build_registered_sms(doc, invoice_name, irn, grand_total))

    except Exception:
        frappe.msgprint("Failed to send registered invoice email. Please check the error log.")
        frappe.log_error(frappe.get_traceback(), f"EIMS receipt email failed for {invoice_name}")
        return {"sent": False}

    sent_any = results["email"]["sent"] or results["sms"]["sent"]
    return {"sent": sent_any, "channels": results}


def send_cancellation_notice(invoice_name, irn, doctype="Sales Invoice"):
    """Notify the buyer digitally when their invoice is cancelled (Art 26(5)).
    Sends email (if email_receipt_delivery is on) and/or SMS (if sms_enabled
    + sms_provider is configured)."""
    flags = _settings()
    results = {"email": {"sent": False}, "sms": {"sent": False}}
    try:
        doc = frappe.get_doc(doctype, invoice_name)
        email, phone = _buyer_contact(doc)

        if flags["email"]:
            if not email:
                results["email"] = {"sent": False, "reason": "no_buyer_email"}
            else:
                frappe.sendmail(
                    recipients=[email],
                    subject=f"Your Tax Invoice {invoice_name} was cancelled",
                    message=_build_cancellation_email(doc, invoice_name, irn),
                    reference_doctype=doctype,
                    reference_name=invoice_name,
                )
                results["email"] = {"sent": True}

        if flags["sms"] and phone:
            results["sms"] = send_sms(phone, _build_cancellation_sms(doc, invoice_name, irn))

    except Exception:
        frappe.log_error(frappe.get_traceback(), f"EIMS cancellation notice failed for {invoice_name}")
        return {"sent": False}

    sent_any = results["email"]["sent"] or results["sms"]["sent"]
    return {"sent": sent_any, "channels": results}


def send_sms(phone, text):

    settings = frappe.get_doc("EIMS Setting")
    if not bool(settings.get("sms_enabled")):
        return {"sent": False, "reason": "disabled"}
    if not phone:
        return {"sent": False, "reason": "no_recipient"}
    if not settings.get("afro_base_url"):
        return {"sent": False, "reason": "no_provider_configured"}
    base_url = (settings.get("afro_base_url") or "").strip()
    token = settings.get_password("afro_token") if settings.get("afro_token") else None
    if not token or not settings.get("afro_from_id"):
        return {"sent": False, "reason": "no_provider_configured"}

    payload = {
        "from": (settings.get("afro_from_id") or "").strip(),
        "sender": (settings.get("afro_sender") or "").strip(),
        "to": str(phone).strip(),
        "message": (text or "")[:1000],
        "callback": (settings.get("afro_callback") or "").strip(),
    }
    try:
        response = requests.get(
            base_url,
            headers={"Authorization": f"Bearer {token}"},
            params=payload,
            timeout=15,
        )
    except requests.exceptions.RequestException as e:
        frappe.log_error(f"EIMS SMS send failed (transport): {e}", "EIMS SMS")
        return {"sent": False, "reason": "transport_error"}

    try:
        response_json = response.json()
    except ValueError:
        frappe.log_error(f"EIMS SMS send failed (HTTP {response.status_code}): {response.text[:300]}", "EIMS SMS")
        return {"sent": False, "reason": "bad_response"}

    if response.status_code == 200 and response_json.get("acknowledge") == "success":
        return {"sent": True, "provider_id": response_json.get("data", {}).get("message_id") or ""}
    frappe.log_error(f"EIMS SMS send failed (HTTP {response.status_code}): {response_json}", "EIMS SMS")
    return {"sent": False, "reason": "provider_error"}
from email import header
import re

import frappe
import requests

BRAND_COLOR = "#0057A3"
BRAND_COLOR_DARK = "#003E75"


def _normalize_phone(phone):
    """Normalize an Ethiopian phone number to E.164 (+251...)."""
    s = re.sub(r"[^0-9+]", "", str(phone or ""))
    if s.startswith("+"):
        return s
    if s.startswith("00"):
        return "+" + s[2:]
    if s.startswith("0"):
        return "+251" + s[1:]
    if s.startswith("251") and len(s) == 12:
        return "+" + s
    if len(s) == 9:
        return "+251" + s
    return ("+" + s) if s else s


def _clean_sender(sender):
    """AfroMessage `sender` must be 3-11 alphanumeric starting with a letter."""
    s = re.sub(r"[^A-Za-z0-9]", "", str(sender or ""))
    if not s:
        return ""
    if s[0].isdigit():
        s = "S" + s
    s = s[:11]
    return s if len(s) >= 3 else ""


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


def _build_registered_email(doc, invoice_name, irn, receipt_url, note_type="INV", ref_irn=None):
    org = doc.get("company") or "Ethio Telecom"
    buyer_name = doc.get("customer_name") or doc.get("buyer_name") or doc.get("customer") or "customer"
    amount = frappe.utils.fmt_money(doc.get("grand_total"), currency=doc.get("currency"))
    if note_type == "CRE":
        kicker = "CREDIT NOTE REGISTERED WITH THE MINISTRY OF REVENUE"
        heading = "Your Credit Note"
        blurb = (
            f"{_e(org)} has issued you a <b>Credit Note</b>, and it has been registered "
            "with the Ministry of Revenue. Its details are below."
        )
    elif note_type == "DEB":
        kicker = "DEBIT NOTE REGISTERED WITH THE MINISTRY OF REVENUE"
        heading = "Your Debit Note"
        blurb = (
            f"{_e(org)} has issued you a <b>Debit Note</b>, and it has been registered "
            "with the Ministry of Revenue. Its details are below."
        )
    else:
        kicker = "REGISTERED WITH THE MINISTRY OF REVENUE"
        heading = "Your Invoice"
        blurb = (
            f"{_e(org)} has issued you an <b>Invoice</b>, and it has been registered with "
            "the Ministry of Revenue. Its details are below."
        )
    summary_rows = _invoice_summary_rows(doc, irn)
    if ref_irn:
        summary_rows = [("Original Invoice (IRN)", ref_irn)] + summary_rows
    body = f"""
<p style="font-size:11px;color:#6a6d70;letter-spacing:1.5px;font-weight:bold;text-transform:uppercase;margin:0 0 6px;">
  {kicker}
</p>
<h1 style="font-size:22px;color:#32363a;margin:0 0 14px;">{heading}</h1>
<div style="font-size:14px;color:#212529;line-height:1.6;">
  Dear {_e(buyer_name)},<br/>
  {blurb}
</div>
<p style="font-size:11px;color:#6a6d70;letter-spacing:1.5px;font-weight:bold;text-transform:uppercase;margin:20px 0 2px;">
  Total Amount
</p>
<div style="font-size:30px;color:#0a6ed1;font-weight:bold;margin:0 0 10px;">{_e(amount)}</div>
{_summary_card(summary_rows)}
<p style="font-size:11px;color:#6a6d70;letter-spacing:1.5px;font-weight:bold;text-transform:uppercase;margin:18px 0 8px;">
  Verify this document with the Ministry of Revenue using the IRN above
</p>
{_button("View Your Document", receipt_url)}
<p style="font-size:12px;color:#6c757d;line-height:1.6;">
  This message confirms that the document has been registered. It is not a
  receipt for payment &mdash; you will receive a separate confirmation once a
  payment against it has been recorded. Please keep this email for your
  records. If you were not expecting this document, contact {_e(org)} directly.
</p>
"""
    return _email_shell(
        preheader=f"Your {heading.lower()} {invoice_name} has been registered with the Ministry of Revenue.",
        body_html=body,
        org=org,
    )


def _build_cancellation_email(doc, invoice_name, irn):
    org = doc.get("company") or "Ethio Telecom"
    receipt_url = "{0}/invoice_receipt?irn={1}".format(
        frappe.utils.get_url().rstrip("/"), irn or ""
    )
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
<p style="font-size:11px;color:#6a6d70;letter-spacing:1.5px;font-weight:bold;text-transform:uppercase;margin:18px 0 8px;">
  Verify this document with the Ministry of Revenue using the IRN above
</p>
{_button("View Your Document", receipt_url)}
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


def _build_registered_sms(doc, invoice_name, irn, amount, note_type="INV", ref_irn=None):
    """Buyer SMS for EIMS registration, same length/shape as the
    cancellation notice (<=253 chars)."""
    customer = doc.get("customer_name") or doc.get("buyer_name") or doc.get("customer") or "customer"
    kind = {"CRE": "credit note", "DEB": "debit note"}.get(note_type, "tax invoice")
    irn_part = f" (IRN {irn})" if irn else ""
    return (
        f"Dear {customer}, your {kind} {invoice_name}{irn_part} has been registered "
        "in Ethiopia's Electronic Invoicing System. "
        "Please contact the merchant if this was not expected."
    )


def _build_cancellation_sms(doc, invoice_name, irn):
    org = doc.get("company") or "Ethio Telecom"
    customer = doc.get("customer_name") or doc.get("buyer_name") or doc.get("customer") or "customer"
    return (
        f"Dear {customer}, your tax invoice {invoice_name} (IRN {irn}) has been "
        "cancelled in Ethiopia's Electronic Invoicing System. "
        "Please contact the merchant if this was not expected."
    )


def send_registered_receipt(invoice_name, doctype="Sales Invoice", note_type="INV", ref_irn=None):
    """Notify the buyer that their invoice (INV contractor, CRE credit note
    or DEB debit note) was registered with MoR.
    Sends email (if email_receipt_delivery is on) and/or SMS (if
    sms_enabled + AfroMessage is configured)."""
    flags = _settings()
    results = {"email": {"sent": False}, "sms": {"sent": False}}
    try:
      doc = frappe.get_doc(doctype, invoice_name)
    except Exception:
      frappe.log_error(frappe.get_traceback(), f"EIMS receipt retrieval failed for {invoice_name}")
      return {"sent": False}

    email, phone = _buyer_contact(doc)
    irn = doc.get("custom_irn")
    grand_total = doc.get("grand_total")

    # Email channel: isolate failures so SMS still runs
    if flags["email"]:
      if not email:
        results["email"] = {"sent": False, "reason": "no_buyer_email"}
      else:
        try:
          receipt_url = "{0}/invoice_receipt?irn={1}".format(
            frappe.utils.get_url().rstrip("/"), irn
          )
          frappe.sendmail(
            recipients=[email],
            subject=f"Your Tax Invoice {invoice_name} - IRN {irn}",
            message=_build_registered_email(doc, invoice_name, irn, receipt_url, note_type=note_type, ref_irn=ref_irn),
            reference_doctype=doctype,
            reference_name=invoice_name,
          )
          frappe.msgprint("Registered invoice email sent.")
          results["email"] = {"sent": True}
        except Exception:
          results["email"] = {"sent": False}
          frappe.msgprint("Failed to send registered invoice email. Please check the error log.")
          frappe.log_error(frappe.get_traceback(), f"EIMS receipt email failed for {invoice_name}")

    # SMS channel: isolate failures so email result is preserved
    if flags["sms"]:
      if not phone:
        results["sms"] = {"sent": False, "reason": "no_recipient"}
      else:
        try:
          results["sms"] = send_sms(phone, _build_registered_sms(doc, invoice_name, irn, grand_total, note_type=note_type, ref_irn=ref_irn))
        except Exception:
          results["sms"] = {"sent": False}
          frappe.log_error(frappe.get_traceback(), f"EIMS SMS send failed for {invoice_name}")

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


def _build_sales_receipt_email(receipt):
    org = receipt.get("collector_name") or "Ethio Telecom"
    amount = float(receipt.get("collected_amount") or 0.0)
    currency = receipt.get("currency") or "ETB"
    receipt_url = "{0}/invoice_receipt?rrn={1}".format(
        frappe.utils.get_url().rstrip("/"), receipt.get("returned_rnn") or receipt.get("eims_rrn") or ""
    )
    summary_rows = [
        ("Receipt Number", receipt.get("receipt_number") or "-"),
        ("MoR Reference (RRN)", receipt.get("returned_rnn") or receipt.get("eims_rrn") or "-"),
        ("Payment Method", receipt.get("mode_of_payment") or "CASH"),
        ("Collected Amount", frappe.utils.fmt_money(amount, currency=currency)),
        ("Receipt Date", frappe.utils.format_datetime(receipt.get("receipt_date") or "")),
    ]
    body = f"""
<p style="font-size:11px;color:#0a7d33;letter-spacing:1.5px;font-weight:bold;text-transform:uppercase;margin:0 0 6px;">
  PAYMENT RECEIPT &mdash; REGISTERED WITH THE MINISTRY OF REVENUE
</p>
<h1 style="font-size:22px;color:#32363a;margin:0 0 14px;">Your payment has been received</h1>
<div style="font-size:14px;color:#212529;line-height:1.6;">
  Your payment of <b>{_e(frappe.utils.fmt_money(amount, currency=currency))}</b>
  has been recorded and registered with the Ministry of Revenue. Details are below.
</div>
{_summary_card(summary_rows)}
<p style="font-size:11px;color:#6a6d70;letter-spacing:1.5px;font-weight:bold;text-transform:uppercase;margin:18px 0 8px;">
  Verify this receipt with the Ministry of Revenue using the RRN above
</p>
{_button("View Your Receipt", receipt_url)}
<div style="font-size:12px;color:#6c757d;line-height:1.6;">
  This message confirms that the payment receipt was registered. Please keep
  this email for your records.
</div>
<div style="font-size:14px;color:#212529;margin-top:22px;">Regards,<br/>{_e(org)}</div>
"""
    return _email_shell(
        preheader=f"Your payment of {frappe.utils.fmt_money(amount, currency=currency)} was received and registered.",
        body_html=body,
        org=org,
    )


def send_receipt_notice(receipt_name):
    """Notify the paying customer that a MoR sales receipt was generated.
    Recipient: the receipt's party (Customer) — email + SMS per settings."""
    flags = _settings()
    results = {"email": {"sent": False}, "sms": {"sent": False}}
    try:
        receipt = frappe.get_doc("EIMS Invoice Receipt", receipt_name)
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"EIMS receipt notice retrieval failed for {receipt_name}")
        return {"sent": False}

    party = receipt.get("party") or ""
    party_name = receipt.get("party_name") or party or "customer"
    email = None
    phone = None
    if party:
        cd = frappe.db.get_value(
            "Customer Details", party, ["email", "phone"], as_dict=True
        ) if frappe.db.exists("Customer Details", party) else None
        email = (cd or {}).get("email") or None
        phone = (cd or {}).get("phone") or None
    # Fall back to a covered Sales Invoice's buyer contact when the party
    # registry has no contact info.
    if not (email or phone):
        for row in (receipt.get("invoices_covered") or []):
            si = row.get("sales_invoice") or row.get("pos_invoice")
            if not si:
                continue
            doc = frappe.get_doc(row.get("sales_invoice") and "Sales Invoice" or "POS Invoice", si)
            email, phone = _buyer_contact(doc)
            if email or phone:
                break

    if flags["email"]:
        if not email:
            results["email"] = {"sent": False, "reason": "no_buyer_email"}
        else:
            frappe.sendmail(
                recipients=[email],
                subject=f"Your Payment Receipt {receipt.get('receipt_number') or receipt_name}",
                message=_build_sales_receipt_email(receipt),
                reference_doctype="EIMS Invoice Receipt",
                reference_name=receipt_name,
            )
            results["email"] = {"sent": True}

    if flags["sms"] and phone:
        amount = receipt.get("collected_amount") or 0
        org = receipt.get("collector_name") or "Ethio Telecom"
        try:
            amount_txt = f"{float(amount):,.2f}"
        except (TypeError, ValueError):
            amount_txt = str(amount)
        rrn = receipt.get("returned_rnn") or receipt.get("eims_rrn") or ""
        results["sms"] = send_sms(
            phone,
            f"Dear {party_name}, your payment receipt #{receipt.get('receipt_number') or receipt_name} "
            f"for {amount_txt} {receipt.get('currency') or 'ETB'} has been registered with MoR. "
            f"RRN: {rrn}. We honor working with us {org}."
        )

    sent_any = results["email"]["sent"] or results["sms"]["sent"]
    return {"sent": sent_any, "channels": results}


def _supplier_contact(invoice_number):
    """Resolve supplier (withholdee) email + phone from the linked
    Purchase Invoice via its Supplier's Contact."""
    email = None
    phone = None
    if not invoice_number or not frappe.db.exists("Purchase Invoice", invoice_number):
        return None, None
    supplier = frappe.db.get_value("Purchase Invoice", invoice_number, "supplier") or ""
    if not supplier:
        return None, None
    contact = frappe.db.sql(
        """
        SELECT dl.parent FROM `tabDynamic Link` dl
        JOIN `tabContact` c ON c.name = dl.parent
        WHERE dl.link_doctype = 'Supplier' AND dl.link_name = %s AND c.docstatus < 2
        ORDER BY c.creation ASC
        LIMIT 1
        """,
        supplier,
    )
    if not contact:
        return None, None
    cdoc = frappe.get_doc("Contact", contact[0][0])
    email = (cdoc.get("email_id") or "").strip() or None
    phone = (cdoc.get("mobile_no") or "").strip() or cdoc.get("phone") or None
    return email, phone


def _build_withholding_email(wr, supplier_name):
    org = wr.get("agent_name") or "Ethio Telecom"
    amount = float(wr.get("withholding_amount") or 0.0)
    receipt_url = "{0}/invoice_receipt?irn={1}".format(
        frappe.utils.get_url().rstrip("/"), wr.get("invoice_irn") or ""
    )
    summary_rows = [
        ("Withholding Receipt", wr.get("receipt_number") or "-"),
        ("Invoice IRN", wr.get("invoice_irn") or "-"),
        ("Withholding Type", wr.get("withholding_type") or "TWTH"),
        ("Rate", f"{frappe.utils.flt(wr.get('withholding_rate') or 0)}%"),
        ("Withholding Amount", frappe.utils.fmt_money(amount, currency=wr.get("currency") or "ETB")),
        ("Invoice Date", frappe.utils.format_datetime(wr.get("invoice_date") or "")),
        ("Authorized Date", frappe.utils.format_datetime(wr.get("receipt_date") or "")),
        ("MoR Receipt ID", wr.get("mor_receipt_id") or wr.get("rrn") or "-"),
    ]
    body = f"""
<p style="font-size:11px;color:#7a4f00;letter-spacing:1.5px;font-weight:bold;text-transform:uppercase;margin:0 0 6px;">
  WITHHOLDING RECEIPT &mdash; AUTHORIZED BY THE MINISTRY OF REVENUE
</p>
<h1 style="font-size:22px;color:#32363a;margin:0 0 14px;">Withholding receipt authorized</h1>
<div style="font-size:14px;color:#212529;line-height:1.6;">
  Dear {_e(supplier_name)}<br/>
  A withholding receipt for invoice above has been authorized by the Ministry
  of Revenue. Details are below.
</div>
{_summary_card(summary_rows)}
<p style="font-size:11px;color:#6a6d70;letter-spacing:1.5px;font-weight:bold;text-transform:uppercase;margin:18px 0 8px;">
  View the invoice this withholding applies to using the IRN above
</p>
{_button("View Your Invoice", receipt_url)}
<div style="font-size:12px;color:#6c757d;line-height:1.6;">
  This receipt certifies the tax withheld on the linked invoice. Please keep
  this email for your records.
</div>
<div style="font-size:14px;color:#212529;margin-top:22px;">Regards,<br/>{_e(org)}</div>
"""
    return _email_shell(
        preheader=f"Withholding receipt {wr.get('receipt_number') or ''} authorized by the Ministry of Revenue.",
        body_html=body,
        org=org,
    )


def send_withholding_notice(receipt_name):
    """Notify the seller (supplier) that a MoR withholding receipt was
    authorized. Recipient: the supplier on the linked Purchase Invoice —
    email + SMS per settings."""
    flags = _settings()
    results = {"email": {"sent": False}, "sms": {"sent": False}}
    try:
        wr = frappe.get_doc("Withholding Receipt", receipt_name)
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"EIMS withholding notice retrieval failed for {receipt_name}")
        return {"sent": False}

    supplier_name = wr.get("seller_name") or "Supplier"
    email, phone = _supplier_contact(wr.get("invoice_number"))

    if flags["email"]:
        if not email:
            results["email"] = {"sent": False, "reason": "no_supplier_email"}
        else:
            frappe.sendmail(
                recipients=[email],
                subject=f"Withholding Receipt {wr.get('receipt_number') or receipt_name} - authorized by MoR",
                message=_build_withholding_email(wr, supplier_name),
                reference_doctype="Withholding Receipt",
                reference_name=receipt_name,
            )
            results["email"] = {"sent": True}

    if flags["sms"] and phone:
        amount = wr.get("withholding_amount") or 0
        try:
            amount_txt = f"{float(amount):,.2f}"
        except (TypeError, ValueError):
            amount_txt = str(amount)
        results["sms"] = send_sms(
            phone,
            f"Dear {supplier_name}, your withholding receipt #{wr.get('receipt_number') or receipt_name} "
            f"for {amount_txt} {wr.get('currency') or 'ETB'} (Invoice IRN {wr.get('invoice_irn') or '-'}) "
            f"has been authorized by MoR. "
            f"Receipt ID: {wr.get('mor_receipt_id') or wr.get('rrn') or '-'} "
            f"Regards, {wr.get('agent_name') or 'Ethio Telecom'}."
        )

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

    to = _normalize_phone(phone)
    payload = {
        "from": (settings.get("afro_from_id") or "").strip(),
        "to": to,
        "message": (text or "")[:1000],
    }
    sender = _clean_sender(settings.get("afro_sender"))
    if sender:
        payload["sender"] = sender
    callback = (settings.get("afro_callback") or "").strip()
    if callback:
        payload["callback"] = callback

    session = requests.Session()
    headers = {"Authorization": "Bearer " + token}
    req = requests.Request("GET", base_url, params=payload, headers=headers)
    prepared = session.prepare_request(req)
    try:
        result = session.send(prepared, timeout=15)
        summary = f"EIMS SMS outbound {prepared.url} HTTP {result.status_code}: {result.text[:300]}"
        if result.status_code == 200:
            json = result.json()
            frappe.logger().info(summary.replace("EIMS SMS", "EIMS SMS ok"))
            if json["acknowledge"] == "success":
                return {"sent": True, "provider_id": result.json().get("message_id") or ""}
            return {"sent": False, "reason": "provider_error"}
        frappe.log_error(summary, "EIMS SMS")
        return {"sent": False, "reason": "provider_error"}
    except requests.exceptions.RequestException as e:
        frappe.log_error(f"EIMS SMS send failed (transport): {e}", "EIMS SMS")
        return {"sent": False, "reason": "transport_error"}
   

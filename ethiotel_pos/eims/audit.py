import frappe
from frappe.utils import now_datetime

from .sanitize import redact_payload


def log_audit(
    action,
    invoice_type=None,
    invoice=None,
    eims_status=None,
    document_number=None,
    success=True,
    description=None,
    request_brief=None,
    response_brief=None,
):

    if not frappe.db.exists("DocType", "EIMS Audit Log"):
        return
    try:
        frappe.get_doc(
            {
                "doctype": "EIMS Audit Log",
                "timestamp": now_datetime(),
                "user": frappe.session.user or "System",
                "action": action,
                "invoice_type": invoice_type if invoice_type else ("None" if invoice else None),
                "invoice": invoice,
                "eims_status": eims_status,
                "document_number": str(document_number) if document_number is not None else None,
                "success": 1 if success else 0,
                "ip_address": getattr(frappe.local, "request_ip", None),
                "description": description,
                "request_brief": redact_payload(request_brief),
                "response_brief": redact_payload(response_brief),
            }
        ).insert(ignore_permissions=True, ignore_mandatory=True)
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "EIMS Audit Log write failed")

import json

import frappe
from frappe import _

from .audit import log_audit

EIMS_CUSTOM_FIELDS = [
    "custom_irn",
    "custom_document_number",
    "custom_eims_status",
    "custom_eims_submitted_at",
    "custom_mor_total_value",
    "custom_mor_qr",
    "custom_eims_error_log",
    "custom_eims_retry_count",
    "custom_qr_code_url",
    "custom_conversation_id",
    "custom_cancelled_at",
    "custom_gps_lat",
    "custom_gps_lng",
]

INVOICE_CORE_FIELDS = ["name", "posting_date", "grand_total", "company", "customer"]

LAYOUT_DOCTYPES = [
    ("Sales Invoice", "custom_irn"),
    ("POS Invoice", "custom_irn"),
]


def _require_manager():
    if not frappe.has_permission("EIMS Setting", "write"):
        frappe.throw(_("Only System Managers can manage taxpayer data."), frappe.PermissionError)


def _confirm(confirm):
    if confirm not in (1, "1", True):
        frappe.throw(_("This destructive operation requires explicit confirmation."), frappe.PermissionError)


def _sanitize_setting():
    doc = frappe.get_doc("EIMS Setting")
    data = doc.as_dict()
    for secret in ("api_key", "current_access_token"):
        if secret in data:
            data[secret] = "***"
    return data


def _export_invoices():
    invoices = []
    for doctype, irn_field in LAYOUT_DOCTYPES:
        meta = frappe.get_meta(doctype)
        fields = [f for f in INVOICE_CORE_FIELDS if meta.has_field(f)]
        fields += [f for f in EIMS_CUSTOM_FIELDS if meta.has_field(f)]
        rows = frappe.db.get_all(
            doctype,
            fields=list(set(fields)),
            filters=[[irn_field, "is", "set"]],
            order_by="posting_date",
        )
        for row in rows:
            row["doctype"] = doctype
        invoices.extend(rows)

    manual_fields = [
        "name", "manual_invoice_number", "invoice_date", "company", "buyer_name",
        "buyer_tin", "currency", "pre_tax_total", "tax_total", "grand_total",
        "status", "custom_document_number", "custom_irn", "custom_qr_code_url",
    ]
    manual_rows = frappe.db.get_all(
        "EIMS Manual Invoice",
        fields=manual_fields,
        filters=[["custom_irn", "is", "set"]],
        order_by="invoice_date",
    )
    for row in manual_rows:
        row["doctype"] = "EIMS Manual Invoice"
    invoices.extend(manual_rows)
    return invoices


@frappe.whitelist()
def export_taxpayer_data():
    """Build a portable JSON archive and attach it as a File to EIMS Setting.
    Attached to EIMS Setting so an operator can see who exported what/when."""
    _require_manager()

    invoices = _export_invoices()

    archive = {
        "type": "eims_taxpayer_data_export",
        "exported_on": frappe.utils.now_datetime().isoformat(),
        "exported_by": frappe.session.user,
        "counts": {
            "sales_pos_invoices_registered": len(invoices),
            "audit_log_rows": frappe.db.count("EIMS Audit Log"),
            "geo_log_rows": frappe.db.count("EIMS Geo Log"),
            "verification_rows": frappe.db.count("EIMS Invoice Verification"),
            "mpos_devices": frappe.db.count("mPOS Device"),
        },
        "eims_setting": _sanitize_setting(),
        "invoices": invoices,
        "audit_log_rows": frappe.db.get_all("EIMS Audit Log", order_by="creation"),
        "geo_log_rows": frappe.db.get_all("EIMS Geo Log", order_by="creation"),
        "verification_rows": frappe.db.get_all("EIMS Invoice Verification", order_by="creation"),
        "mpos_devices": frappe.db.get_all("mPOS Device", order_by="creation"),
    }

    file_name = f"eims_taxpayer_export_{frappe.utils.nowdate()}_{frappe.utils.data.random_string(6)}.json"
    json_content = json.dumps(archive, indent=2, default=str)
    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": file_name,
        "is_private": 1,
        "attached_to_doctype": "EIMS Setting",
        "attached_to_name": "EIMS Setting",
        "content": json_content,
    })
    file_doc.insert(ignore_permissions=True)
    frappe.db.commit()

    log_audit(
        "Data Export",
        success=True,
        description=f"Taxpayer data exported: {len(invoices)} registered invoices, archive {file_doc.name}.",
    )
    frappe.db.commit()

    return {
        "file_url": file_doc.file_url,
        "file_name": file_name,
        "file_doc": file_doc.name,
        "counts": archive["counts"],
    }


def _clear_custom_fields():
    cleared = {}
    for doctype, _irn_field in LAYOUT_DOCTYPES:
        meta = frappe.get_meta(doctype)
        cleared[doctype] = 0
        for field in EIMS_CUSTOM_FIELDS:
            if meta.has_field(field):
                frappe.db.sql(
                    f"UPDATE `tab{doctype}` SET `{field}` = NULL WHERE `{field}` IS NOT NULL"
                )
                cleared[doctype] += frappe.db._cursor.rowcount
    return cleared


def _delete_generated_qr_files():
    names = frappe.db.get_all(
        "File",
        filters=[
            ["file_name", "like", "qr_%"],
            ["attached_to_doctype", "in", ("Sales Invoice", "POS Invoice")],
        ],
        pluck="name",
    )
    for name in names:
        frappe.delete_doc("File", name, ignore_permissions=True)
    return len(names)


@frappe.whitelist()
def purge_taxpayer_data(confirm=None):
    """Destroy EIMS companion data and clear EIMS tracking fields on invoices.
    Sales/POS Invoices themselves are never deleted; only EIMS metadata is removed."""
    _require_manager()
    _confirm(confirm)

    deleted = {
        "audit_log_rows": frappe.db.count("EIMS Audit Log"),
        "geo_log_rows": frappe.db.count("EIMS Geo Log"),
        "verification_rows": frappe.db.count("EIMS Invoice Verification"),
        "mpos_devices": frappe.db.count("mPOS Device"),
        "qr_files": 0,
    }

    frappe.db.delete("EIMS Audit Log", {})
    frappe.db.delete("EIMS Geo Log", {})
    frappe.db.delete("EIMS Invoice Verification", {})
    frappe.db.delete("mPOS Device", {})
    deleted["qr_files"] = _delete_generated_qr_files()
    deleted["custom_fields_cleared"] = _clear_custom_fields()
    frappe.db.commit()

    # Leave an immutable record of the purge itself.
    log_audit(
        "Data Purge",
        success=True,
        description=f"Taxpayer EIMS companion data purged: {deleted}.",
    )
    frappe.db.commit()

    return {"deleted": deleted}


@frappe.whitelist()
def terminate_service(confirm=None, purge_data=0):
    """Flag the taxpayer as terminated and optionally purge companion data.
    Blocks further EIRMS registration via the submit guard."""
    _require_manager()
    _confirm(confirm)

    purge_result = None
    if purge_data in (1, "1", True):
        purge_result = purge_taxpayer_data(confirm=confirm)

    frappe.db.set_value(
        "EIMS Setting", "EIMS Setting",
        {"service_terminated": 1, "terminated_on": frappe.utils.today()},
    )
    frappe.db.commit()

    log_audit(
        "Service Termination",
        success=True,
        description="EIMS registration service terminated for this taxpayer. New registrations are blocked.",
        response_brief=json.dumps({"purged": bool(purge_result)}, default=str),
    )
    frappe.db.commit()

    return {
        "service_terminated": True,
        "terminated_on": frappe.utils.today(),
        "purge": purge_result,
    }
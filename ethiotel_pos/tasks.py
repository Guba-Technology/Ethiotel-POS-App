import frappe

from ethiotel_pos.eims.connector import EIMSConnector
from ethiotel_pos.eims.logging_setup import eims_logger

EIMS_RETRY_STATUSES = ("Not Submitted", "Failed", "Pending")
RETRY_BATCH_LIMIT = 100


def _retry_settings():
    settings = frappe.get_doc("EIMS Setting")
    return {
        "auto_retry": bool(settings.get("auto_retry_failed_submissions")),
        "max_retries": int(settings.get("max_auto_retries") or 0),
    }


def _load_retry_batch(doctype):
    """Invoices still owed to EIRMS, oldest first, capped per run."""
    max_retries = _retry_settings()["max_retries"]
    names = frappe.db.get_all(
        doctype,
        filters={
            "docstatus": 1,
            "custom_eims_status": ["in", list(EIMS_RETRY_STATUSES)],
        },
        pluck="name",
        order_by="modified asc",
        limit=RETRY_BATCH_LIMIT,
    )
    to_retry = []
    for name in names:
        if max_retries and (frappe.db.get_value(doctype, name, "custom_eims_retry_count") or 0) >= max_retries:
            continue
        to_retry.append(name)
    return to_retry


def retry_failed_eims_submissions():
    """Hourly scheduler entry point (registered in hooks.scheduler_events).

    Re-submits invoices stuck in Not Submitted / Failed / Pending so offline
    sales posted during an EIRMS outage are registered automatically without
    a cashier clicking "Resend". Idempotent: reusing an invoice's assigned
    document number is handled safely by submit_single_invoice."""
    if not _retry_settings()["auto_retry"]:
        return

    for doctype in ("Sales Invoice", "POS Invoice"):
        to_retry = _load_retry_batch(doctype)
        if not to_retry:
            continue
        eims_logger.info("Auto-retry backlog for %s: %s invoices", doctype, len(to_retry))
        frappe.enqueue(
            "ethiotel_pos.tasks._retry_batch",
            doctype=doctype,
            names=to_retry,
            queue="short",
            timeout=900,
            now=frappe.flags.in_test,
        )


def _retry_batch(doctype, names):
    for name in names:
        try:
            result = EIMSConnector().submit_single_invoice(name)
            status = (result or {}).get("status")
            eims_logger.info("Auto-retry %s %s -> %s", doctype, name, status)
            if status != "Transmitted":
                _bump_retry_count(doctype, name)
        except frappe.ValidationError as ve:
            eims_logger.warning("Auto-retry declined %s %s: %s", doctype, name, ve)
            _bump_retry_count(doctype, name)
        except Exception:
            eims_logger.exception("Auto-retry crashed for %s %s", doctype, name)
            _bump_retry_count(doctype, name)


def _bump_retry_count(doctype, name):
    current = frappe.db.get_value(doctype, name, "custom_eims_retry_count") or 0
    frappe.db.set_value(doctype, name, "custom_eims_retry_count", current + 1, update_modified=False)
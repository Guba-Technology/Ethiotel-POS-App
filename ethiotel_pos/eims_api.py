# Minimal all-in-one API for EIMS automation
import json
import frappe
from frappe import _
from ethiotel_pos.eims_connector import EIMSConnector


@frappe.whitelist(allow_guest=True)
def get_token(force_refresh=False):
    """Return a valid EIMS token. Query param `force_refresh=1` forces renewal."""
    try:
        connector = EIMSConnector()
        token = connector.get_valid_token(force_refresh=bool(int(force_refresh)) if isinstance(force_refresh, (str, int)) else bool(force_refresh))
        return {"status": "ok", "token": token}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "EIMS API: get_token error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def submit_invoice(invoice_name):
    try:
        if not invoice_name:
            frappe.throw(_("Missing invoice_name"))

        connector = EIMSConnector()
        res = connector.submit_single_invoice(invoice_name)
        return {"status": "ok", "result": res}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "EIMS API: submit_invoice error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def submit_bulk(invoices_json):
    try:
        if not invoices_json:
            frappe.throw(_("Missing invoices_json"))

        if isinstance(invoices_json, str):
            try:
                parsed = json.loads(invoices_json)
            except Exception:
                parsed = [n.strip() for n in invoices_json.split(',') if n.strip()]
        else:
            parsed = invoices_json

        connector = EIMSConnector()
        res = connector.submit_bulk_invoices(parsed)
        return {"status": "ok", "result": res}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "EIMS API: submit_bulk error")
        return {"status": "error", "message": str(e)}


def _meta_has_field(doctype, fieldname):
    try:
        meta = frappe.get_meta(doctype)
        return meta.get_field(fieldname) is not None
    except Exception:
        return False


def _apply_invoice_result_to_sales_invoice(invoice_name, result):
    try:
        si = frappe.get_doc("Sales Invoice", invoice_name)
    except Exception:
        return {"updated": False, "reason": "Sales Invoice not found"}

    changed = False
    mappings = {
        ("status",): "eims_status",
        ("irn", "Irn", "IRN", "irn_number"): "irn",
        ("mor_doc_number", "mor", "document_number"): "mor_doc_number",
        ("message", "details"): "eims_response"
    }

    for keys, target in mappings.items():
        if _meta_has_field("Sales Invoice", target):
            for k in keys:
                if isinstance(result, dict) and k in result and result.get(k) is not None:
                    try:
                        setattr(si, target, result.get(k))
                        changed = True
                        break
                    except Exception:
                        continue

    if changed:
        try:
            si.save(ignore_permissions=True)
            frappe.db.commit()
            return {"updated": True}
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "EIMS API: saving Sales Invoice mapping failed")
            return {"updated": False, "reason": str(e)}

    return {"updated": False, "reason": "No mappable fields or no changes"}


@frappe.whitelist()
def submit_invoice_and_update(invoice_name):
    try:
        if not invoice_name:
            frappe.throw(_("Missing invoice_name"))

        connector = EIMSConnector()
        res = connector.submit_single_invoice(invoice_name)

        apply_res = _apply_invoice_result_to_sales_invoice(invoice_name, res or {})

        return {"status": "ok", "result": res, "applied": apply_res}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "EIMS API: submit_invoice_and_update error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def submit_bulk_and_update(invoices_json):
    try:
        if isinstance(invoices_json, str):
            try:
                parsed = json.loads(invoices_json)
            except Exception:
                parsed = [n.strip() for n in invoices_json.split(',') if n.strip()]
        else:
            parsed = invoices_json

        connector = EIMSConnector()
        batch = connector.submit_bulk_invoices(parsed)

        results_map = {}
        if isinstance(batch, dict) and "results" in batch:
            results_map = batch.get("results")

        applied = {}
        for inv in parsed:
            res = results_map.get(inv) if results_map else None
            if not res:
                res = connector.submit_single_invoice(inv)
            applied[inv] = _apply_invoice_result_to_sales_invoice(inv, res or {})

        return {"status": "ok", "batch": batch, "applied": applied}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "EIMS API: submit_bulk_and_update error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def verify_invoice_and_update(invoice_name=None, irn=None):

    try:
        if not irn and not invoice_name:
            frappe.throw(_("Provide either invoice_name or irn"))

        if not irn and invoice_name:
            try:
                si = frappe.get_doc("Sales Invoice", invoice_name)
                irn = getattr(si, "irn", None) or getattr(si, "eims_irn", None)
            except Exception:
                irn = None

        if not irn:
            frappe.throw(_("Unable to determine IRN for verification"))

        vres = verify_irn(irn)

        applied = None
        if invoice_name and isinstance(vres, dict) and vres.get("status") == "ok":
            result = vres.get("result") or {}
            # result may contain mor_doc_number
            applied = _apply_invoice_result_to_sales_invoice(invoice_name, result)

        return {"status": "ok", "verification": vres, "applied": applied}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "EIMS API: verify_invoice_and_update error")
        return {"status": "error", "message": str(e)}



@frappe.whitelist()
def verify_irn(irn):

    try:
        if not irn:
            frappe.throw(_("Missing irn"))

        doc = frappe.get_doc({"doctype": "EIMS Invoice Verification", "irn": irn})
        res = doc.trigger_remote_verification()
        return {"status": "ok", "result": res}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "EIMS API: verify_irn error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def generate_receipt_from_payment(payment_entry):

    try:
        if not payment_entry:
            frappe.throw(_("Missing payment_entry"))

        receipt = frappe.get_doc({"doctype": "EIMS Invoice Receipt", "payment_entry": payment_entry})
        receipt.fetch_payment_entry_details()
        result = receipt.trigger_remote_receipt_generation()

        try:
            if getattr(receipt, "eims_rrn", None) or getattr(receipt, "eims_status", None):
                receipt.insert(ignore_permissions=True)
                receipt.save()
                frappe.db.commit()
        except Exception:
            frappe.log_error(frappe.get_traceback(), "EIMS API: saving generated receipt failed")

        return {"status": "ok", "result": result}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "EIMS API: generate_receipt_from_payment error")
        return {"status": "error", "message": str(e)}

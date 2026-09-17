import json

from .audit import log_audit
from .logging_setup import eims_logger
from .sanitize import redact_payload
from ethiotel_pos.notify import _enqueue, send_registered_receipt

import frappe


class EIMSConnectorCallback:
    def _handle_callback(self):
        try:
            raw_body = frappe.request.get_data(as_text=True)
            eims_logger.debug("Callback received (redacted): %s", redact_payload(raw_body))

            if not raw_body or not raw_body.strip():
                eims_logger.debug("Empty callback body received - ignoring.")
                frappe.response["http_status_code"] = 200
                return {"status": "ignored_empty_body"}

            try:
                payload = json.loads(raw_body)
            except (ValueError, TypeError):
                eims_logger.exception("Callback body was not valid JSON")
                frappe.response["http_status_code"] = 400
                return {"status": "invalid_json"}

            items = payload if isinstance(payload, list) else payload.get("body", [payload])
            if not isinstance(items, list):
                items = [items]

            processed, skipped, failed = 0, 0, 0
            last_doc_num = self._peek_next_document_number() - 1

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
                        qr_code_url = self._save_qr_file(invoice_name, signed_qr_base64)

                        frappe.db.set_value("Sales Invoice", invoice_name, {
                            "custom_irn": irn,
                            "custom_qr_code_url": qr_code_url,
                            "custom_eims_status": "Registered",
                            "custom_conversation_id": item.get("conversationId") or item.get("conversionId"),
                            "custom_document_number": doc_no,
                        }, update_modified=True)
                        try:
                            doc_no_int = int(doc_no)
                            if doc_no_int > int(self.settings.last_document_number or 0):
                                self._commit_document_number(doc_no_int)
                        except (TypeError, ValueError):
                            pass
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
                        log_audit(
                            "Callback Confirmation",
                            invoice_type="Sales Invoice",
                            invoice=invoice_name,
                            eims_status="Registered",
                            document_number=doc_no,
                            success=True,
                            description="Async EIRMS confirmation received",
                            response_brief=raw_body[:2000],
                        )
                        _enqueue(send_registered_receipt, invoice_name=invoice_name, doctype="Sales Invoice")
                    else:
                        rule_error = item.get("ruleError")
                        error_detail = redact_payload(json.dumps(rule_error) if rule_error else json.dumps(item))

                        last_doc_num += 1
                        frappe.db.set_value("Sales Invoice", invoice_name, {
                            "custom_eims_status": "Failed",
                            "custom_document_number": last_doc_num,
                        }, update_modified=True)
                        frappe.log_error(message=error_detail, title=f"EIMS Callback Rejection: {invoice_name}")
                        log_audit(
                            "Callback Confirmation",
                            invoice_type="Sales Invoice",
                            invoice=invoice_name,
                            eims_status="Failed",
                            document_number=last_doc_num,
                            success=False,
                            description="Async EIRMS confirmation rejected the invoice",
                            response_brief=error_detail[:2000],
                        )
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

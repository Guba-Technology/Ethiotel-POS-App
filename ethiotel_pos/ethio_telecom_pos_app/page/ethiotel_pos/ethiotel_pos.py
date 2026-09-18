# Copyright (c) 2026, Ethiotel and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.utils import nowdate, add_days, flt, cint, now_datetime, getdate

from erpnext.accounts.doctype.pos_profile.pos_profile import get_item_groups
from erpnext.stock.get_item_details import get_conversion_factor

_pv = "ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos"


_POS_MOR_FIELDS = (
	("custom_sales_invoice", "Link", "Sales Invoice"),
	("custom_buyer_tin", "Data", None),
	("custom_eims_status", "Select", "\nNot Submitted\nRegistered\nPending\nFailed\nTransmitted\nCancelled"),
	("custom_mor_irn", "Data", None),
	("custom_document_number", "Int", None),
	("custom_irn", "Data", None),
	("custom_mor_total_value", "Currency", None),
	("custom_qr_code_url", "Attach Image", None),
	("custom_light_receipt_html", "Long Text", None),
	("custom_conversation_id", "Data", None),
)


def _ensure_pos_mor_fields():
	"""Create the POS Invoice MoR tracking fields on first use (avoids a
	full migrate in this environment)."""
	meta = frappe.get_meta("POS Invoice")
	for fieldname, fieldtype, options in _POS_MOR_FIELDS:
		if meta.get_field(fieldname):
			continue
		frappe.get_doc(
			{
				"doctype": "Custom Field",
				"dt": "POS Invoice",
				"fieldname": fieldname,
				"fieldtype": fieldtype,
				"label": fieldname.replace("custom_", "").replace("_", " ").title(),
				"options": options or "",
				"insert_after": "status",
			}
		).insert(ignore_permissions=True)
	frappe.db.commit()


def _get_or_create_walk_in_customer(company=None):
	"""Return the walk-in customer (auto-created on first use). Walk-in
	sales carry this name on the POS Invoice but are submitted to MoR as a
	minimal B2C invoice with no buyer registration details."""
	from ethiotel_pos.eims_connector import WALK_IN_CUSTOMER

	if frappe.db.exists("Customer", WALK_IN_CUSTOMER):
		return WALK_IN_CUSTOMER
	if not company:
		company = frappe.db.get_single_value("Global Defaults", "default_company")
	if not company:
		company = frappe.db.get_value("Company", {"is_group": 0}, "name")
	company_meta = frappe.get_meta("Company")
	customer_group = frappe.db.get_value("Company", company, "default_customer_group") if company_meta.has_field("default_customer_group") else None
	territory = frappe.db.get_value("Company", company, "default_territory") if company_meta.has_field("default_territory") else None
	if not customer_group or not frappe.db.exists("Customer Group", customer_group):
		customer_group = frappe.db.get_value("Customer Group", {"is_group": 0}, "name")
	if not territory or not frappe.db.exists("Territory", territory):
		territory = frappe.db.get_value("Territory", {"is_group": 0}, "name")
	cust = frappe.get_doc(
		{
			"doctype": "Customer",
			"customer_name": WALK_IN_CUSTOMER,
			"customer_type": "Individual",
			"customer_group": customer_group,
			"territory": territory,
		}
	)
	cust.flags.ignore_permissions = True
	cust.insert(ignore_permissions=True)
	frappe.db.commit()
	return WALK_IN_CUSTOMER


@frappe.whitelist()
def get_walk_in_customer():
	"""Return the walk-in customer name used when no customer is selected."""
	return {"status": "ok", "customer": _get_or_create_walk_in_customer()}


def _convert_pos_invoice_to_sales_invoice(pos_invoice_name):
	raise NotImplementedError("POS Invoices are registered with MoR directly and are never converted to Sales Invoices.")


@frappe.whitelist()
def register_with_mor(pos_invoice_name):
	"""Send a submitted POS Invoice directly to the MoR. The POS Invoice is
	its own EIMS registration — it is NOT converted into a Sales Invoice.
	The MoR document number is pulled from EIMS Setting (peek) and committed
	back only after a successful registration, exactly like Sales Invoices."""
	try:
		_ensure_pos_mor_fields()
		pos = frappe.get_doc("POS Invoice", pos_invoice_name)
		if pos.docstatus != 1:
			return {"status": "error", "message": _("Only submitted POS Invoices can be registered with MoR.")}
		if pos.custom_eims_status == "Registered":
			return {"status": "ok", "result": {"status": "Transmitted", "message": "Already Registered"}, "irn": pos.custom_irn or pos.custom_mor_irn, "eims_status": "Registered", "document_number": pos.custom_document_number, "qr_code_url": pos.get("custom_qr_code_url")}

		from ethiotel_pos.eims_connector import EIMSConnector

		res = EIMSConnector().submit_single_invoice(pos_invoice_name)

		irn = frappe.db.get_value("POS Invoice", pos_invoice_name, "custom_irn") or frappe.db.get_value("POS Invoice", pos_invoice_name, "custom_mor_irn")
		doc_num = frappe.db.get_value("POS Invoice", pos_invoice_name, "custom_document_number")
		status = frappe.db.get_value("POS Invoice", pos_invoice_name, "custom_eims_status") or res.get("status")
		qr_code_url = frappe.db.get_value("POS Invoice", pos_invoice_name, "custom_qr_code_url")
		frappe.db.commit()

		return {
			"status": "ok",
			"result": res,
			"irn": irn,
			"eims_status": status,
			"document_number": doc_num,
			"qr_code_url": qr_code_url,
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "V2 MoR registration error")
		return {"status": "error", "message": str(e)}


@frappe.whitelist()
def verify_mor_pos_invoice(pos_invoice_name=None, irn=None):
	"""Verify an MoR POS Invoice by its own IRN (no Sales Invoice involved)."""
	try:
		_ensure_pos_mor_fields()
		if not irn:
			irn = frappe.db.get_value("POS Invoice", pos_invoice_name, "custom_mor_irn") if pos_invoice_name else None
		if not irn:
			irn = frappe.db.get_value("POS Invoice", pos_invoice_name, "custom_irn") if pos_invoice_name else None
		if not irn:
			return {"status": "error", "message": _("Unable to determine IRN for verification")}

		doc = frappe.get_doc(
			{
				"doctype": "EIMS Invoice Verification",
				"select_registered_invoices": frappe.db.get_value("POS Invoice", pos_invoice_name, "custom_sales_invoice"),
				"pos_invoice": pos_invoice_name,
				"irn": irn.strip(),
			}
		)
		doc.insert(ignore_permissions=True, ignore_mandatory=True, ignore_links=True)
		res = doc.trigger_remote_verification()
		return {"status": "ok", "result": res, "irn": irn}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "V2 MoR verification error")
		return {"status": "error", "message": str(e)}


@frappe.whitelist()
def cancel_mor_pos_invoice(pos_invoice_name, cancellation_reasons="Order cancelled", remark=""):
	"""Cancel a registered MoR POS Invoice (single) using the EIMS Invoice
	Cancellation doctype. The POS Invoice is cancelled directly — no
	Sales Invoice is involved."""
	try:
		_ensure_pos_mor_fields()
		irn = frappe.db.get_value("POS Invoice", pos_invoice_name, "custom_mor_irn") or frappe.db.get_value("POS Invoice", pos_invoice_name, "custom_irn")
		if not irn:
			return {"status": "error", "message": _("No IRN found — invoice was never registered.")}

		doc = frappe.get_doc(
			{
				"doctype": "EIMS Invoice Cancellation",
				"is_bulk_cancellation": 0,
				"pos_invoice": pos_invoice_name,
				"irn": irn,
				"cancellation_reasons": cancellation_reasons,
				"remark": remark or f"Cancelled from POS: {pos_invoice_name}",
			}
		)
		doc.insert(ignore_permissions=True)
		res = doc.trigger_remote_cancellation()

		if res.get("status") == "Cancelled":
			frappe.db.set_value("POS Invoice", pos_invoice_name, "custom_eims_status", "Cancelled", update_modified=True)
			frappe.db.commit()
		return {"status": "ok", "result": res, "irn": irn}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "V2 MoR cancellation error")
		return {"status": "error", "message": str(e)}


@frappe.whitelist()
def register_sales_invoice(sales_invoice):

	try:
		si = frappe.get_doc("Sales Invoice", sales_invoice)
		if si.docstatus != 1:
			return {"status": "error", "message": _("Only submitted Sales Invoices can be registered with MoR.")}
		if si.custom_eims_status == "Registered":
			return {"status": "ok", "result": {"status": "Transmitted", "message": "Already Registered"}, "irn": si.custom_irn, "eims_status": "Registered"}

		from ethiotel_pos.eims_connector import EIMSConnector

		res = EIMSConnector().submit_single_invoice(sales_invoice)
		si.reload()

		res_status = str(res.get("status", "")).lower() if isinstance(res, dict) else ""
		ok = res_status in ("transmitted", "success")

		return {
			"status": "ok" if ok else "error",
			"result": res,
			"message": None if ok else (res.get("message") if isinstance(res, dict) else str(res)),
			"irn": si.custom_irn,
			"eims_status": si.custom_eims_status or res.get("status"),
			"document_number": si.custom_document_number,
			"qr_code_url": si.get("custom_qr_code_url"),
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "V2 MoR Sales Invoice registration error")
		return {"status": "error", "message": str(e)}


@frappe.whitelist()
def verify_sales_invoice(sales_invoice, irn=None):
	"""MoR task (desk Sales Invoice): verify a registered invoice via the
	EIMS Invoice Verification doctype."""
	try:
		irn = irn or frappe.db.get_value("Sales Invoice", sales_invoice, "custom_irn")
		if not irn:
			return {"status": "error", "message": _("Invoice has no IRN — register it with MoR first.")}

		irn = irn.strip()
		existing_name = frappe.db.get_value("EIMS Invoice Verification", {"irn": irn}, "name")
		if existing_name:
			doc = frappe.get_doc("EIMS Invoice Verification", existing_name)
		else:
			doc = frappe.get_doc(
				{
					"doctype": "EIMS Invoice Verification",
					"select_registered_invoices": sales_invoice,
					"irn": irn,
				}
			)
			doc.insert(ignore_permissions=True)

		res = doc.trigger_remote_verification()
		return {"status": "ok", "result": res, "irn": irn}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "V2 MoR Sales Invoice verification error")
		return {"status": "error", "message": str(e)}


@frappe.whitelist()
def cancel_sales_invoice(sales_invoice, cancellation_reasons="Order cancelled", remark=""):
	"""MoR task (desk Sales Invoice): cancel a registered invoice via the
	EIMS Invoice Cancellation doctype."""
	try:
		irn = frappe.db.get_value("Sales Invoice", sales_invoice, "custom_irn")
		if not irn:
			return {"status": "error", "message": _("No IRN found — invoice was never registered with MoR.")}

		doc = frappe.get_doc(
			{
				"doctype": "EIMS Invoice Cancellation",
				"is_bulk_cancellation": 0,
				"sales_invoice": sales_invoice,
				"irn": irn,
				"cancellation_reasons": cancellation_reasons,
				"remark": remark or f"Cancelled from Sales Invoice: {sales_invoice}",
			}
		)
		doc.insert(ignore_permissions=True)
		res = doc.trigger_remote_cancellation()

		if res.get("status") == "Cancelled":
			frappe.db.set_value("Sales Invoice", sales_invoice, "custom_eims_status", "Cancelled", update_modified=True)
			frappe.db.commit()
		return {"status": "ok", "result": res, "irn": irn}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "V2 MoR Sales Invoice cancellation error")
		return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_mor_details(sales_invoice):
	"""MoR task (desk Sales Invoice): everything the MoR Details dialog
	needs in one round-trip — registration fields, receipt and latest
	verification references, plus item/tax breakdown."""
	try:
		si = frappe.get_doc("Sales Invoice", sales_invoice)
		receipt_rows = frappe.db.sql(
			"""
			SELECT r.name, r.eims_rrn, r.eims_status, r.receipt_date
			FROM `tabEIMS Invoice Receipt` r
			JOIN `tabEIMS Invoice Receipt Reference` ref ON ref.parent = r.name
			WHERE (ref.sales_invoice = %s OR ref.pos_invoice = %s) AND r.docstatus < 2
			ORDER BY r.modified DESC LIMIT 1
			""",
			(sales_invoice, sales_invoice),
			as_dict=True,
		)
		verification = None
		if si.custom_irn:
			vrows = frappe.db.sql(
				"""
				SELECT name, verification_status, verified_at
				FROM `tabEIMS Invoice Verification`
				WHERE irn = %s
				ORDER BY modified DESC LIMIT 1
				""",
				(si.custom_irn,),
				as_dict=True,
			)
			verification = vrows[0] if vrows else None

		return {
			"status": "ok",
			"details": {
				"name": si.name,
				"eims_status": (si.custom_eims_status or "Not Submitted").strip(),
				"irn": si.custom_irn or "",
				"document_number": si.custom_document_number or "",
				"mor_total": flt(si.get("custom_mor_total_value")),
				"qr_code_url": si.custom_qr_code_url or "",
				"customer": si.customer,
				"customer_name": si.customer_name,
				"currency": si.currency,
				"net_total": flt(si.net_total),
				"discount_amount": flt(si.discount_amount),
				"total_taxes_and_charges": flt(si.total_taxes_and_charges),
				"grand_total": flt(si.grand_total),
				"posting_date": str(si.posting_date or ""),
				"posting_time": str(si.posting_time or ""),
				"owner": si.owner,
				"items": [
					{
						"item_code": it.item_code,
						"item_name": it.item_name,
						"qty": it.qty,
						"uom": it.uom,
						"rate": it.rate,
						"amount": it.amount,
					}
					for it in (si.items or [])
				],
				"taxes": [
					{
						"description": t.description or t.account_head,
						"rate": t.rate,
						"tax_amount": t.tax_amount,
					}
					for t in (si.taxes or [])
				],
			},
			"receipt": receipt_rows[0] if receipt_rows else None,
			"verification": verification,
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "V2 MoR Sales Invoice details error")
		return {"status": "error", "message": str(e)}


def _mor_registered_total(inv):
	"""Exact invoice total as registered with the MoR. Prefers the value
	stored at registration time; falls back to MoR's own verification
	record (authoritative); recomputes from the payload builder only as a
	last resort for invoices registered before both existed."""
	stored = flt(inv.get("custom_mor_total_value") or 0.0)
	if stored:
		return stored
	irn = inv.get("custom_irn")
	if irn:
		vrows = frappe.get_all(
			"EIMS Invoice Verification",
			filters={"irn": irn},
			fields=["total_value"],
			order_by="modified desc",
			limit=1,
		)
		if vrows and flt(vrows[0].total_value):
			return flt(vrows[0].total_value)
	try:
		from ethiotel_pos.eims_connector import EIMSConnector

		connector = EIMSConnector()
		doc_num = int(inv.get("custom_document_number") or 0) or connector._peek_next_document_number()
		payload = connector.build_invoice_payload(inv, override_doc_num=doc_num)
		return flt(payload["ValueDetails"]["TotalValue"])
	except Exception:
		frappe.log_error(frappe.get_traceback(), "V2 MoR total recompute failed")
		return flt(inv.grand_total)


def _build_invoice_receipt(invoice_name, doctype="Sales Invoice"):
	"""Create an EIMS Invoice Receipt document covering a registered
	Sales Invoice or POS Invoice (populated directly from the invoice —
	no Payment Entry)."""
	inv = frappe.get_doc(doctype, invoice_name)
	if inv.docstatus != 1 or not inv.custom_irn:
		frappe.throw(_("Invoice is not registered with MoR — no IRN found."))

	settings = frappe.get_single("EIMS Setting")
	default_client = None
	if settings.get("client_data_list"):
		for row in settings.client_data_list:
			if row.is_default == 1:
				try:
					default_client = frappe.get_doc(row.doctype, row.name)
				except Exception:
					default_client = None
				break

	existing = frappe.db.sql(
		"""
		SELECT parent FROM `tabEIMS Invoice Receipt Reference`
		WHERE (sales_invoice = %s OR pos_invoice = %s) AND docstatus < 2
		ORDER BY parent LIMIT 1
		""",
		(invoice_name, invoice_name),
	)
	if existing:
		receipt = frappe.get_doc("EIMS Invoice Receipt", existing[0][0])
		if receipt.eims_status != "Active":
			# Refresh stale amounts (receipts created before exact
			# registered totals were stored) so MoR accepts the retry.
			total_amount = _mor_registered_total(inv)
			receipt.collected_amount = total_amount
			for row in receipt.invoices_covered or []:
				if row.invoice_irn == inv.custom_irn:
					row.payment_coverage = "FULL"
					row.invoice_paid_amount = total_amount
					row.total_amount = total_amount
					row.remaining_amount = 0.0
			receipt.save(ignore_permissions=True)
			frappe.db.commit()
		return receipt

	receipt = frappe.new_doc("EIMS Invoice Receipt")
	doc_num = int(inv.custom_document_number or 0)
	total_amount = _mor_registered_total(inv)
	receipt.receipt_number = f"RCP-{doc_num if doc_num else inv.name}"
	receipt.receipt_type = "Sales Receipts"
	receipt.receipt_date = now_datetime()
	receipt.receipt_counter = doc_num
	receipt.eims_rrn = inv.custom_irn
	receipt.eims_status = "Pending"
	receipt.party_type = "Customer"
	receipt.party = inv.customer
	receipt.party_name = inv.customer_name
	receipt.mode_of_payment = "CASH"
	if inv.payments:
		from ethiotel_pos.eims_connector import resolve_mor_payment_mode
		mop = (inv.payments[0].mode_of_payment or "CASH")
		receipt.mode_of_payment = resolve_mor_payment_mode(mop) or "CASH"
	receipt.collected_amount = total_amount
	receipt.currency = inv.currency
	receipt.collector_name = inv.owner or "Cashier"
	receipt.seller_tin = settings.get("seller_tin") or ""
	if default_client:
		receipt.source_system_type = default_client.get("system_type")
		receipt.source_system_no = default_client.get("system_number")
	covered_row = {
		"invoice_irn": inv.custom_irn,
		"payment_coverage": "FULL",
		"invoice_paid_amount": total_amount,
		"discount_amount": float(inv.discount_amount or 0.0),
		"remaining_amount": 0.0,
		"total_amount": total_amount,
	}
	if doctype == "POS Invoice":
		covered_row["pos_invoice"] = inv.name
	else:
		covered_row["sales_invoice"] = inv.name
	receipt.append("invoices_covered", covered_row)
	receipt.insert(ignore_permissions=True)
	frappe.db.commit()
	return receipt


def _finalize_receipt_result(receipt, res):
	"""Idempotent handling of MoR's duplicate-receipt rejection.

	When MoR answers 406 with
	  "Receipt generated for the Invoice IRN given."
	a receipt ALREADY exists remotely for that IRN — typically because a
	previous attempt succeeded at MoR but failed locally (timeout, bad
	response, crash). Retrying forever would keep failing. Instead we mark
	the local receipt Active (it genuinely exists at MoR) and return it
	so the UI can navigate to it."""
	if not (isinstance(res, dict) and not res.get("success")):
		return None
	raw = str(res.get("message") or "")
	if "Receipt generated for the Invoice IRN given" not in raw:
		return None
	if receipt.eims_status != "Active":
		receipt.eims_status = "Active"
		receipt.response_log = f"{receipt.response_log or ''}\n[auto-heal] {raw[:2000]}"
		receipt.save(ignore_permissions=True)
		frappe.db.commit()
	return {
		"status": "ok",
		"already_active": True,
		"healed_duplicate": True,
		"receipt_name": receipt.name,
		"rrn": receipt.eims_rrn,
		"html": receipt.compile_receipt_html(),
	}


@frappe.whitelist()
def get_invoice_receipt(sales_invoice):
	"""MoR task (desk Sales Invoice): receipts are issued whenever money is
	received, i.e. against a SUBMITTED Payment Entry. This creates (or
	returns) the EIMS Invoice Receipt document populated from that Payment
	Entry and forwards the user to it — it NEVER transmits to MoR
	automatically; authorization happens from the receipt document."""
	try:
		inv = frappe.get_doc("Sales Invoice", sales_invoice)
		if inv.docstatus != 1:
			return {"status": "error", "message": _("Sales Invoice {0} is not submitted.").format(sales_invoice)}
		if not inv.custom_irn:
			return {"status": "error", "message": _("Invoice is not registered with MoR yet — no IRN found.")}

		payment_entry = _find_sales_invoice_payment(sales_invoice)
		if not payment_entry:
			return {
				"status": "no_payment_entry",
				"message": _(
					"No submitted Payment Entry found for {0}. A MoR receipt can only be issued after the payment is received and recorded."
				).format(sales_invoice),
			}

		receipt = _build_payment_receipt(inv, payment_entry)
		return {
			"status": "ok",
			"receipt_name": receipt.name,
			"payment_entry": payment_entry,
			"already_active": receipt.eims_status == "Active",
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "V2 MoR receipt generation error")
		return {"status": "error", "message": str(e)}


def _find_sales_invoice_payment(sales_invoice):
	"""Latest SUBMITTED Payment Entry covering this Sales Invoice."""
	rows = frappe.get_all(
		"Payment Entry Reference",
		filters={"reference_doctype": "Sales Invoice", "reference_name": sales_invoice},
		fields=["parent"],
		order_by="creation desc",
		limit=5,
	)
	for r in rows:
		if frappe.db.get_value("Payment Entry", r.parent, "docstatus") == 1:
			return r.parent
	return None


def _build_payment_receipt(inv, payment_entry):
	"""Create (or reuse) an EIMS Invoice Receipt for a registered Sales
	Invoice against its Payment Entry. Amounts are rebuilt from the exact
	registered totals by fetch_payment_entry_details(); nothing is sent
	to MoR here."""
	existing = frappe.db.sql(
		"""
		SELECT parent FROM `tabEIMS Invoice Receipt Reference`
		WHERE sales_invoice = %s AND docstatus < 2
		ORDER BY parent LIMIT 1
		""",
		(inv.name,),
	)
	if existing:
		receipt = frappe.get_doc("EIMS Invoice Receipt", existing[0][0])
		if receipt.eims_status != "Active":
			# Re-sync from the Payment Entry (exact registered totals).
			receipt.payment_entry = payment_entry
			receipt.fetch_payment_entry_details()
			receipt.save(ignore_permissions=True)
			frappe.db.commit()
		return receipt

	receipt = frappe.new_doc("EIMS Invoice Receipt")
	doc_num = int(inv.custom_document_number or 0)
	receipt.receipt_number = f"RCP-{doc_num if doc_num else inv.name}"
	receipt.receipt_type = "Sales Receipts"
	receipt.eims_status = "Pending"
	receipt.payment_entry = payment_entry
	receipt.remark = _("Auto-created from Payment Entry {0}").format(payment_entry)
	receipt.insert(ignore_permissions=True)
	# Populates party/mode/provider fields, eims_rrn, receipt_counter and
	# invoices_covered rows with EXACT registered totals (never rounded).
	receipt.fetch_payment_entry_details()
	receipt.save(ignore_permissions=True)
	frappe.db.commit()
	return receipt


@frappe.whitelist()
def get_pos_receipt(pos_invoice_name):
	"""MoR task (POS page): generate an EIMS Invoice Receipt for a POS
	Invoice directly (no Sales Invoice involved)."""
	try:
		_ensure_pos_mor_fields()
		pos = frappe.get_doc("POS Invoice", pos_invoice_name)
		if pos.docstatus != 1 or not (pos.custom_irn or pos.custom_mor_irn):
			return {"status": "error", "message": _("POS Invoice has not been registered with MoR yet.")}
		receipt = _build_invoice_receipt(pos_invoice_name, "POS Invoice")
		if receipt.eims_status == "Active":
			return {
				"status": "ok",
				"already_active": True,
				"receipt_name": receipt.name,
				"rrn": receipt.eims_rrn,
				"html": receipt.compile_receipt_html(),
			}
		res = receipt.trigger_remote_receipt_generation()
		healed = _finalize_receipt_result(receipt, res)
		if healed:
			return healed
		return {"status": "ok", "receipt_name": receipt.name, "result": res}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "V2 MoR POS receipt error")
		return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_forkiva_receipt(pos_invoice_name):
	"""Compact customer receipt: the Forkiva Sales Receipt print format
	rendered with the MoR QR code and IRN (when the invoice is
	registered). Returns standalone HTML including the format CSS."""
	try:
		pos = frappe.get_doc("POS Invoice", pos_invoice_name)
		if pos.docstatus != 1:
			return {"status": "error", "message": _("POS Invoice is not submitted yet.")}
		body = frappe.get_print(
			"POS Invoice",
			pos_invoice_name,
			print_format="Forkiva Sales Receipt",
			no_letterhead=1,
		)
		css = frappe.db.get_value("Print Format", "Forkiva Sales Receipt", "css") or ""
		return {"status": "ok", "html": f"<style>{css}</style>{_clean_print_html(body)}"}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "V2 Forkiva receipt error")
		return {"status": "error", "message": str(e)}


@frappe.whitelist()
def queue_mor_registration(pos_invoice_name):
	"""Fire-and-forget: hand the invoice to a background worker which
	registers it with MoR and pre-renders the light (Forkiva) receipt so
	the cashier never waits on MoR at the counter."""
	try:
		pos = frappe.get_doc("POS Invoice", pos_invoice_name)
		if pos.docstatus != 1:
			return {"status": "error", "message": _("Only submitted POS Invoices can be queued.")}
		frappe.enqueue(
			"ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos._register_and_prepare_receipt",
			queue="short",
			timeout=300,
			pos_invoice_name=pos_invoice_name,
			now=frappe.flags.in_test,
		)
		return {"status": "queued"}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "V2 MoR queue error")
		return {"status": "error", "message": str(e)}


def _register_and_prepare_receipt(pos_invoice_name):
	"""Background job: register with MoR (unless already registered), then
	pre-render and store the light customer receipt for instant access."""
	try:
		_ensure_pos_mor_fields()
		pos = frappe.get_doc("POS Invoice", pos_invoice_name)
		if pos.docstatus != 1:
			return
		if pos.custom_eims_status != "Registered":
			from ethiotel_pos.eims_connector import EIMSConnector

			EIMSConnector().submit_single_invoice(pos_invoice_name)
			frappe.db.commit()
		_prepare_light_receipt(pos_invoice_name)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Background MoR registration failed")


def _clean_print_html(raw_html):
	"""frappe.get_print() returns a FULL HTML document (head/body/scripts).
	Dialogs need only the printable fragment: extract the <body> content,
	drop every <script>, and keep any <style> blocks so the format still
	renders styled."""
	import re

	body_match = re.search(r"<body[^>]*>([\s\S]*)</body>", raw_html, re.I)
	body = body_match.group(1) if body_match else raw_html
	body = re.sub(r"<script[\s\S]*?</script>", "", body, flags=re.I)
	styles = "".join(re.findall(r"<style[^>]*>([\s\S]*?)</style>", raw_html, re.I))
	return f"<style>{styles}</style>{body}"


def _prepare_light_receipt(pos_invoice_name):
	"""Render the compact Forkiva receipt (with MoR QR + IRN when
	registered) and store it on the invoice for later one-click printing."""
	body = frappe.get_print(
		"POS Invoice",
		pos_invoice_name,
		print_format="Forkiva Sales Receipt",
		no_letterhead=1,
	)
	css = frappe.db.get_value("Print Format", "Forkiva Sales Receipt", "css") or ""
	frappe.db.set_value(
		"POS Invoice",
		pos_invoice_name,
		"custom_light_receipt_html",
		f"<style>{css}</style>{_clean_print_html(body)}",
		update_modified=False,
	)
	frappe.db.commit()


@frappe.whitelist()
def get_light_receipt(pos_invoice_name):
	"""Instant light (Forkiva) receipt for walk-in customers — served from
	the pre-rendered copy when available, rendered on demand otherwise."""
	try:
		pos = frappe.get_doc("POS Invoice", pos_invoice_name)
		if pos.docstatus != 1:
			return {"status": "error", "message": _("POS Invoice is not submitted yet.")}
		html = pos.get("custom_light_receipt_html")
		if not html:
			_prepare_light_receipt(pos_invoice_name)
			html = frappe.db.get_value("POS Invoice", pos_invoice_name, "custom_light_receipt_html")
		# Sanitize at serve time too — receipts stored before the fix may
		# still contain full-document markup. Receipts stored before the
		# big-QR / verification-link update are re-rendered once.
		stale = ("<script" in html.lower() or "<body" in html.lower()
			or "portal.mor.gov.et" not in html.lower())
		if html and stale:
			if "<script" in html.lower() or "<body" in html.lower():
				html = _clean_print_html(html)
				frappe.db.set_value(
					"POS Invoice", pos_invoice_name, "custom_light_receipt_html", html, update_modified=False
				)
				frappe.db.commit()
			else:
				_prepare_light_receipt(pos_invoice_name)
				html = frappe.db.get_value("POS Invoice", pos_invoice_name, "custom_light_receipt_html")
		return {
			"status": "ok",
			"html": html,
			"registered": bool(pos.custom_irn or pos.custom_mor_irn),
			"eims_status": pos.custom_eims_status or "Not Submitted",
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "V2 light receipt error")
		return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_mor_invoices(status="", search_term="", limit=50, offset=0):
	"""List submitted POS Invoices with their MoR status for the MoR
	workspace (filtered by custom_eims_status)."""
	try:
		_ensure_pos_mor_fields()
	except Exception as e:
		# Roll back any partial DB changes performed while attempting to
		# ensure required custom fields, then re-raise to stop invoice
		# insertion when setup is not available.
		frappe.db.rollback()
		raise
	cond = "docstatus = 1"
	params = []
	st = (status or "").strip()
	if st and st != "All":
		cond += " AND custom_eims_status = %s"
		params.append(st)
	if search_term:
		cond += " AND (name LIKE %s OR customer LIKE %s OR customer_name LIKE %s)"
		params += [f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"]
	rows = frappe.db.sql(
		f"""
		SELECT name, customer, customer_name, grand_total, net_total, currency,
		       total_taxes_and_charges, posting_date,
		       ifnull(custom_document_number, 0) AS custom_document_number,
		       ifnull(custom_eims_status, '') AS eims_status,
		       ifnull(custom_irn, ifnull(custom_mor_irn, '')) AS mor_irn,
		       ifnull(custom_sales_invoice, '') AS sales_invoice
		FROM `tabPOS Invoice`
		WHERE {cond}
		ORDER BY posting_date DESC, creation DESC
		LIMIT %s OFFSET %s
		""",
		params + [cint(limit), cint(offset)],
		as_dict=True,
	)

	stats = {"Registered": 0, "Pending": 0, "Failed": 0, "Cancelled": 0, "Not Submitted": 0}
	for row in frappe.db.sql(
		"""
		SELECT ifnull(custom_eims_status, 'Not Submitted') AS st, COUNT(*) AS n
		FROM `tabPOS Invoice`
		WHERE docstatus = 1
		GROUP BY ifnull(custom_eims_status, 'Not Submitted')
		""",
		as_dict=True,
	):
		key = (row.st or "Not Submitted").strip() or "Not Submitted"
		if key in stats:
			stats[key] = row.n

	return {"invoices": rows, "stats": stats}


@frappe.whitelist()
def check_opening_entry(user):
	"""
	Find the cashier's currently-open shift. A shift stays open until the
	cashier (or the close-shift route) links a POS Closing Entry, so this
	must match SUBMITTED (docstatus=1) POS Opening Entries that have no
	closing entry yet — same contract as the v1 POS.
	"""
	return frappe.db.sql(
		"""
		SELECT name, company, pos_profile, period_start_date, taxes_and_charges
		FROM `tabPOS Opening Entry`
		WHERE user = %s
		  AND docstatus = 1
		  AND (pos_closing_entry = '' OR pos_closing_entry IS NULL)
		ORDER BY period_start_date DESC
		""",
		user,
		as_dict=True,
	)


@frappe.whitelist()
def get_pos_profile_data(pos_profile):
	data = frappe.get_doc("POS Profile", pos_profile).as_dict()
	# Only offer payment methods the POS can actually send to MoR
	# (CASH, CHEQUE, CPO, Local Bank Transfer, SWIFT, Wire Transfer,
	# Letter of Credit, Card) and that exist on the profile.
	from ethiotel_pos.eims_connector import resolve_mor_payment_mode

	data["payments"] = [
		p for p in (data.get("payments") or [])
		if resolve_mor_payment_mode(p.get("mode_of_payment"))
	]
	return data


@frappe.whitelist()
def get_opening_payment_modes(pos_profile):
	"""MoR-valid payment modes configured on a POS Profile — used by the
	opening-shift dialog so cashiers only see methods that can be sent to
	MoR (rule 7022)."""
	from ethiotel_pos.eims_connector import resolve_mor_payment_mode

	profile = frappe.get_doc("POS Profile", pos_profile)
	modes = []
	for p in profile.payments or []:
		mode = p.mode_of_payment
		if mode and resolve_mor_payment_mode(mode) and mode not in modes:
			modes.append(mode)
	return modes


@frappe.whitelist()
def get_tax_templates():
	"""Enabled tax templates with their primary tax rate, plus the current
	EIMS Setting default — used by the sale workspace tax picker."""
	templates = frappe.db.sql(
		"SELECT name FROM `tabSales Taxes and Charges Template` WHERE disabled = 0 ORDER BY name",
		as_dict=True,
	)
	result = []
	for t in templates:
		doc = frappe.get_doc("Sales Taxes and Charges Template", t.name)
		tax_row = doc.get("taxes")[0] if doc.get("taxes") else None
		result.append(
			{
				"name": t.name,
				"rate": tax_row.rate if tax_row else 0,
				"account_head": tax_row.account_head if tax_row else None,
			}
		)
	return {
		"templates": result,
		"current": frappe.get_single("EIMS Setting").get("default_taxes_and_charges_template"),
	}


@frappe.whitelist()
def set_default_tax_template(tax_template=None):
	"""Persist the cashier's tax template choice onto the EIMS Setting so it
	becomes the default for future shifts/invoices."""
	if tax_template and not frappe.db.exists("Sales Taxes and Charges Template", tax_template):
		frappe.throw(f"Invalid tax template: {tax_template}")

	settings = frappe.get_single("EIMS Setting")
	settings.default_taxes_and_charges_template = tax_template or None
	settings.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "ok", "default_taxes_and_charges_template": settings.default_taxes_and_charges_template}


@frappe.whitelist()
def get_root_item_group():
	return frappe.db.sql(
		"SELECT name FROM `tabItem Group` WHERE lft = 1 AND is_group = 1 LIMIT 1",
		as_dict=True,
	)


@frappe.whitelist()
def resync_pos_data():
	"""Force-refresh cached POS data (item groups, prices, stock bins and
	the profiles themselves) so the sale workspace re-browses on next load.
	Used by the sidebar "Resync" action — replaces the dead v1-era call."""
	frappe.cache().delete_keys("*pos_profile*")
	frappe.cache().delete_keys("*item_group*")
	frappe.cache().delete_keys("*item_price*")
	frappe.cache().delete_keys("pos_profile")
	frappe.cache().delete_keys("item:data:*")
	frappe.clear_cache(doctype="Item")
	frappe.clear_cache(doctype="Bin")
	frappe.clear_cache(doctype="POS Profile")
	frappe.clear_cache(doctype="Item Price")
	frappe.clear_cache(doctype="Item Group")
	return {"status": "ok"}


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def item_group_query(doctype, txt, searchfield, start, page_len, filters):
	"""
	Category lookup for the sale workspace chips. Filters to the POS
	Profile's configured item groups (ports v1's item_group_query).
	"""
	item_groups = []
	cond = "is_group = 0"

	try:
		if isinstance(filters, str):
			filters = json.loads(filters)
	except Exception:
		filters = {}

	pos_profile = (filters or {}).get("pos_profile")

	if pos_profile:
		item_groups = get_item_groups(pos_profile)
		if item_groups:
			cond = "name in (%s)" % (", ".join(["%s"] * len(item_groups)))

	return frappe.db.sql(
		f"""
		SELECT DISTINCT name FROM `tabItem Group`
		WHERE {cond} AND (name LIKE %(txt)s)
		ORDER BY lft ASC
		LIMIT %(page_len)s OFFSET %(start)s
		""",
		{"txt": f"%{txt}%", "page_len": cint(page_len), "start": cint(start)},
	)


@frappe.whitelist()
def get_uom_conversion_factor(item_code, uom):
	"""Conversion factor between an item's stock uom and the given uom."""
	cf = get_conversion_factor(item_code, uom)
	return {"conversion_factor": cf.get("conversion_factor", 1)}


@frappe.whitelist()
def get_warehouse_stock(item_code, warehouse):
	"""Live stock availability for an item in a specific warehouse."""
	from erpnext.accounts.doctype.pos_invoice.pos_invoice import get_stock_availability

	actual_qty, is_stock_item, _is_negative_stock_allowed = get_stock_availability(
		item_code, warehouse
	)
	return {"actual_qty": flt(actual_qty), "is_stock_item": cint(is_stock_item)}


@frappe.whitelist()
def get_items(start, page_length, price_list, item_group, pos_profile, search_term=""):
	"""
	Browse/query products for the V2 sale workspace.
	Reuses the same query shape as the v1 POS but returns a flat list
	plus the category tree so the workspace can build its own UI.
	"""
	parent = frappe.db.sql(
		"SELECT name FROM `tabItem Group` WHERE lft = 1 AND is_group = 1 LIMIT 1", as_dict=True
	)
	parent_item_group = item_group or (parent[0].name if parent else "")

	if not frappe.db.exists("Item Group", parent_item_group):
		parent_item_group = "All Item Groups"

	pos_profile_doc = frappe.get_doc("POS Profile", pos_profile)
	warehouse = pos_profile_doc.warehouse or pos_profile_doc.set_warehouse
	hide_unavailable = frappe.db.get_value("POS Profile", pos_profile, "hide_unavailable_items")

	# item.item_group is included so the sale workspace's list view can
	# show each product's category as a subtitle.
	fields = "item.name AS item_code, item.item_name, item.item_group, item.description, item.stock_uom, item.image AS item_image, item.is_stock_item, item.sales_uom"

	lft, rgt = frappe.db.get_value("Item Group", parent_item_group, ["lft", "rgt"])

	search_cond = ""
	if search_term:
		search_cond = "AND (item.name LIKE %s OR item.item_name LIKE %s OR item.item_code LIKE %s)"

	bin_join = """LEFT JOIN (
			SELECT item_code, SUM(actual_qty) AS actual_qty
			FROM `tabBin`
			GROUP BY item_code
		) bin ON bin.item_code = item.name"""
	if hide_unavailable:
		bin_join = """LEFT JOIN (
			SELECT bin.item_code, bin.actual_qty
			FROM `tabBin` bin
			WHERE bin.warehouse = %s
		) bin ON bin.item_code = item.name"""

	sql = f"""
		SELECT {fields}, ip.price_list_rate, ip.uom, ip.currency, ip.batch_no,
		       ifnull(bin.actual_qty, 0) AS actual_qty
		FROM `tabItem` item
		LEFT JOIN (
			SELECT ip.item_code, ip.price_list_rate, ip.uom, ip.currency, ip.batch_no
			FROM `tabItem Price` ip
			WHERE ip.price_list = %s AND ip.selling = 1 AND %s BETWEEN ifnull(ip.valid_from, '2000-01-01') AND ifnull(ip.valid_upto, '2099-12-31')
		) ip ON ip.item_code = item.name
		{bin_join}
		WHERE item.disabled = 0
		  AND item.has_variants = 0
		  AND item.is_sales_item = 1
		  AND item.is_fixed_asset = 0
		  AND item.item_group in (SELECT name FROM `tabItem Group` WHERE lft >= %s AND rgt <= %s)
		  {search_cond}
		  {("AND actual_qty > 0" if hide_unavailable else "")}
		ORDER BY item.item_name ASC
		LIMIT %s OFFSET %s
	"""
	params = [price_list, nowdate()]
	if hide_unavailable:
		params.append(warehouse)
	params += [cint(lft), cint(rgt)]
	if search_term:
		params += [f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"]
	params += [cint(page_length), cint(start)]

	items = frappe.db.sql(sql, params, as_dict=True)

	return {
		"items": items,
		"warehouse": warehouse,
		"parent_item_group": parent_item_group,
	}


@frappe.whitelist()
def get_dashboard_data(pos_profile=None, from_date=None, to_date=None):
	from_date = from_date or nowdate()
	to_date = to_date or nowdate()

	cond = "docstatus = 1 AND posting_date BETWEEN %s AND %s"
	params = [from_date, to_date]
	if pos_profile:
		cond += " AND pos_profile = %s"
		params.append(pos_profile)

	sales_today = frappe.db.sql(
		f"SELECT ifnull(SUM(grand_total), 0) FROM `tabPOS Invoice` WHERE {cond}",
		params,
	)[0][0]

	transactions = frappe.db.sql(
		f"SELECT COUNT(name) FROM `tabPOS Invoice` WHERE {cond}",
		params,
	)[0][0]

	customers = frappe.db.sql(
		f"SELECT COUNT(DISTINCT customer) FROM `tabPOS Invoice` WHERE {cond}",
		params,
	)[0][0]

	held_orders = frappe.db.sql(
		"SELECT COUNT(name) FROM `tabPOS Invoice` WHERE docstatus = 0"
	)[0][0]

	# hourly sales for the last 24h (by hour of posting_time)
	hourly = frappe.db.sql(
		"""
		SELECT HOUR(posting_time) AS hr, ifnull(SUM(grand_total), 0) AS amount, COUNT(name) AS cnt
		FROM `tabPOS Invoice`
		WHERE docstatus = 1 AND posting_date = %s AND pos_profile = COALESCE(%s, pos_profile)
		GROUP BY HOUR(posting_time)
		ORDER BY hr
		""",
		(nowdate(), pos_profile),
		as_dict=True,
	)

	# payment methods
	payments = frappe.db.sql(
		"""
		SELECT sip.mode_of_payment, ifnull(SUM(sip.amount), 0) AS amount
		FROM `tabSales Invoice Payment` sip
		JOIN `tabPOS Invoice` si ON si.name = sip.parent
		WHERE si.docstatus = 1 AND si.posting_date BETWEEN %s AND %s AND si.pos_profile = COALESCE(%s, si.pos_profile)
		GROUP BY sip.mode_of_payment
		ORDER BY amount DESC
		""",
		(from_date, to_date, pos_profile),
		as_dict=True,
	)

	# top selling items
	top_items = frappe.db.sql(
		"""
		SELECT sii.item_code, sii.item_name, ifnull(SUM(sii.qty), 0) AS qty, ifnull(SUM(sii.base_net_amount), 0) AS amount
		FROM `tabPOS Invoice Item` sii
		JOIN `tabPOS Invoice` si ON si.name = sii.parent
		WHERE si.docstatus = 1 AND si.posting_date BETWEEN %s AND %s AND si.pos_profile = COALESCE(%s, si.pos_profile)
		GROUP BY sii.item_code, sii.item_name
		ORDER BY amount DESC
		LIMIT 8
		""",
		(from_date, to_date, pos_profile),
		as_dict=True,
	)

	# recent activity
	recent = frappe.db.sql(
		"""
		SELECT name, customer, customer_name, grand_total, posting_time, posting_date
		FROM `tabPOS Invoice`
		WHERE docstatus = 1 AND posting_date BETWEEN %s AND %s AND pos_profile = COALESCE(%s, pos_profile)
		ORDER BY creation DESC
		LIMIT 12
		""",
		(from_date, to_date, pos_profile),
		as_dict=True,
	)

	# cash drawer — opening amount of the current open shift + today's cash payment
	opening = frappe.db.sql(
		"""
		SELECT ifnull(SUM(bd.opening_amount), 0) AS amount
		FROM `tabPOS Opening Entry Detail` bd
		JOIN `tabPOS Opening Entry` o ON o.name = bd.parent
		WHERE o.docstatus = 0 AND o.pos_profile = COALESCE(%s, o.pos_profile)
		""",
		(pos_profile,),
		as_dict=True,
	)
	opening_amount = opening[0]["amount"] if opening else 0

	cash_in = frappe.db.sql(
		"""
		SELECT ifnull(SUM(sip.amount), 0)
		FROM `tabSales Invoice Payment` sip
		JOIN `tabPOS Invoice` si ON si.name = sip.parent
		WHERE si.docstatus = 1 AND si.posting_date = %s
		  AND lower(sip.mode_of_payment) LIKE '%%cash%%'
		  AND si.pos_profile = COALESCE(%s, si.pos_profile)
		""",
		(nowdate(), pos_profile),
	)[0][0]

	return {
		"sales_today": sales_today,
		"transactions": transactions,
		"customers": customers,
		"held_orders": held_orders,
		"hourly_sales": hourly,
		"payment_methods": payments,
		"top_items": top_items,
		"recent_activity": recent,
		"cash_drawer": {
			"opening_amount": opening_amount,
			"cash_in": cash_in,
			"expected": flt(opening_amount) + flt(cash_in),
		},
		"from_date": from_date,
		"to_date": to_date,
	}


@frappe.whitelist()
def get_customers(search_term="", limit=50, customer_group=None):
	cond = ""
	params = []
	if search_term:
		cond = " AND (name LIKE %s OR customer_name LIKE %s OR mobile_no LIKE %s)"
		params += [f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"]
	if customer_group:
		cond += " AND customer_group = %s"
		params.append(customer_group)

	return frappe.db.sql(
		f"""
		SELECT name, customer_name, customer_group, mobile_no, email_id, image, loyalty_program, territory, disabled
		FROM `tabCustomer`
		WHERE disabled = 0 {cond}
		ORDER BY customer_name ASC
		LIMIT %s
		""",
		params + [cint(limit)],
		as_dict=True,
	)


@frappe.whitelist()
def get_customer_details(customer):
	cust = frappe.db.get_value(
		"Customer",
		customer,
		["name", "customer_name", "customer_group", "mobile_no", "email_id", "image", "loyalty_program", "territory"],
		as_dict=True,
	)
	transactions = frappe.db.sql(
		"""
		SELECT name, grand_total, posting_date, posting_time, status, currency
		FROM `tabPOS Invoice`
		WHERE customer = %s AND docstatus = 1
		ORDER BY creation DESC
		LIMIT 15
		""",
		customer,
		as_dict=True,
	)
	return {"customer": cust, "transactions": transactions}


@frappe.whitelist()
def get_held_orders(search_term="", limit=50):
	cond = "docstatus = 0"
	params = []
	if search_term:
		cond += " AND (name LIKE %s OR customer LIKE %s)"
		params += [f"%{search_term}%", f"%{search_term}%"]
	return frappe.db.sql(
		f"""
		SELECT name, customer, customer_name, grand_total, currency, posting_time, posting_date
		FROM `tabPOS Invoice`
		WHERE {cond}
		ORDER BY creation DESC
		LIMIT %s
		""",
		params + [cint(limit)],
		as_dict=True,
	)


@frappe.whitelist()
def get_invoices(search_term="", status="", limit=50, from_date=None, to_date=None):
	try:
		_ensure_pos_mor_fields()
	except Exception:
		# Roll back any partial DB changes performed while attempting to
		# ensure required custom fields, then re-raise to stop offline
		# replay so the queued invoice remains for retry.
		frappe.db.rollback()
		raise
	cond = "1=1"
	params = []
	st = (status or "").strip()
	# docstatus / lifecycle filter
	if st in ("draft", "Draft", "not-submitted"):
		cond += " AND docstatus = 0"
	elif st in ("submitted",):
		cond += " AND docstatus = 1"
	elif st in ("cancelled", "Cancelled"):
		cond += " AND docstatus = 2"
	elif st in ("Paid", "Credit", "Return"):
		# these are POS Invoice `status` values on a submitted invoice
		cond += " AND docstatus = 1 AND status = %s"
		params.append(st)
	elif st and st != "All":
		# any other explicit status value
		cond += " AND status = %s"
		params.append(st)
	# "All" or empty -> every docstatus
	if search_term:
		cond += " AND (name LIKE %s OR customer LIKE %s OR customer_name LIKE %s)"
		params += [f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"]
	if from_date:
		cond += " AND posting_date >= %s"
		params.append(from_date)
	if to_date:
		cond += " AND posting_date <= %s"
		params.append(to_date)
	meta = frappe.get_meta("POS Invoice")
	extra_cols = ""
	for fieldname in ("custom_sales_invoice", "custom_eims_status", "custom_mor_irn"):
		if meta.get_field(fieldname):
			extra_cols += f", ifnull({fieldname}, '') AS {fieldname.replace('custom_', '')}"
	try:
		return frappe.db.sql(
			f"""
			SELECT name, customer, customer_name, grand_total, currency, status, posting_time, posting_date{extra_cols}
			FROM `tabPOS Invoice`
			WHERE {cond}
			ORDER BY creation DESC
			LIMIT %s
			""",
			params + [cint(limit)],
			as_dict=True,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "get_invoices failed")
		return []


@frappe.whitelist()
def get_sales_invoices(search_term="", status="", limit=50, from_date=None, to_date=None):
	"""List Sales Invoices (the converted/from-POS documents) for the
	Sales Invoice tab. Each row carries its source POS Invoice so the MoR
	actions can be routed through the POS Invoice registration helpers."""
	try:
		_ensure_pos_mor_fields()
	except Exception:
		frappe.db.rollback()
	cond = "1=1"
	params = []
	st = (status or "").strip()
	if st in ("Draft", "draft"):
		cond += " AND docstatus = 0"
	elif st in ("Submitted", "submitted"):
		cond += " AND docstatus = 1"
	elif st in ("Cancelled", "cancelled"):
		cond += " AND docstatus = 2"
	elif st and st not in ("All", "Paid", "Credit", "Return"):
		cond += " AND status = %s"
		params.append(st)
	if search_term:
		cond += " AND (name LIKE %s OR customer LIKE %s OR customer_name LIKE %s)"
		params += [f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"]
	if from_date:
		cond += " AND posting_date >= %s"
		params.append(from_date)
	if to_date:
		cond += " AND posting_date <= %s"
		params.append(to_date)
	meta = frappe.get_meta("Sales Invoice")
	extra_cols = ""
	for fieldname in ("custom_eims_status", "custom_irn"):
		if meta.get_field(fieldname):
			extra_cols += f", ifnull({fieldname}, '') AS {fieldname.replace('custom_', '')}"
	try:
		return frappe.db.sql(
			f"""
			SELECT name, customer, customer_name, grand_total, currency, status, posting_time, posting_date{extra_cols},
				(select name from `tabPOS Invoice` where custom_sales_invoice = `tabSales Invoice`.name limit 1) as pos_invoice
			FROM `tabSales Invoice`
			WHERE {cond}
			ORDER BY creation DESC
			LIMIT %s
			""",
			params + [cint(limit)],
			as_dict=True,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "get_sales_invoices failed")
		return []


@frappe.whitelist()
def make_sales_invoice_from_pos(pos_invoice_name):
	"""POS Invoices are registered with MoR directly and are never converted
	to Sales Invoices."""
	return {"status": "error", "message": _("POS Invoices are no longer converted to Sales Invoices.")}


@frappe.whitelist()
def get_sales_report(from_date=None, to_date=None, pos_profile=None):
	from_date = from_date or add_days(nowdate(), -30)
	to_date = to_date or nowdate()

	cond = "docstatus = 1 AND posting_date BETWEEN %s AND %s"
	params = [from_date, to_date]
	if pos_profile:
		cond += " AND pos_profile = %s"
		params.append(pos_profile)

	total_sales = frappe.db.sql(f"SELECT ifnull(SUM(grand_total), 0) FROM `tabPOS Invoice` WHERE {cond}", params)[0][0]
	invoice_count = frappe.db.sql(f"SELECT COUNT(name) FROM `tabPOS Invoice` WHERE {cond}", params)[0][0]
	avg_sale = (total_sales / invoice_count) if invoice_count else 0

	by_payment_mode = frappe.db.sql(
		f"""
		SELECT sip.mode_of_payment, ifnull(SUM(sip.amount), 0) AS amount
		FROM `tabSales Invoice Payment` sip
		JOIN `tabPOS Invoice` si ON si.name = sip.parent
		WHERE si.docstatus = 1 AND si.posting_date BETWEEN %s AND %s
		  AND si.pos_profile = COALESCE(%s, si.pos_profile)
		GROUP BY sip.mode_of_payment
		ORDER BY amount DESC
		""",
		(from_date, to_date, pos_profile),
		as_dict=True,
	)

	return {
		"total_sales": total_sales,
		"invoice_count": invoice_count,
		"avg_sale": avg_sale,
		"by_payment_mode": by_payment_mode,
		"from_date": from_date,
		"to_date": to_date,
	}


def _ensure_mop_mor_field():
	"""Create the MoR Payment Mode classification field on Mode of Payment
	on first use (avoids a full migrate in this environment)."""
	if frappe.get_meta("Mode of Payment").get_field("custom_mor_mode"):
		return
	frappe.get_doc(
		{
			"doctype": "Custom Field",
			"dt": "Mode of Payment",
			"fieldname": "custom_mor_mode",
			"fieldtype": "Select",
			"label": "MoR Payment Mode",
			"options": "\nCASH\nCHEQUE\nCPO\nLocal Bank Transfer\nSWIFT\nWire Transfer\nLetter of Credit\nCard",
			"insert_after": "type",
		}
	).insert(ignore_permissions=True)
	frappe.db.commit()


@frappe.whitelist()
def save_held_order(doc):
	"""Persist a POS invoice as a DRAFT (held order). Returns the doc name."""
	import json

	if isinstance(doc, str):
		doc = json.loads(doc)
	if not doc or doc.get("doctype") != "POS Invoice":
		frappe.throw("Invalid held order payload")

	# Make sure the MoR tracking fields (incl. custom_buyer_tin) exist on
	# POS Invoice before inserting the draft.
	try:
		_ensure_pos_mor_fields()
	except Exception:
		frappe.db.rollback()

	doc["doctype"] = "POS Invoice"
	doc["is_pos"] = 1
	doc["docstatus"] = 0

	# Validate the payment methods BEFORE the invoice exists — MoR rejects
	# registrations whose payment mode is not one of CASH, CHEQUE, CPO,
	# Local Bank Transfer, SWIFT, Wire Transfer, Letter of Credit, Card,
	# so catch it here while the cashier can still fix it.
	try:
		_ensure_mop_mor_field()
	except Exception:
		frappe.db.rollback()
	from ethiotel_pos.eims_connector import resolve_mor_payment_mode

	for pay in doc.get("payments") or []:
		mode_name = (pay.get("mode_of_payment") or "").strip()
		if mode_name and not resolve_mor_payment_mode(mode_name):
			frappe.throw(
				f"Payment method <b>{mode_name}</b> cannot be sent to MoR. "
				f"MoR accepts only: CASH, CHEQUE, CPO, Local Bank Transfer, SWIFT, "
				f"Wire Transfer, Letter of Credit, Card. Ask your administrator "
				f"to open <a href='/app/mode-of-payment/{mode_name}'>{mode_name}</a> "
				f"and set <b>MoR Payment Mode</b>.",
				title="Unsupported Payment Method"
			)

	# Resolve the tax template for this order: the payload wins, otherwise
	# fall back to the cashier's open shift, then the EIMS Setting default,
	# then the POS Profile. Always carry the chosen template onto the invoice
	# and, when no tax rows were sent, materialise them from the template so
	# ERPNext calculates taxes during insert (POS invoices skip the default
	# tax-master auto-application).
	tax_template = doc.get("taxes_and_charges")
	if not tax_template:
		opening = frappe.db.sql(
			"""
			SELECT taxes_and_charges
			FROM `tabPOS Opening Entry`
			WHERE user = %s AND docstatus = 1
			  AND (pos_closing_entry = '' OR pos_closing_entry IS NULL)
			ORDER BY period_start_date DESC
			LIMIT 1
			""",
			frappe.session.user,
			as_dict=True,
		)
		if opening and opening[0].taxes_and_charges:
			tax_template = opening[0].taxes_and_charges
	if not tax_template:
		tax_template = frappe.get_single("EIMS Setting").get("default_taxes_and_charges_template")
	if not tax_template:
		pos_profile_tax = frappe.db.get_value("POS Profile", doc.get("pos_profile"), "taxes_and_charges")
		tax_template = pos_profile_tax

	if tax_template:
		doc["taxes_and_charges"] = tax_template
		if not doc.get("taxes"):
			from erpnext.controllers.accounts_controller import get_taxes_and_charges

			doc["taxes"] = get_taxes_and_charges("Sales Taxes and Charges Template", tax_template) or []

	if not doc.get("customer"):
		doc["customer"] = _get_or_create_walk_in_customer(doc.get("company"))

	pos_inv = frappe.get_doc(doc)
	pos_inv.flags.ignore_permissions = True
	pos_inv.insert(ignore_permissions=True, ignore_mandatory=False)
	frappe.db.commit()
	return {"status": "ok", "invoice_name": pos_inv.name, "grand_total": pos_inv.grand_total}


@frappe.whitelist()
def submit_invoice(name):
	doc = frappe.get_doc("POS Invoice", name)
	if not doc.customer:
		doc.customer = _get_or_create_walk_in_customer(doc.company)
	doc.flags.ignore_permissions = True
	if doc.docstatus == 0:
		doc.submit()
	frappe.db.commit()
	return {"status": "ok", "invoice_name": doc.name, "grand_total": doc.grand_total}


@frappe.whitelist()
def delete_draft(name):
	frappe.db.delete("POS Invoice", {"name": name})
	frappe.db.commit()
	return {"status": "ok"}


@frappe.whitelist()
def get_item_by_barcode(barcode, price_list, pos_profile):
	"""Look up a single item by its barcode (any barcode in the Item Barcodes
	child table) and return it in the same shape as get_items rows so the sale
	workspace can push it straight into the cart."""
	from erpnext.stock.utils import scan_barcode

	scanned = scan_barcode(barcode)
	if not scanned or not scanned.get("item_code"):
		return {}

	item_code = scanned["item_code"]
	item = frappe.db.sql(
		"""
		SELECT item.name AS item_code, item.item_name, item.item_group, item.description, item.stock_uom,
		       item.image AS item_image, item.is_stock_item, item.sales_uom
		FROM `tabItem` item
		WHERE item.name = %s AND item.disabled = 0
		  AND item.has_variants = 0 AND item.is_sales_item = 1 AND item.is_fixed_asset = 0
		""",
		item_code,
		as_dict=True,
	)
	if not item:
		return {}
	item = item[0]

	# price for the profile's selling price list (today-valid)
	price = frappe.db.sql(
		"""
		SELECT ip.price_list_rate, ip.currency, ip.uom, ip.batch_no
		FROM `tabItem Price` ip
		WHERE ip.price_list = %s AND ip.item_code = %s AND ip.selling = 1
		  AND %s BETWEEN ifnull(ip.valid_from, '2000-01-01') AND ifnull(ip.valid_upto, '2099-12-31')
		ORDER BY ip.valid_from DESC
		LIMIT 1
		""",
		(price_list, item_code, nowdate()),
		as_dict=True,
	)
	item["price_list_rate"] = price[0]["price_list_rate"] if price else 0
	item["currency"] = price[0]["currency"] if price else frappe.get_cached_value("Company", frappe.defaults.get_user_default("company"), "default_currency")
	item["uom"] = (price[0]["uom"] or item.sales_uom or item.stock_uom) if price else (item.sales_uom or item.stock_uom)
	item["batch_no"] = price[0]["batch_no"] if price else None

	# stock across all warehouses (fall back to profile warehouse when available)
	warehouse = frappe.db.get_value("POS Profile", pos_profile, "warehouse")
	if warehouse:
		item["actual_qty"] = frappe.db.sql(
			"SELECT ifnull(actual_qty, 0) FROM `tabBin` WHERE item_code = %s AND warehouse = %s",
			(item_code, warehouse),
		)[0][0]
	else:
		item["actual_qty"] = frappe.db.sql(
			"SELECT ifnull(SUM(actual_qty), 0) FROM `tabBin` WHERE item_code = %s", item_code
		)[0][0]

	item["barcode"] = scanned.get("barcode")
	return item


def _sales_rows_cond(from_date=None, to_date=None, pos_profile=None, pos_opening=None):
	"""Shared WHERE clause for X/Z report queries. X uses the open-shift
	period (creation >= shift start); Z uses a date range."""
	cond = "docstatus = 1"
	params = []
	if pos_opening:
		entry = frappe.get_doc("POS Opening Entry", pos_opening)
		cond += " AND creation >= %s"
		params.append(entry.period_start_date)
		pos_profile = entry.pos_profile
	elif from_date and to_date:
		cond += " AND posting_date BETWEEN %s AND %s"
		params += [from_date, to_date]
	if pos_profile:
		cond += " AND pos_profile = %s"
		params.append(pos_profile)
	return cond, params, pos_profile


@frappe.whitelist()
def get_x_report(pos_opening=None, pos_profile=None):
	"""X report — intermediate reading for the currently-open shift
	(sales, counts, payments, taxes and a line-item summary)."""
	cond, params, pos_profile = _sales_rows_cond(pos_opening=pos_opening, pos_profile=pos_profile)

	invoices = frappe.db.sql(
		f"""
		SELECT name, customer, customer_name, grand_total, net_total, total_taxes_and_charges,
		       posting_date, posting_time, currency, creation
		FROM `tabPOS Invoice`
		WHERE {cond}
		ORDER BY creation ASC
		""",
		params,
		as_dict=True,
	)

	grand_total = flt(sum(i.grand_total or 0 for i in invoices))
	net_total = flt(sum(i.net_total or 0 for i in invoices))
	tax_total = flt(sum(i.total_taxes_and_charges or 0 for i in invoices))
	discount_total = flt(sum((i.discount_amount or 0) for i in invoices))
	item_count = 0
	invoice_count = len(invoices)

	items = frappe.db.sql(
		f"""
		SELECT sii.item_code, sii.item_name, ifnull(SUM(sii.qty), 0) AS qty,
		       ifnull(SUM(sii.base_net_amount), 0) AS amount
		FROM `tabPOS Invoice Item` sii
		JOIN `tabPOS Invoice` si ON si.name = sii.parent
		WHERE si.docstatus = 1
		  AND si.creation >= COALESCE((SELECT period_start_date FROM `tabPOS Opening Entry`
		     WHERE name = %s), '2000-01-01')
		  AND si.pos_profile = COALESCE(%s, si.pos_profile)
		GROUP BY sii.item_code, sii.item_name
		ORDER BY amount DESC
		LIMIT 100
		""",
		(pos_opening, pos_profile),
		as_dict=True,
	)
	item_count = flt(sum(i.qty for i in items))

	payments = frappe.db.sql(
		f"""
		SELECT sip.mode_of_payment, ifnull(SUM(sip.amount), 0) AS amount
		FROM `tabSales Invoice Payment` sip
		JOIN `tabPOS Invoice` si ON si.name = sip.parent
		WHERE si.docstatus = 1
		  AND si.creation >= COALESCE((SELECT period_start_date FROM `tabPOS Opening Entry`
		     WHERE name = %s), '2000-01-01')
		  AND si.pos_profile = COALESCE(%s, si.pos_profile)
		GROUP BY sip.mode_of_payment
		ORDER BY amount DESC
		""",
		(pos_opening, pos_profile),
		as_dict=True,
	)

	taxes = frappe.db.sql(
		f"""
		SELECT sit.account_head, sit.rate, ifnull(SUM(sit.tax_amount), 0) AS amount
		FROM `tabSales Taxes and Charges` sit
		JOIN `tabPOS Invoice` si ON si.name = sit.parent
		WHERE si.docstatus = 1
		  AND si.creation >= COALESCE((SELECT period_start_date FROM `tabPOS Opening Entry`
		     WHERE name = %s), '2000-01-01')
		  AND si.pos_profile = COALESCE(%s, si.pos_profile)
		GROUP BY sit.account_head, sit.rate
		ORDER BY amount DESC
		""",
		(pos_opening, pos_profile),
		as_dict=True,
	)

	return {
		"report_type": "X",
		"invoices": invoices,
		"grand_total": grand_total,
		"net_total": net_total,
		"tax_total": tax_total,
		"discount_total": discount_total,
		"invoice_count": invoice_count,
		"item_count": item_count,
		"avg_sale": (grand_total / invoice_count) if invoice_count else 0,
		"payments": payments,
		"items": items,
		"taxes": taxes,
		"pos_profile": pos_profile,
		"period_start": frappe.db.get_value("POS Opening Entry", pos_opening, "period_start_date")
		if pos_opening
		else None,
	}


@frappe.whitelist()
def get_z_report(from_date=None, to_date=None, pos_profile=None):
	"""Z report — daily / closed-period reading (full detail + totals)."""
	from_date = from_date or nowdate()
	to_date = to_date or nowdate()
	cond, params, pos_profile = _sales_rows_cond(
		from_date=from_date, to_date=to_date, pos_profile=pos_profile
	)

	invoices = frappe.db.sql(
		f"""
		SELECT name, customer, customer_name, grand_total, net_total, total_taxes_and_charges,
		       posting_date, posting_time, currency, creation
		FROM `tabPOS Invoice`
		WHERE {cond}
		ORDER BY posting_date ASC, posting_time ASC
		""",
		params,
		as_dict=True,
	)

	grand_total = flt(sum(i.grand_total or 0 for i in invoices))
	net_total = flt(sum(i.net_total or 0 for i in invoices))
	tax_total = flt(sum(i.total_taxes_and_charges or 0 for i in invoices))
	discount_total = flt(sum((i.discount_amount or 0) for i in invoices))
	invoice_count = len(invoices)

	items = frappe.db.sql(
		f"""
		SELECT sii.item_code, sii.item_name, ifnull(SUM(sii.qty), 0) AS qty,
		       ifnull(SUM(sii.base_net_amount), 0) AS amount
		FROM `tabPOS Invoice Item` sii
		JOIN `tabPOS Invoice` si ON si.name = sii.parent
		WHERE si.docstatus = 1 AND si.posting_date BETWEEN %s AND %s
		  AND si.pos_profile = COALESCE(%s, si.pos_profile)
		GROUP BY sii.item_code, sii.item_name
		ORDER BY amount DESC
		LIMIT 200
		""",
		(from_date, to_date, pos_profile),
		as_dict=True,
	)
	item_count = flt(sum(i.qty for i in items))

	payments = frappe.db.sql(
		f"""
		SELECT sip.mode_of_payment, ifnull(SUM(sip.amount), 0) AS amount
		FROM `tabSales Invoice Payment` sip
		JOIN `tabPOS Invoice` si ON si.name = sip.parent
		WHERE si.docstatus = 1 AND si.posting_date BETWEEN %s AND %s
		  AND si.pos_profile = COALESCE(%s, si.pos_profile)
		GROUP BY sip.mode_of_payment
		ORDER BY amount DESC
		""",
		(from_date, to_date, pos_profile),
		as_dict=True,
	)

	taxes = frappe.db.sql(
		f"""
		SELECT sit.account_head, sit.rate, ifnull(SUM(sit.tax_amount), 0) AS amount
		FROM `tabSales Taxes and Charges` sit
		JOIN `tabPOS Invoice` si ON si.name = sit.parent
		WHERE si.docstatus = 1 AND si.posting_date BETWEEN %s AND %s
		  AND si.pos_profile = COALESCE(%s, si.pos_profile)
		GROUP BY sit.account_head, sit.rate
		ORDER BY amount DESC
		""",
		(from_date, to_date, pos_profile),
		as_dict=True,
	)

	return {
		"report_type": "Z",
		"invoices": invoices,
		"grand_total": grand_total,
		"net_total": net_total,
		"tax_total": tax_total,
		"discount_total": discount_total,
		"invoice_count": invoice_count,
		"item_count": item_count,
		"avg_sale": (grand_total / invoice_count) if invoice_count else 0,
		"payments": payments,
		"items": items,
		"taxes": taxes,
		"pos_profile": pos_profile,
		"from_date": from_date,
		"to_date": to_date,
	}


@frappe.whitelist()
def save_offline_order(order, ref):
	"""Replay a POS Invoice that was queued in the browser while offline
	(mirrors the v1 endpoint so the same sync strategy works for V2)."""
	if isinstance(order, str):
		order = json.loads(order)

	if not order or order.get("doctype") != "POS Invoice":
		frappe.throw("Invalid offline order: missing POS Invoice details")

	try:
		_ensure_pos_mor_fields()
	except Exception:
		frappe.db.rollback()

	cleaned = {k: v for k, v in order.items() if not str(k).startswith("__")}
	cleaned["doctype"] = "POS Invoice"
	cleaned["is_pos"] = 1
	cleaned["docstatus"] = 0

	pos_inv = frappe.get_doc(cleaned)
	pos_inv.flags.ignore_permissions = True
	pos_inv.insert(ignore_permissions=True, ignore_mandatory=False)

	if pos_inv.docstatus == 0:
		pos_inv.submit()

	frappe.db.commit()
	frappe.db.set_value(
		"POS Invoice", pos_inv.name, "remarks", "Synced from offline queue: {0}".format(ref)
	)

	# Auto-register with MoR right after submission, mirroring the online
	# charge flow. A failure here must not fail the sync — the invoice can
	# be registered later from the MoR workspace.
	mor = {"irn": None, "registered": False}
	try:
		reg = register_with_mor(pos_inv.name)
		if reg.get("status") == "ok" and reg.get("irn"):
			mor = {"irn": reg.get("irn"), "registered": True}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Offline order MoR registration failed")

	return {
		"status": "ok",
		"invoice_name": pos_inv.name,
		"grand_total": pos_inv.grand_total,
		"mor": mor,
	}


@frappe.whitelist()
def get_shift_summary(pos_opening):
	"""Sales + payments made during the currently-open shift (used by the
	Check-in workspace and the shift dashboard)."""
	summary = {
		"sales_total": 0.0,
		"invoice_count": 0,
		"customer_count": 0,
		"payments": [],
		"opening_balance": {},
	}

	if not pos_opening:
		return summary

	entry = frappe.get_doc("POS Opening Entry", pos_opening)
	summary["period_start_date"] = entry.period_start_date
	summary["pos_profile"] = entry.pos_profile
	summary["company"] = entry.company

	for d in entry.balance_details:
		summary["opening_balance"][d.mode_of_payment] = d.opening_amount

	rows = frappe.db.sql(
		"""
		SELECT name, grand_total, customer, posting_date, posting_time
		FROM `tabPOS Invoice`
		WHERE docstatus = 1 AND creation >= %s AND pos_profile = %s
		""",
		(entry.period_start_date, entry.pos_profile),
		as_dict=True,
	)
	summary["invoice_count"] = len(rows)
	summary["sales_total"] = flt(sum(r.grand_total or 0) for r in rows)
	summary["customer_count"] = len({r.customer for r in rows})

	payments = frappe.db.sql(
		"""
		SELECT sip.mode_of_payment, ifnull(SUM(sip.amount), 0) AS amount
		FROM `tabSales Invoice Payment` sip
		JOIN `tabPOS Invoice` si ON si.name = sip.parent
		WHERE si.docstatus = 1 AND si.creation >= %s AND si.pos_profile = %s
		GROUP BY sip.mode_of_payment
		""",
		(entry.period_start_date, entry.pos_profile),
		as_dict=True,
	)
	summary["payments"] = payments
	return summary


@frappe.whitelist()
def close_shift(pos_opening):
	"""Create + submit the POS Closing Entry for the open shift, then link it
	back to the POS Opening Entry. Returns the closing entry details."""
	from erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry import make_closing_entry_from_opening

	opening = frappe.get_doc("POS Opening Entry", pos_opening)
	closing = make_closing_entry_from_opening(opening)
	closing.flags.ignore_permissions = True
	# Insert + commit the closing entry BEFORE submit(). on_submit runs
	# consolidate_pos_invoices which creates a POS Invoice Merge Log linked
	# to this closing entry; that link validation cannot see the uncommitted
	# row (separate read connection) and raises LinkValidationError.
	closing.insert()
	frappe.db.commit()
	closing.submit()
	frappe.db.commit()
	closing.update_opening_entry()
	frappe.db.commit()

	return {
		"status": "ok",
		"closing_entry": closing.name,
		"grand_total": closing.grand_total,
		"net_total": closing.net_total,
		"total_quantity": closing.total_quantity,
		"period_end_date": closing.period_end_date,
	}
@frappe.whitelist()
def create_opening_voucher(pos_profile, company, balance_details, taxes_and_charges=None):
	balance_details = json.loads(balance_details)

	new_pos_opening = frappe.get_doc(
		{
			"doctype": "POS Opening Entry",
			"period_start_date": frappe.utils.get_datetime(),
			"posting_date": frappe.utils.getdate(),
			"user": frappe.session.user,
			"pos_profile": pos_profile,
			"company": company,
			"taxes_and_charges": taxes_and_charges or None,
		}
	)
	new_pos_opening.set("balance_details", balance_details)
	new_pos_opening.submit()

	return new_pos_opening.as_dict()

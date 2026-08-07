# Copyright (c) 2026, Guba Technology
# Jinja / helpers used by EIMS-style print formats


import base64
import io

import frappe


def _qrcode_png_data_uri(text):
	try:
		import qrcode

		qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=6, border=2)
		qr.add_data(text)
		qr.make(fit=True)
		img = qr.make_image(fill_color="black", back_color="white")
		buf = io.BytesIO()
		img.save(buf, format="PNG")
		return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ethiotel_pos: QR generation error")
		return ""


def get_invoice_qr_data_uri(doc, tax=0):
	"""QR payload matching EIMS: Seller / Vat No / Date / Total / Tax."""
	total = doc.get("grand_total") or 0
	vatt = tax or doc.get("total_taxes_and_charges") or 0
	currency = doc.get("currency") or "ETB"
	date = doc.get("posting_date") or doc.get("date")
	payload = "\n".join(
		[
			"Seller: {0}".format(doc.get("company") or ""),
			"Vat No: {0}".format(doc.get("company_tax_id") or doc.get("tax_id") or ""),
			"Date: {0}".format(frappe.utils.formatdate(date) if date else ""),
			"Total: {0}".format(frappe.utils.fmt_money(total, currency=currency)),
			"Tax: {0}".format(frappe.utils.fmt_money(vatt, currency=currency)),
		]
	)
	return _qrcode_png_data_uri(payload)


def get_qr_img_tag(doc, tax=0, width=80):
	uri = get_invoice_qr_data_uri(doc, tax)
	if not uri:
		return ""
	return '<img src="{0}" width="{1}" height="{1}" alt="QR" />'.format(uri, width)


def eims_qr(data_uri):
	"""Jinja filter passthrough for a data uri."""
	return data_uri
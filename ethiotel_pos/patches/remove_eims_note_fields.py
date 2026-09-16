import frappe


def execute():
	"""Remove the EIMS note custom fields that are no longer needed.
	CRE/DEB document types are now derived from ERPNext's native return
	fields (is_return / is_debit_note / return_against) instead."""
	targets = [
		("Sales Invoice", "custom_eims_note_type"),
		("POS Invoice", "custom_eims_note_type"),
		("Sales Invoice", "custom_eims_original_invoice"),
	]
	for dt, fieldname in targets:
		name = frappe.db.get_value("Custom Field", {"dt": dt, "fieldname": fieldname})
		if name:
			frappe.delete_doc("Custom Field", name, ignore_permissions=True, force=1)
	frappe.db.commit()

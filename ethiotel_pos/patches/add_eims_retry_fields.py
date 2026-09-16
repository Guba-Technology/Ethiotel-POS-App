import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Sales Invoice": [
				dict(
					fieldname="custom_eims_retry_count",
					label="EIMS Retry Count",
					fieldtype="Int",
					default=0,
					insert_after="custom_mor_total_value",
					read_only=1,
					no_copy=1,
					print_hide=1,
				),
			],
			"POS Invoice": [
				dict(
					fieldname="custom_eims_retry_count",
					label="EIMS Retry Count",
					fieldtype="Int",
					default=0,
					insert_after="custom_mor_total_value",
					read_only=1,
					no_copy=1,
					print_hide=1,
				),
			],
		}
	)
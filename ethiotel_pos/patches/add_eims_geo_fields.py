import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Sales Invoice": [
				dict(
					fieldname="custom_gps_lat",
					label="GPS Latitude",
					fieldtype="Float",
					insert_after="custom_eims_retry_count",
					no_copy=1,
					print_hide=1,
				),
				dict(
					fieldname="custom_gps_lng",
					label="GPS Longitude",
					fieldtype="Float",
					insert_after="custom_gps_lat",
					no_copy=1,
					print_hide=1,
				),
			],
			"POS Invoice": [
				dict(
					fieldname="custom_gps_lat",
					label="GPS Latitude",
					fieldtype="Float",
					insert_after="custom_eims_retry_count",
					no_copy=1,
					print_hide=1,
				),
				dict(
					fieldname="custom_gps_lng",
					label="GPS Longitude",
					fieldtype="Float",
					insert_after="custom_gps_lat",
					no_copy=1,
					print_hide=1,
				),
			],
		}
	)
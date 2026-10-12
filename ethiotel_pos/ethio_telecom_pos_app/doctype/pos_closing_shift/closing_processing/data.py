import frappe
from frappe.utils import cint
from ethiotel_pos.ethio_telecom_pos_app.doctype.pos_closing_shift.closing_processing.invoices import (
    submit_printed_invoices,
)


@frappe.whitelist()
def get_cashiers(doctype, txt, searchfield, start, page_len, filters):
    cashiers_list = frappe.get_all("POS Profile User", filters=filters, fields=["user"])
    result = []
    for cashier in cashiers_list:
        user_email = frappe.get_value("User", cashier.user, "email")
        if user_email:
            # Return list of tuples in format (value, label) where value is user ID and label shows both ID and email
            result.append([cashier.user, f"{cashier.user} ({user_email})"])
    return result


@frappe.whitelist()
def get_pos_invoices(pos_opening_shift, doctype=None, submit_printed=1):
    if not doctype:
        pos_profile = frappe.db.get_value("POS Opening Shift", pos_opening_shift, "pos_profile")
        use_pos_invoice = frappe.db.get_value(
            "POS Profile",
            pos_profile,
            "create_pos_invoice_instead_of_sales_invoice",
        )
        doctype = "POS Invoice" if use_pos_invoice else "Sales Invoice"
    if cint(submit_printed):
        submit_printed_invoices(pos_opening_shift, doctype)
    cond = " and ifnull(consolidated_invoice,'') = ''" if doctype == "POS Invoice" else ""
    data = frappe.db.sql(
        f"""
	select
		name
	from
		`tab{doctype}`
	where
		docstatus = 1 and posa_pos_opening_shift = %s{cond}
	""",
        (pos_opening_shift),
        as_dict=1,
    )

    data = [frappe.get_doc(doctype, d.name).as_dict() for d in data]

    return data


@frappe.whitelist()
def get_payments_entries(pos_opening_shift):
    return frappe.get_all(
        "Payment Entry",
        filters={
            "docstatus": 1,
            "reference_no": pos_opening_shift,
            "payment_type": ["in", ["Receive", "Pay"]],
        },
        fields=[
            "name",
            "mode_of_payment",
            "paid_amount",
            "base_paid_amount",
            "unallocated_amount",
            "paid_from_account_currency",
            "paid_to_account_currency",
            "target_exchange_rate",
            "reference_no",
            "posting_date",
            "party_type",
            "party",
            "payment_type",
        ],
    )


def get_payment_entry_references(payment_entry_names):
    """Return the Payment Entry References of the given entries, grouped by entry."""

    references_by_entry = {}

    payment_entry_names = [name for name in payment_entry_names or [] if name]
    if not payment_entry_names:
        return references_by_entry

    reference_meta = frappe.get_meta("Payment Entry Reference")
    reference_fieldnames = {df.fieldname for df in reference_meta.get("fields", [])}
    reference_fields = [
        "parent",
        "reference_doctype",
        "reference_name",
        "allocated_amount",
    ]

    for fieldname in (
        "exchange_rate",
        "allocated_amount_in_company_currency",
        "base_allocated_amount",
    ):
        if fieldname in reference_fieldnames:
            reference_fields.append(fieldname)

    reference_rows = frappe.get_all(
        "Payment Entry Reference",
        filters={"parent": ["in", payment_entry_names]},
        fields=reference_fields,
    )

    for reference in reference_rows:
        references_by_entry.setdefault(reference.get("parent"), []).append(reference)

    return references_by_entry

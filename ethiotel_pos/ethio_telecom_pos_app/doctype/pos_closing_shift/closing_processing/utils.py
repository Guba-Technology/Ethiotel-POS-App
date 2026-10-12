import frappe
from frappe.utils import flt


def get_base_value(doc, fieldname, base_fieldname=None, conversion_rate=None):
    """Return the value for a field in company currency."""

    base_fieldname = base_fieldname or f"base_{fieldname}"
    base_value = doc.get(base_fieldname)

    if base_value not in (None, ""):
        return flt(base_value)

    value = doc.get(fieldname)
    if value in (None, ""):
        return 0

    if conversion_rate is None:
        conversion_rate = (
            doc.get("conversion_rate")
            or doc.get("source_exchange_rate")
            or doc.get("target_exchange_rate")
            or doc.get("exchange_rate")
            or 1
        )

    return flt(value) * flt(conversion_rate or 1)


def net_change_from_payments(payment_rows, change_amount=None, base_change_amount=None, conversion_rate=None):
    """Return the payment rows of an invoice with the change netted out exactly once.

    `payments` rows hold the gross tender the customer handed over, so the change
    that came back out of the drawer has to be removed once. It comes off the row
    that overpaid - the largest tender - and never off the drawer when another
    mode handed back the money.
    """

    rows = []
    for payment in payment_rows or []:
        rows.append(
            {
                "row": payment,
                "mode_of_payment": payment.get("mode_of_payment"),
                "amount": flt(payment.get("amount") or 0),
                "base_amount": get_base_value(payment, "amount", "base_amount"),
            },
        )

    if not rows:
        return rows

    change_base = flt(base_change_amount or 0)
    if not change_base and change_amount:
        change_base = flt(change_amount) * flt(conversion_rate or 1)

    if not change_base:
        return rows

    # The change cannot be larger than the tender that produced it.
    target_index = None
    for index, row in enumerate(rows):
        if row["base_amount"] <= 0:
            continue
        if target_index is None or row["base_amount"] > rows[target_index]["base_amount"]:
            target_index = index

    if target_index is not None:
        target = rows[target_index]
        row_rate = abs(target["base_amount"]) / abs(target["amount"]) if target["amount"] else 0
        if row_rate:
            target["amount"] -= change_base / row_rate
        target["base_amount"] -= change_base

    return rows


def reference_base_amount(reference, fallback_rate=None):
    """Return the allocated amount of a Payment Entry Reference in company currency."""

    for fieldname in ("allocated_amount_in_company_currency", "base_allocated_amount"):
        value = reference.get(fieldname)
        if value not in (None, ""):
            return flt(value)

    amount_value = flt(reference.get("allocated_amount") or 0)
    rate_value = reference.get("exchange_rate") or fallback_rate or 1
    return amount_value * flt(rate_value or 1)


def remaining_change_after_refund(base_change_total, base_paid_amount):
    """Split a refund into the part that is this shift's change and the rest.

    Change handed back while serving this shift's sales is already netted out of
    the invoice tender, so it must not reduce the drawer a second time. Only a
    refund beyond that (returning an older advance, for example) is real cash out.
    """

    paid_amount = abs(flt(base_paid_amount or 0))
    covered_change = min(abs(flt(base_change_total or 0)), paid_amount)
    return covered_change, paid_amount - covered_change

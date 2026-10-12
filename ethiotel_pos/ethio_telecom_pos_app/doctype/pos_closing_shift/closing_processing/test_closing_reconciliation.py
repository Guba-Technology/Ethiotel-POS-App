import importlib.util
import json
import pathlib
import sys
import types
import unittest
from types import SimpleNamespace


CLOSING_PROCESSING_PATH = pathlib.Path(__file__).resolve().parent
OVERVIEW_PATH = CLOSING_PROCESSING_PATH / "overview.py"
CREATION_PATH = CLOSING_PROCESSING_PATH / "creation.py"
UTILS_PATH = CLOSING_PROCESSING_PATH / "utils.py"
PACKAGE = "ethiotel_pos.ethio_telecom_pos_app.doctype.pos_closing_shift.closing_processing"


class AttrDict(dict):
    __getattr__ = dict.get


class FakeDoc(AttrDict):
    """Minimal stand-in for a frappe document."""

    def set(self, fieldname, value):
        self[fieldname] = value

    def append(self, fieldname, row):
        self.setdefault(fieldname, []).append(row)

    def get(self, fieldname, default=None):
        return dict.get(self, fieldname, default)


def _cash_row(amount, base_amount=None, mode="Cash"):
    return AttrDict(
        {
            "mode_of_payment": mode,
            "currency": "USD",
            "amount": amount,
            "base_amount": amount if base_amount is None else base_amount,
        },
    )


def _invoice(name="SINV-0001", grand_total=100, change_amount=0, payments=None, **kwargs):
    return AttrDict(
        {
            "name": name,
            "doctype": "Sales Invoice",
            "customer": "Customer A",
            "currency": "USD",
            "conversion_rate": 1,
            "grand_total": grand_total,
            "rounded_total": grand_total,
            "base_grand_total": grand_total,
            "net_total": grand_total,
            "base_net_total": grand_total,
            "outstanding_amount": 0,
            "base_outstanding_amount": 0,
            "change_amount": change_amount,
            "base_change_amount": change_amount,
            "total_qty": 1,
            "is_return": 0,
            "posting_date": "2026-01-01",
            "payments": payments if payments is not None else [],
            "taxes": [],
            **kwargs,
        },
    )


def _payment_entry(name, payment_type="Receive", amount=0, references=None, **kwargs):
    return AttrDict(
        {
            "name": name,
            "mode_of_payment": "Cash",
            "payment_type": payment_type,
            "paid_amount": amount,
            "base_paid_amount": amount,
            "unallocated_amount": 0,
            "paid_from_account_currency": "USD",
            "paid_to_account_currency": "USD",
            "target_exchange_rate": 1,
            "reference_no": "POS-OPEN-1",
            "posting_date": "2026-01-01",
            "party_type": "Customer",
            "party": "Customer A",
            "references": references or [],
            **kwargs,
        },
    )


def _reference(parent, reference_name, allocated, reference_doctype="Sales Invoice"):
    return AttrDict(
        {
            "parent": parent,
            "reference_doctype": reference_doctype,
            "reference_name": reference_name,
            "allocated_amount": allocated,
            "base_allocated_amount": allocated,
            "exchange_rate": 1,
        },
    )


def _install_stubs(invoices, payment_entries):
    frappe_module = types.ModuleType("frappe")
    frappe_utils_module = types.ModuleType("frappe.utils")
    data_module = types.ModuleType(PACKAGE + ".data")
    invoices_module = types.ModuleType(PACKAGE + ".invoices")

    frappe_module._ = lambda text: text
    frappe_module.whitelist = lambda *args, **kwargs: (lambda fn: fn)
    frappe_module.throw = lambda message: (_ for _ in ()).throw(Exception(message))
    frappe_module.DoesNotExistError = Exception
    frappe_module.get_cached_value = lambda doctype, name, field: "USD"
    frappe_module.get_doc = lambda doctype, name: SimpleNamespace(
        doctype="POS Opening Shift",
        name=name,
        pos_profile="POS-PROFILE-1",
        company="My Co",
    )
    frappe_module.get_all = lambda *args, **kwargs: []
    frappe_module.get_meta = lambda *args, **kwargs: SimpleNamespace(get=lambda key, default=None: [])

    def get_value(doctype, name, field):
        if field == "create_pos_invoice_instead_of_sales_invoice":
            return 0
        if field == "posa_cash_mode_of_payment":
            return "Cash"
        if field == "posa_pos_opening_shift":
            return "POS-OPEN-1"
        return None

    frappe_module.db = SimpleNamespace(get_value=get_value, get_all=lambda *a, **k: [])
    frappe_utils_module.flt = lambda value=0, precision=None: float(value or 0)
    frappe_utils_module.json = __import__("json")

    references_by_entry = {}
    for entry in payment_entries:
        references_by_entry[entry["name"]] = entry.get("references") or []

    data_module.get_pos_invoices = lambda *args, **kwargs: invoices
    data_module.get_payments_entries = lambda *args, **kwargs: payment_entries
    data_module.get_payment_entry_references = lambda names: {
        name: references_by_entry.get(name) or [] for name in (names or [])
    }
    invoices_module.submit_printed_invoices = lambda *args, **kwargs: None

    sys.modules["frappe"] = frappe_module
    sys.modules["frappe.utils"] = frappe_utils_module
    sys.modules[PACKAGE + ".data"] = data_module
    sys.modules[PACKAGE + ".invoices"] = invoices_module

    utils_spec = importlib.util.spec_from_file_location(PACKAGE + ".utils", UTILS_PATH)
    utils_module = importlib.util.module_from_spec(utils_spec)
    sys.modules[PACKAGE + ".utils"] = utils_module
    utils_spec.loader.exec_module(utils_module)

    frappe_module._dict = AttrDict


def _load_module(module_name, path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestClosingOverviewReconciliation(unittest.TestCase):
    def _overview(self, invoices, payment_entries):
        _install_stubs(invoices, payment_entries)
        module = _load_module(PACKAGE + ".overview", OVERVIEW_PATH)
        return module.get_closing_shift_overview("POS-OPEN-1")

    def _cash_total(self, result):
        return result["cash_expected"]["company_currency_total"]

    def test_plain_cash_sale_counts_the_tender(self):
        result = self._overview([_invoice(payments=[_cash_row(100)])], [])

        self.assertEqual(self._cash_total(result), 100)
        self.assertEqual(result["change_returned"]["company_currency_total"], 0)

    def test_advance_redemption_entry_is_not_counted_twice(self):
        invoice = _invoice(payments=[_cash_row(60)])
        entry = _payment_entry(
            "PE-RCV-1",
            "Receive",
            60,
            references=[_reference("PE-RCV-1", invoice["name"], 60)],
        )

        result = self._overview([invoice], [entry])

        self.assertEqual(self._cash_total(result), 60)

    def test_external_advance_is_counted_once(self):
        entry = _payment_entry("PE-RCV-2", "Receive", 40, unallocated_amount=40)

        result = self._overview([_invoice(payments=[_cash_row(100)])], [entry])

        self.assertEqual(self._cash_total(result), 140)

    def test_change_is_netted_out_of_a_cash_sale_without_payment_entry(self):
        invoice = _invoice(grand_total=100, change_amount=20, payments=[_cash_row(120)])

        result = self._overview([invoice], [])

        self.assertEqual(self._cash_total(result), 100)
        self.assertEqual(result["change_returned"]["company_currency_total"], 20)

    def test_change_is_netted_out_once_when_a_change_entry_exists(self):
        invoice = _invoice(grand_total=100, change_amount=20, payments=[_cash_row(120)])
        entry = _payment_entry(
            "PE-PAY-1",
            "Pay",
            20,
            references=[_reference("PE-PAY-1", invoice["name"], 20)],
        )

        result = self._overview([invoice], [entry])

        self.assertEqual(self._cash_total(result), 100)
        self.assertEqual(result["change_returned"]["company_currency_total"], 20)

    def test_refund_beyond_this_shift_change_still_leaves_the_drawer(self):
        invoice = _invoice(grand_total=100, change_amount=20, payments=[_cash_row(120)])
        entry = _payment_entry("PE-PAY-2", "Pay", 50, unallocated_amount=50)

        result = self._overview([invoice], [entry])

        self.assertEqual(self._cash_total(result), 70)
        self.assertEqual(
            result["change_returned"]["overpayment_change"]["company_currency_total"],
            30,
        )

    def test_multi_mode_sale_nets_change_from_the_cash_row_only(self):
        invoice = _invoice(
            grand_total=100,
            change_amount=20,
            payments=[_cash_row(120), _cash_row(50, mode="Telebirr")],
        )

        result = self._overview([invoice], [])

        by_mode = {row["mode_of_payment"]: row["company_currency_total"] for row in result["payments_by_mode"]}
        self.assertEqual(by_mode["Cash"], 100)
        self.assertEqual(by_mode["Telebirr"], 50)

    def test_change_is_netted_out_of_a_non_cash_sale(self):
        invoice = _invoice(
            grand_total=100,
            change_amount=20,
            payments=[_cash_row(10), _cash_row(110, mode="Card")],
        )

        result = self._overview([invoice], [])

        by_mode = {row["mode_of_payment"]: row["company_currency_total"] for row in result["payments_by_mode"]}
        self.assertEqual(by_mode["Cash"], 10)
        self.assertEqual(by_mode["Card"], 90)
        self.assertEqual(self._cash_total(result), 10)


class TestClosingShiftCreationReconciliation(unittest.TestCase):
    def _expected_amounts(self, invoices, payment_entries, opening=()):
        _install_stubs(invoices, payment_entries)
        frappe_module = sys.modules["frappe"]
        frappe_module.new_doc = lambda doctype: FakeDoc(
            {
                "doctype": doctype,
                "payment_reconciliation": [],
                "pos_transactions": [],
                "pos_payments": [],
                "taxes": [],
            },
        )
        frappe_module.utils = SimpleNamespace(get_datetime=lambda: "2026-01-01 18:00:00")
        frappe_module.get_value = lambda doctype, name, field: "Cash"

        module = _load_module(PACKAGE + ".creation", CREATION_PATH)
        opening_shift = AttrDict(
            {
                "name": "POS-OPEN-1",
                "pos_profile": "POS-PROFILE-1",
                "company": "My Co",
                "user": "cashier@example.com",
                "period_start_date": "2026-01-01 08:00:00",
                "balance_details": list(opening),
            },
        )

        result = module.make_closing_shift_from_opening(json.dumps(opening_shift))

        return {
            row.mode_of_payment: row.expected_amount
            for row in result["closing_shift"].get("payment_reconciliation")
        }

    def test_change_is_netted_out_of_the_first_cash_row(self):
        amounts = self._expected_amounts([_invoice(grand_total=100, change_amount=20, payments=[_cash_row(120)])], [])

        self.assertEqual(amounts["Cash"], 100)

    def test_advance_redemption_entry_is_not_counted_twice(self):
        invoice = _invoice(payments=[_cash_row(60)])
        entry = _payment_entry(
            "PE-RCV-1",
            "Receive",
            60,
            references=[_reference("PE-RCV-1", invoice["name"], 60)],
        )

        amounts = self._expected_amounts([invoice], [entry])

        self.assertEqual(amounts["Cash"], 60)

    def test_change_entry_does_not_reduce_the_drawer_twice(self):
        invoice = _invoice(grand_total=100, change_amount=20, payments=[_cash_row(120)])
        entry = _payment_entry(
            "PE-PAY-1",
            "Pay",
            20,
            unallocated_amount=20,
        )

        amounts = self._expected_amounts([invoice], [entry])

        self.assertEqual(amounts["Cash"], 100)

    def test_opening_balance_is_carried_into_the_expectation(self):
        amounts = self._expected_amounts(
            [_invoice(payments=[_cash_row(100)])],
            [],
            opening=[AttrDict({"mode_of_payment": "Cash", "amount": 50})],
        )

        self.assertEqual(amounts["Cash"], 150)


if __name__ == "__main__":
    unittest.main()

import importlib.util
import pathlib
import sys
import types
import unittest
from types import SimpleNamespace


REPO_ROOT = pathlib.Path(__file__).resolve().parents[5]
CLOSING_PROCESSING_PATH = pathlib.Path(__file__).resolve().parent
OVERVIEW_PATH = CLOSING_PROCESSING_PATH / "overview.py"
UTILS_PATH = CLOSING_PROCESSING_PATH / "utils.py"


class AttrDict(dict):
    __getattr__ = dict.get


def _install_stubs():
    frappe_module = types.ModuleType("frappe")
    frappe_utils_module = types.ModuleType("frappe.utils")
    closing_data_module = types.ModuleType(
        "ethiotel_pos.ethio_telecom_pos_app.doctype.pos_closing_shift.closing_processing.data"
    )

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
    frappe_module.db = SimpleNamespace(
        get_value=lambda doctype, name, field: (
            0
            if (doctype, name, field)
            == ("POS Profile", "POS-PROFILE-1", "create_pos_invoice_instead_of_sales_invoice")
            else "Cash"
        )
    )
    frappe_utils_module.flt = lambda value=0, precision=None: float(value or 0)
    frappe_utils_module.json = __import__("json")

    closing_data_module.get_payments_entries = lambda *args, **kwargs: []
    closing_data_module.get_pos_invoices = lambda *args, **kwargs: []
    closing_data_module.get_payment_entry_references = lambda *args, **kwargs: {}

    sys.modules["frappe"] = frappe_module
    sys.modules["frappe.utils"] = frappe_utils_module
    sys.modules[
        "ethiotel_pos.ethio_telecom_pos_app.doctype.pos_closing_shift.closing_processing.data"
    ] = closing_data_module

    # The real utils module is used so the payment netting helpers are exercised.
    utils_name = "ethiotel_pos.ethio_telecom_pos_app.doctype.pos_closing_shift.closing_processing.utils"
    utils_spec = importlib.util.spec_from_file_location(utils_name, UTILS_PATH)
    utils_module = importlib.util.module_from_spec(utils_spec)
    sys.modules[utils_name] = utils_module
    utils_spec.loader.exec_module(utils_module)


def _load_module():
    module_name = "ethiotel_pos.ethio_telecom_pos_app.doctype.pos_closing_shift.closing_processing.overview"
    spec = importlib.util.spec_from_file_location(module_name, OVERVIEW_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestClosingOverviewLoyalty(unittest.TestCase):
    def setUp(self):
        _install_stubs()
        self.module = _load_module()

    def test_loyalty_redemption_excludes_return_adjustments_from_redeemed_totals(self):
        self.module.get_pos_invoices = lambda *args, **kwargs: [
            AttrDict(
                {
                    "name": "SINV-0001",
                    "currency": "USD",
                    "conversion_rate": 1,
                    "grand_total": 100,
                    "rounded_total": 100,
                    "base_grand_total": 100,
                    "loyalty_amount": 10,
                    "base_loyalty_amount": 10,
                    "loyalty_points": 2,
                    "payments": [],
                }
            ),
            AttrDict(
                {
                    "name": "SINV-RET-0001",
                    "currency": "USD",
                    "conversion_rate": 1,
                    "is_return": 1,
                    "grand_total": -40,
                    "rounded_total": -40,
                    "base_grand_total": -40,
                    "loyalty_amount": -3,
                    "base_loyalty_amount": -3,
                    "loyalty_points": -1,
                    "payments": [],
                }
            ),
        ]

        result = self.module.get_closing_shift_overview("POS-OPEN-1")

        self.assertEqual(result["loyalty_redemption"]["company_currency_total"], 10)
        self.assertEqual(result["loyalty_redemption"]["points"], 2)
        self.assertEqual(result["loyalty_redemption"]["count"], 1)
        self.assertEqual(result["loyalty_redemption"]["by_currency"][0]["total"], 10)
        self.assertEqual(result["loyalty_redemption"]["by_currency"][0]["points"], 2)
        self.assertEqual(result["loyalty_redemption"]["by_currency"][0]["invoice_count"], 1)


if __name__ == "__main__":
    unittest.main()

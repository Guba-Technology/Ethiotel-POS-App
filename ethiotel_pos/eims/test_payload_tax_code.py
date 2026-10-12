import importlib.util
import pathlib
import sys
import types
import unittest
from types import SimpleNamespace


EIMS_PATH = pathlib.Path(__file__).resolve().parent
PAYLOAD_PATH = EIMS_PATH / "payload.py"

# Captured while the real frappe is still in sys.modules: the stub installed by
# _load_payload must be removed again so it cannot leak into other test modules.
_REAL_FRAPPE = sys.modules.get("frappe")
_REAL_FRAPPE_UTILS = sys.modules.get("frappe.utils")


class AttrDict:
    """Attribute access document stand-in.

    Keys live in ``__dict__`` rather than in a dict mapping so that document
    fields such as ``items`` do not collide with ``dict.items``.
    """

    def __init__(self, data=None, **kwargs):
        self.__dict__.update(data or {})
        self.__dict__.update(kwargs)
        # Records every tax recalculation so tests can assert that applying the
        # default actually re-totalled the invoice.
        self.recalc_count = 0

    def get(self, fieldname, default=None):
        return self.__dict__.get(fieldname, default)

    def __getitem__(self, fieldname):
        return self.__dict__[fieldname]

    def __setitem__(self, fieldname, value):
        setattr(self, fieldname, value)

    def set(self, fieldname, value):
        setattr(self, fieldname, value)

    def append(self, fieldname, row):
        self.__dict__.setdefault(fieldname, []).append(AttrDict(row))

    def calculate_taxes_and_totals(self):
        self.recalc_count += 1


def _line(item_code="ITEM-1", item_tax_rate="{}", **kwargs):
    """An invoice line with no tax of its own unless told otherwise."""
    return AttrDict(
        {
            "item_code": item_code,
            "item_tax_rate": item_tax_rate,
            "item_tax_template": "",
            "qty": 1,
            "rate": 100.0,
            "base_rate": 100.0,
            "net_amount": 100.0,
            "base_net_amount": 100.0,
            **kwargs,
        },
    )


def _invoice(name="ACC-SINV-2026-00106", is_consolidated=0, taxes_and_charges=None, **kwargs):
    return AttrDict(
        {
            "name": name,
            "doctype": "Sales Invoice",
            "customer": "Walk-In Customer",
            "company": "GT",
            "is_consolidated": is_consolidated,
            "taxes_and_charges": taxes_and_charges,
            "taxes": [],
            "discount_amount": 0,
            "is_return": 0,
            "is_debit_note": 0,
            "custom_transaction_type": "B2C",
            "items": [_line()],
            **kwargs,
        },
    )


def _default_accounts():
    """Account fixtures mirroring the ERP: docname -> account_name / type / rate."""
    return {
        "VAT0 - GT": {"account_name": "VAT0", "account_type": "Tax", "tax_rate": 0.0},
        "VAT15 - GT": {"account_name": "VAT15", "account_type": "Tax", "tax_rate": 15.0},
        "VATEX - GT": {"account_name": "VATEX", "account_type": "Tax", "tax_rate": 0.0},
        "WTHOT - GT": {"account_name": "WTHOT", "account_type": "Tax", "tax_rate": 3.0},
        # Legacy 16% account, deliberately left out of the default mapping.
        "VAT - GT": {"account_name": "VAT", "account_type": "Tax", "tax_rate": 16.0},
        "WTHOI - GT": {"account_name": "WTHOI", "account_type": "Tax", "tax_rate": 3.0},
        # Non-tax heads must be ignored by the account scan.
        "Cash - GT": {"account_name": "Cash", "account_type": "Asset", "tax_rate": 0.0},
    }


def _default_tax_rows():
    """Valid one-to-one mapping with exactly one Default row.

    The Default row names an Item Tax Template, which is how the default gets
    applied to untaxed invoice items.
    """
    return [
        {"account": "VAT0 - GT", "tax_code": "VAT0", "is_default": 0, "item_tax_template": ""},
        {"account": "VAT15 - GT", "tax_code": "VAT15", "is_default": 1,
         "item_tax_template": "Vat 15 template - GT"},
        {"account": "VATEX - GT", "tax_code": "VATEX", "is_default": 0, "item_tax_template": ""},
        {"account": "WTHOT - GT", "tax_code": "WTHOT", "is_default": 0, "item_tax_template": ""},
    ]


def _load_payload(merge_log_names=None, tax_rows=None, accounts=None):
    """Import payload.py with a stubbed frappe so the guard can be unit tested."""

    merge_log_names = merge_log_names or set()
    if tax_rows is None:
        tax_rows = _default_tax_rows()
    if accounts is None:
        accounts = _default_accounts()
    # Convenience: a Default row that does not mention a template is given the
    # matching one, so tests can declare only what they are asserting about.
    # Pass item_tax_template="" explicitly to test the missing-template error.
    tax_rows = [
        r if "item_tax_template" in r or int(r.get("is_default") or 0) != 1
        else {**r, "item_tax_template": "Vat 15 template - GT"}
        for r in tax_rows
    ]
    frappe = types.ModuleType("frappe")

    class ValidationError(Exception):
        pass

    def _throw(msg, *args, **kwargs):
        raise ValidationError(msg)

    def _exists(doctype, filters=None):
        if doctype != "POS Invoice Merge Log" or not isinstance(filters, dict):
            return None
        for field in ("consolidated_invoice", "consolidated_credit_note"):
            if filters.get(field) and filters[field] in merge_log_names:
                return "POS-INV-MERGE-LOG-1"
        return None

    def _get_value(doctype, name, fieldname, *args, **kwargs):
        if isinstance(fieldname, (list, tuple)):
            values = [accounts.get(name, {}).get(f) for f in fieldname]
            return values if any(v is not None for v in values) else None
        if doctype == "Account":
            return accounts.get(name, {}).get(fieldname)
        return None

    frappe.ValidationError = ValidationError
    frappe.throw = _throw
    frappe._ = lambda text: text
    frappe.utils = types.ModuleType("frappe.utils")
    frappe.utils.get_datetime = None
    frappe.utils.now_datetime = None
    frappe.db = SimpleNamespace(exists=_exists, get_value=_get_value)
    settings = AttrDict({"tax_code_config": [AttrDict(r) for r in tax_rows]})
    frappe.get_doc = lambda *args, **kwargs: settings
    frappe.get_cached_doc = lambda *args, **kwargs: settings
    frappe.get_meta = lambda *args, **kwargs: SimpleNamespace(has_field=lambda fieldname: False)

    package = types.ModuleType("ethiotel_pos.eims")
    package.__path__ = [str(EIMS_PATH)]
    constants = types.ModuleType("ethiotel_pos.eims.constants")
    constants.ID_TYPE_ALIASES = {}
    constants.ID_TYPES = []
    constants.MOR_PAYMENT_MODES = []
    constants.VALID_UNITS = []
    constants.WALK_IN_CUSTOMER = "Walk-In Customer"

    sys.modules["frappe"] = frappe
    sys.modules["frappe.utils"] = frappe.utils
    sys.modules["ethiotel_pos.eims"] = package
    sys.modules["ethiotel_pos.eims.constants"] = constants

    spec = importlib.util.spec_from_file_location("ethiotel_pos.eims.payload", PAYLOAD_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["ethiotel_pos.eims.payload"] = module
    spec.loader.exec_module(module)
    return module


class TestEIMSConsolidatedInvoiceSkip(unittest.TestCase):
    def tearDown(self):
        # Undo the module-level stubbing done by _load_payload.
        sys.modules["frappe"] = _REAL_FRAPPE
        sys.modules["frappe.utils"] = _REAL_FRAPPE_UTILS
        sys.modules.pop("ethiotel_pos.eims.payload", None)
        sys.modules.pop("ethiotel_pos.eims.constants", None)

    def test_merge_log_invoice_is_recognised_as_consolidated(self):
        payload = _load_payload(merge_log_names={"ACC-SINV-2026-00106"})

        self.assertTrue(payload._is_consolidated(_invoice(is_consolidated=0)))
        self.assertTrue(payload._is_consolidated(_invoice(is_consolidated=1)))

    def test_consolidated_credit_note_is_recognised(self):
        payload = _load_payload(merge_log_names={"ACC-SINV-2026-00106"})

        self.assertTrue(payload._is_consolidated(_invoice(is_consolidated=0)))

    def test_ordinary_sales_invoice_is_not_treated_as_consolidated(self):
        payload = _load_payload()

        self.assertFalse(payload._is_consolidated(_invoice(is_consolidated=0)))
        self.assertFalse(payload._is_consolidated(_invoice(name="new-sales-invoice")))

    def test_pos_invoice_is_never_consolidated(self):
        payload = _load_payload()

        pos_invoice = _invoice()
        pos_invoice.set("doctype", "POS Invoice")
        pos_invoice.set("is_consolidated", 1)

        self.assertFalse(payload._is_consolidated(pos_invoice))

    def test_shift_close_consolidated_invoice_skips_the_tax_code_check(self):
        """ERPNext builds the consolidated SI with an 'Actual' tax row but no
        taxes_and_charges template, so header resolution finds no EIMS code.
        Shift close must still go through, and the row resolves through the
        configured Default tax code."""

        payload = _load_payload(merge_log_names={"ACC-SINV-2026-00106"})
        doc = _invoice(is_consolidated=0)
        doc["taxes"] = [AttrDict({"charge_type": "Actual", "account_head": "VAT15 - GT", "rate": 0, "tax_amount": 13})]

        # This shape resolves no code of its own, so it relies on the Default.
        self.assertTrue(payload._invoice_has_tax_code(doc))

        payload.validate_invoice_for_eims(doc)

    def test_ordinary_invoice_without_any_tax_code_uses_the_default(self):
        """With a Default configured, a tax-less invoice is filled from it
        rather than rejected. The Default row is the whole point of the flag."""
        payload = _load_payload()
        doc = _invoice(is_consolidated=0)

        self.assertTrue(payload._invoice_has_tax_code(doc))
        payload.validate_invoice_for_eims(doc)

    def test_tax_less_invoice_is_rejected_when_no_default_exists(self):
        payload = _load_payload(tax_rows=[])
        doc = _invoice(is_consolidated=0)

        self.assertFalse(payload._invoice_has_tax_code(doc))
        with self.assertRaises(payload.frappe.ValidationError):
            payload.validate_invoice_for_eims(doc)

    def test_ordinary_invoice_with_a_tax_template_passes(self):
        payload = _load_payload()
        doc = _invoice(is_consolidated=0, taxes_and_charges="Ethiopia Tax POS - GT")
        doc["taxes"] = [AttrDict({"charge_type": "On Net Total", "account_head": "VAT15 - GT", "rate": 15, "tax_amount": 15})]

        payload.validate_invoice_for_eims(doc)


class TestTaxCodeConfigMappingIsOneToOne(unittest.TestCase):
    """Each tax account maps to exactly one EIMS tax code, and each code to
    exactly one account. Nothing may be hardcoded: every code sent to MoR must
    come from EIMS Setting > Account Config."""

    def tearDown(self):
        sys.modules["frappe"] = _REAL_FRAPPE
        sys.modules["frappe.utils"] = _REAL_FRAPPE_UTILS
        sys.modules.pop("ethiotel_pos.eims.payload", None)
        sys.modules.pop("ethiotel_pos.eims.constants", None)

    def _invoice_with(self, accounts, items=None):
        doc = _invoice(
            is_consolidated=0,
            taxes_and_charges="Ethiopia Tax POS - GT",
            items=items or [AttrDict({"item_code": "ITEM-1", "item_tax_rate": "{}", "qty": 1})],
        )
        doc["taxes"] = [
            AttrDict({"charge_type": "On Net Total", "account_head": a, "rate": 15,
                      "tax_amount": 15})
            for a in accounts
        ]
        return doc

    def test_codes_come_from_the_mapping_not_the_account_name(self):
        payload = _load_payload()
        # Accounts deliberately named differently from their configured code.
        rows = [{"account": "VAT15 - GT", "tax_code": "TOT2", "is_default": 1}]
        payload = _load_payload(tax_rows=rows)

        self.assertEqual(payload._tax_code_for("VAT15 - GT"), "TOT2")
        self.assertEqual(payload._tax_code_for("VAT15"), "TOT2")

    def test_lookup_accepts_both_docname_and_account_name(self):
        payload = _load_payload()

        self.assertEqual(payload._tax_code_for("VAT15 - GT"), "VAT15")
        self.assertEqual(payload._tax_code_for("VAT15"), "VAT15")

    def test_unmapped_account_is_rejected_before_save(self):
        payload = _load_payload(tax_rows=[
            {"account": "VAT15 - GT", "tax_code": "VAT15", "is_default": 1},
        ])
        doc = self._invoice_with(["VATEX - GT"])

        with self.assertRaises(payload.frappe.ValidationError) as ctx:
            payload.validate_invoice_for_eims(doc)
        self.assertIn("VATEX - GT", str(ctx.exception))

    def test_item_level_unmapped_account_is_rejected(self):
        payload = _load_payload(tax_rows=[
            {"account": "VAT15 - GT", "tax_code": "VAT15", "is_default": 1},
        ])
        doc = self._invoice_with(
            ["VAT15 - GT"],
            items=[AttrDict({"item_code": "ITEM-1", "item_tax_rate": '{"WTHOI - GT": 3.0}',
                             "qty": 1})],
        )

        with self.assertRaises(payload.frappe.ValidationError) as ctx:
            payload.validate_invoice_for_eims(doc)
        self.assertIn("WTHOI - GT", str(ctx.exception))

    def test_non_tax_account_head_is_ignored(self):
        payload = _load_payload()
        doc = self._invoice_with(["VAT15 - GT", "Cash - GT"])

        self.assertEqual(payload._invoice_tax_accounts(doc), ["VAT15 - GT"])
        payload.validate_invoice_for_eims(doc)

    def test_two_accounts_claiming_one_code_is_rejected(self):
        rows = [
            {"account": "VAT15 - GT", "tax_code": "VAT15", "is_default": 1},
            {"account": "VAT - GT", "tax_code": "VAT15", "is_default": 0},
        ]
        payload = _load_payload(tax_rows=rows)
        doc = self._invoice_with(["VAT15 - GT", "VAT - GT"])

        with self.assertRaises(payload.frappe.ValidationError) as ctx:
            payload.validate_invoice_for_eims(doc)
        self.assertIn("more than one tax account", str(ctx.exception))

    def test_one_account_claiming_two_codes_is_rejected(self):
        rows = [
            {"account": "VAT15 - GT", "tax_code": "VAT15", "is_default": 1},
            {"account": "VAT15 - GT", "tax_code": "VATEX", "is_default": 0},
        ]
        payload = _load_payload(tax_rows=rows)
        doc = self._invoice_with(["VAT15 - GT"])

        with self.assertRaises(payload.frappe.ValidationError) as ctx:
            payload.validate_invoice_for_eims(doc)
        self.assertIn("Conflicting EIMS tax codes", str(ctx.exception))

    def test_repeated_identical_row_is_rejected(self):
        rows = [
            {"account": "VAT15 - GT", "tax_code": "VAT15", "is_default": 1},
            {"account": "VAT15 - GT", "tax_code": "VAT15", "is_default": 0},
        ]
        payload = _load_payload(tax_rows=rows)
        doc = self._invoice_with(["VAT15 - GT"])

        with self.assertRaises(payload.frappe.ValidationError) as ctx:
            payload.validate_invoice_for_eims(doc)
        self.assertIn("Duplicate rows", str(ctx.exception))

    def test_strict_resolution_refuses_to_emit_a_raw_account_name(self):
        payload = _load_payload(tax_rows=[
            {"account": "VAT15 - GT", "tax_code": "VAT15", "is_default": 1},
        ])
        item = AttrDict({"item_code": "ITEM-1", "item_tax_rate": '{"VATEX - GT": 0.0}', "qty": 1})

        with self.assertRaises(payload.frappe.ValidationError):
            payload.resolve_item_tax_rate(item, "VAT15", 15.0, strict=True)


class TestExactlyOneDefaultTaxCode(unittest.TestCase):
    """Exactly one row must carry the Default flag: it is the fallback for an
    invoice line that resolves no code of its own."""

    def tearDown(self):
        sys.modules["frappe"] = _REAL_FRAPPE
        sys.modules["frappe.utils"] = _REAL_FRAPPE_UTILS
        sys.modules.pop("ethiotel_pos.eims.payload", None)
        sys.modules.pop("ethiotel_pos.eims.constants", None)

    def _mapped_invoice(self):
        doc = _invoice(
            is_consolidated=0,
            taxes_and_charges="Ethiopia Tax POS - GT",
        )
        doc["taxes"] = [AttrDict({"charge_type": "On Net Total",
                                  "account_head": "VAT15 - GT", "rate": 15,
                                  "tax_amount": 15})]
        return doc

    def test_no_default_is_rejected(self):
        rows = [dict(r, is_default=0) for r in _default_tax_rows()]
        payload = _load_payload(tax_rows=rows)

        self.assertIsNone(payload._default_tax_row())
        with self.assertRaises(payload.frappe.ValidationError) as ctx:
            payload.validate_invoice_for_eims(self._mapped_invoice())
        self.assertIn("No <b>Default</b> tax code", str(ctx.exception))

    def test_two_defaults_are_rejected(self):
        rows = [
            {"account": "VAT15 - GT", "tax_code": "VAT15", "is_default": 1},
            {"account": "VATEX - GT", "tax_code": "VATEX", "is_default": 1},
        ]
        payload = _load_payload(tax_rows=rows)

        self.assertIsNone(payload._default_tax_row())
        with self.assertRaises(payload.frappe.ValidationError) as ctx:
            payload.validate_invoice_for_eims(self._mapped_invoice())
        self.assertIn("More than one row is marked", str(ctx.exception))

    def test_empty_mapping_table_is_rejected(self):
        payload = _load_payload(tax_rows=[])

        with self.assertRaises(payload.frappe.ValidationError) as ctx:
            payload.validate_invoice_for_eims(self._mapped_invoice())
        self.assertIn("No EIMS tax codes are configured", str(ctx.exception))

    def test_exactly_one_default_is_accepted(self):
        payload = _load_payload()

        row = payload._default_tax_row()
        self.assertEqual(row.account, "VAT15 - GT")
        self.assertEqual(row.tax_code, "VAT15")
        payload.validate_invoice_for_eims(self._mapped_invoice())

    def test_default_supplies_the_code_for_a_line_with_none(self):
        payload = _load_payload()
        item = AttrDict({"item_tax_rate": "{}"})

        # Code from the default row, rate from that row's own Account.tax_rate.
        self.assertEqual(
            payload.resolve_item_tax_rate(item, "", 0, strict=True),
            ("VAT15", 15.0),
        )

    def test_default_does_not_override_an_explicit_account_code(self):
        payload = _load_payload()
        item = AttrDict({"item_tax_rate": '{"VATEX - GT": 0.0}'})

        self.assertEqual(
            payload.resolve_item_tax_rate(item, "", 0, strict=True),
            ("VATEX", 0.0),
        )


class TestWithholdingIsAnAmountNotARate(unittest.TestCase):
    """ValueDetails.TransactionWithholdValue must be a monetary amount.

    It used to read the tax RATE, so a 3% withholding was registered as
    "3.0" instead of the real amount (e.g. 2,254.04). MoR then has no way to
    reconcile the invoice, and the withheld portion shows as an outstanding
    balance that no receipt can ever settle.
    """

    def _withholding_invoice(self):
        doc = _invoice(
            is_consolidated=0,
            custom_transaction_type="B2B",
        )
        doc["items"] = [
            AttrDict({"item_code": "ITEM-1", "item_tax_rate": "{}", "qty": 1,
                      "net_amount": 75134.55, "base_net_amount": 75134.55})
        ]
        doc["taxes"] = [
            AttrDict({
                "charge_type": "On Net Total",
                "account_head": "VAT15 - GT",
                "rate": 15.0,
                "tax_amount": 11270.18,
                "tax_amount_after_discount_amount": 11270.18,
            }),
            AttrDict({
                "charge_type": "On Net Total",
                "account_head": "WTHOT - GT",
                "rate": -3.0,
                "tax_amount": -2372.67,
                # ERPNext folds the AFTER-discount amount into grand_total
                "tax_amount_after_discount_amount": -2254.04,
            }),
        ]
        return doc

    def _payload(self):
        payload = _load_payload()
        payload.frappe.db.get_value = lambda doctype, name, field: (
            {"is_stock_item": 1}.get(field) if doctype == "Item" else None
        )
        return payload

    def test_withholding_returns_the_amount_not_the_percentage(self):
        payload = self._payload()
        doc = self._withholding_invoice()

        transaction_wht, income_wht = payload.sum_withholding(doc, "B2B")

        self.assertAlmostEqual(transaction_wht, 2254.04, places=2)
        self.assertEqual(income_wht, 0.0)
        self.assertNotEqual(
            transaction_wht, 3.0,
            "TransactionWithholdValue must not be the tax rate",
        )

    def test_prefers_the_after_discount_amount_that_feeds_grand_total(self):
        payload = self._payload()
        doc = self._withholding_invoice()

        transaction_wht, _ = payload.sum_withholding(doc, "B2B")

        # 75,134.55 net + 11,270.18 VAT - 2,254.04 WHT == 84,150.69 grand total,
        # so the after-discount figure is the one that reconciles.
        self.assertAlmostEqual(
            75134.55 + 11270.18 - transaction_wht, 84150.69, places=2
        )

    def test_withholding_is_still_ignored_for_non_b2b(self):
        payload = self._payload()
        doc = self._withholding_invoice()

        self.assertEqual(payload.sum_withholding(doc, "B2C"), (0.0, 0.0))


class TestDefaultTaxCodeIsAppliedToUntaxedItems(unittest.TestCase):
    """The Default row exists to give its tax account to invoice items that
    carry no tax code of their own. It must be applied to the Sales Invoice
    itself (so ERPNext posts the tax and the total moves), not only substituted
    into the MoR payload."""

    def tearDown(self):
        sys.modules["frappe"] = _REAL_FRAPPE
        sys.modules["frappe.utils"] = _REAL_FRAPPE_UTILS
        sys.modules.pop("ethiotel_pos.eims.payload", None)
        sys.modules.pop("ethiotel_pos.eims.constants", None)

    def test_untaxed_item_receives_the_default_template_and_recalculates(self):
        payload = _load_payload()
        doc = _invoice(is_consolidated=0)

        applied = payload.apply_default_item_tax_template(doc)

        self.assertEqual(applied, ["ITEM-1"])
        self.assertEqual(doc.items[0].item_tax_template, "Vat 15 template - GT")
        self.assertEqual(doc.recalc_count, 1, "totals must be recalculated")

    def test_missing_tax_row_is_appended_for_the_default_account(self):
        payload = _load_payload()
        doc = _invoice(is_consolidated=0)

        payload.apply_default_item_tax_template(doc)

        self.assertEqual(len(doc.taxes), 1)
        row = doc.taxes[0]
        self.assertEqual(row.account_head, "VAT15 - GT")
        self.assertEqual(row.charge_type, "On Net Total")
        # Rate is 0 on purpose: ERPNext reads the real rate from each item's
        # tax map and only falls back to the row rate when the account is
        # absent from that map. Seeding 15% would tax the exempt lines too.
        self.assertEqual(row.rate, 0.0)
        self.assertEqual(row.set_by_item_tax_template, 1)

    def test_existing_tax_row_is_reused_rather_than_duplicated(self):
        payload = _load_payload()
        doc = _invoice(is_consolidated=0, taxes_and_charges="Ethiopia Tax - GT")
        doc["taxes"] = [
            AttrDict({"charge_type": "On Net Total", "account_head": "VAT15 - GT", "rate": 15.0})
        ]

        payload.apply_default_item_tax_template(doc)

        self.assertEqual([t.account_head for t in doc.taxes], ["VAT15 - GT"])

    def test_inclusive_flag_is_inherited_from_the_existing_rows(self):
        payload = _load_payload()
        doc = _invoice(is_consolidated=0)
        doc["taxes"] = [
            AttrDict({"charge_type": "On Net Total", "account_head": "Cash - GT",
                      "included_in_print_rate": 1})
        ]

        payload.apply_default_item_tax_template(doc)

        appended = [t for t in doc.taxes if t.account_head == "VAT15 - GT"][0]
        self.assertEqual(appended.included_in_print_rate, 1)

    def test_item_with_its_own_template_is_left_alone(self):
        payload = _load_payload()
        doc = _invoice(is_consolidated=0, items=[
            _line(item_tax_rate='{"VATEX - GT": 0.0}', item_tax_template="Excise Tax Template - GT"),
        ])

        applied = payload.apply_default_item_tax_template(doc)

        self.assertEqual(applied, [])
        self.assertEqual(doc.items[0].item_tax_template, "Excise Tax Template - GT")
        self.assertEqual(doc.recalc_count, 0)

    def test_line_is_judged_on_its_template_not_its_stale_rate_map(self):
        """ERPNext rebuilds item_tax_rate from item_tax_template on every
        recalculation, so the stored map is derived data. A line whose template
        was cleared but whose old map had not been recalculated yet must still
        be treated as untaxed, otherwise it silently escapes the default."""
        payload = _load_payload()
        doc = _invoice(is_consolidated=0, items=[
            _line(item_tax_rate='{"VATEX - GT": 0.0}', item_tax_template=""),
        ])

        applied = payload.apply_default_item_tax_template(doc)

        self.assertEqual(applied, ["ITEM-1"])
        self.assertEqual(doc.items[0].item_tax_template, "Vat 15 template - GT")

    def test_only_the_untaxed_lines_are_touched(self):
        payload = _load_payload()
        doc = _invoice(is_consolidated=0, items=[
            _line("PEN", item_tax_template="vat0 template - GT"),
            _line("PHONE"),
            _line("SERVICE", item_tax_rate=""),
            _line("NO-ITEM-GROUP", item_tax_rate="not-json"),
        ])

        applied = payload.apply_default_item_tax_template(doc)

        self.assertEqual(applied, ["PHONE", "SERVICE", "NO-ITEM-GROUP"])
        self.assertEqual(doc.items[0].item_tax_template, "vat0 template - GT")
        for idx in (1, 2, 3):
            self.assertEqual(doc.items[idx].item_tax_template, "Vat 15 template - GT")

    def test_second_save_is_idempotent(self):
        payload = _load_payload()
        doc = _invoice(is_consolidated=0)

        payload.apply_default_item_tax_template(doc)
        after_first = doc.recalc_count
        tax_rows_after_first = len(doc.taxes)

        applied = payload.apply_default_item_tax_template(doc)

        self.assertEqual(applied, [])
        self.assertEqual(doc.recalc_count, after_first, "no work, no recalculation")
        self.assertEqual(len(doc.taxes), tax_rows_after_first)

    def test_default_row_without_a_template_is_rejected(self):
        payload = _load_payload(tax_rows=[
            {"account": "VAT15 - GT", "tax_code": "VAT15", "is_default": 1,
             "item_tax_template": ""},
        ])
        doc = _invoice(is_consolidated=0)

        with self.assertRaises(payload.frappe.ValidationError) as ctx:
            payload.apply_default_item_tax_template(doc)
        self.assertIn("Item Tax Template", str(ctx.exception))

    def test_pos_invoice_is_not_touched(self):
        """POS invoices get their taxes from the POS profile/template; this
        feature is scoped to Sales Invoice."""
        payload = _load_payload()
        doc = _invoice(is_consolidated=0)
        doc["doctype"] = "POS Invoice"

        applied = payload.apply_default_item_tax_template(doc)

        self.assertEqual(applied, [])
        self.assertEqual(doc.items[0].item_tax_template, "")
        self.assertEqual(doc.recalc_count, 0)

    def test_invoice_without_items_is_a_no_op(self):
        payload = _load_payload()
        doc = _invoice(is_consolidated=0, items=[])

        self.assertEqual(payload.apply_default_item_tax_template(doc), [])

    def test_validate_applies_the_default_and_then_accepts_the_invoice(self):
        """End-to-end through the save-time guard: an invoice whose only line
        has no tax at all used to be rejected for a missing TaxCode. Now the
        default tax account is applied first, so it saves."""
        payload = _load_payload()
        doc = _invoice(is_consolidated=0)

        payload.validate_invoice_for_eims(doc)

        self.assertEqual(doc.items[0].item_tax_template, "Vat 15 template - GT")
        self.assertEqual([t.account_head for t in doc.taxes], ["VAT15 - GT"])


if __name__ == "__main__":
    unittest.main()

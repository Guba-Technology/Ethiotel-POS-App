import unittest
from unittest.mock import patch

import frappe

from ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos import (
    _normalize_opening_balances,
    get_opening_payment_modes,
)


class TestOpeningBalanceNormalisation(unittest.TestCase):
    def setUp(self):
        # Mock the profile to return a stable, predictable list of modes.
        self.profile_modes = ["Cash", "Telebirr", "CBE Birr"]
        self.get_modes_patcher = patch.object(
            __import__("ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos", fromlist=["get_opening_payment_modes"]),
            "get_opening_payment_modes",
            return_value=self.profile_modes,
        )
        self.get_modes_patcher.start()

    def tearDown(self):
        self.get_modes_patcher.stop()

    def test_opening_amount_is_kept(self):
        rows = _normalize_opening_balances(
            "dummy_profile", [{"mode_of_payment": "Cash", "opening_amount": 1000}]
        )

        # All profile modes present, submitted one wins
        self.assertEqual(
            rows,
            [
                {"mode_of_payment": "Cash", "opening_amount": 1000.0},
                {"mode_of_payment": "Telebirr", "opening_amount": 0.0},
                {"mode_of_payment": "CBE Birr", "opening_amount": 0.0},
            ],
        )

    def test_amount_alias_is_accepted(self):
        """The shift's own naming must still record the float, not drop it to zero."""

        rows = _normalize_opening_balances(
            "dummy_profile", [{"mode_of_payment": "Cash", "amount": 1000}]
        )

        self.assertEqual(
            rows,
            [
                {"mode_of_payment": "Cash", "opening_amount": 1000.0},
                {"mode_of_payment": "Telebirr", "opening_amount": 0.0},
                {"mode_of_payment": "CBE Birr", "opening_amount": 0.0},
            ],
        )

    def test_opening_amount_wins_over_amount(self):
        rows = _normalize_opening_balances(
            "dummy_profile", [{"mode_of_payment": "Cash", "opening_amount": 1000, "amount": 7}]
        )

        self.assertEqual(rows[0]["opening_amount"], 1000.0)

    def test_rows_without_a_mode_are_dropped(self):
        rows = _normalize_opening_balances(
            "dummy_profile",
            [
                {"mode_of_payment": "", "opening_amount": 1000},
                {"mode_of_payment": "  ", "opening_amount": 1000},
                {"opening_amount": 1000},
                "not-a-row",
                None,
                {"mode_of_payment": "Cash", "opening_amount": 1000},
            ],
        )

        # Only the valid row + the other profile modes zeroed
        self.assertEqual(
            rows,
            [
                {"mode_of_payment": "Cash", "opening_amount": 1000.0},
                {"mode_of_payment": "Telebirr", "opening_amount": 0.0},
                {"mode_of_payment": "CBE Birr", "opening_amount": 0.0},
            ],
        )

    def test_extra_client_keys_are_not_persisted(self):
        rows = _normalize_opening_balances(
            "dummy_profile", [{"mode_of_payment": "Cash", "opening_amount": 1000, "idx": 3, "__islocal": 1}]
        )

        self.assertEqual(sorted(rows[0].keys()), ["mode_of_payment", "opening_amount"])

    def test_mode_is_trimmed(self):
        rows = _normalize_opening_balances(
            "dummy_profile", [{"mode_of_payment": "  Cash  ", "opening_amount": 5}]
        )

        self.assertEqual(rows[0]["mode_of_payment"], "Cash")

    def test_non_numeric_amount_becomes_zero_not_a_crash(self):
        rows = _normalize_opening_balances(
            "dummy_profile",
            [{"mode_of_payment": "Cash", "opening_amount": "abc"}, {"mode_of_payment": "Cheque", "opening_amount": 5}],
        )

        # Cheque is not in profile modes, so it's appended after profile modes
        cash_row = next(r for r in rows if r["mode_of_payment"] == "Cash")
        cheque_row = next(r for r in rows if r["mode_of_payment"] == "Cheque")
        self.assertEqual(cash_row["opening_amount"], 0.0)
        self.assertEqual(cheque_row["opening_amount"], 5.0)

    def test_all_profile_modes_are_present_even_when_not_submitted(self):
        """Every MoR-valid mode on the profile gets a row, zero if not sent."""

        rows = _normalize_opening_balances("dummy_profile", [])

        self.assertEqual(
            [r["mode_of_payment"] for r in rows],
            ["Cash", "Telebirr", "CBE Birr"],
        )
        self.assertTrue(all(r["opening_amount"] == 0.0 for r in rows))

    def test_no_rows_is_rejected_when_profile_has_no_modes(self):
        with patch("ethiotel_pos.ethio_telecom_pos_app.page.ethiotel_pos.ethiotel_pos.get_opening_payment_modes", return_value=[]):
            with self.assertRaises(frappe.ValidationError):
                _normalize_opening_balances("empty_profile", [])

    def test_extra_mode_not_on_profile_is_appended(self):
        rows = _normalize_opening_balances(
            "dummy_profile", [{"mode_of_payment": "OtherMode", "opening_amount": 100}]
        )

        modes = [r["mode_of_payment"] for r in rows]
        self.assertEqual(modes[:3], ["Cash", "Telebirr", "CBE Birr"])
        self.assertIn("OtherMode", modes)


if __name__ == "__main__":
    unittest.main()

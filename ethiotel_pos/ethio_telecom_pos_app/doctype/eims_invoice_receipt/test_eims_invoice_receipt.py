# Copyright (c) 2026, Guba Technology and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from types import SimpleNamespace

from ethiotel_pos.ethio_telecom_pos_app.doctype.eims_invoice_receipt.eims_invoice_receipt import (
	_cumulative_paid_amount,
	_invoice_payload_row,
	_next_receipt_number,
)


class TestEIMSInvoiceReceipt(FrappeTestCase):
	"""Several receipts against one partially paid Sales Invoice."""

	def setUp(self):
		self.invoice = self._pick_invoice()
		if not self.invoice:
			self.skipTest("No submitted Sales Invoice available on this site")
		self.addCleanup(self._cleanup_receipts)

	# reference numbering

	def test_base_number_used_when_free(self):
		self.assertEqual(_next_receipt_number("RCP-000-NONE", None), "RCP-000-NONE")

	def test_second_receipt_gets_a_suffix(self):
		base = f"RCP-TST-{frappe.generate_hash(length=6)}"
		first = _next_receipt_number(base, None)
		self.assertEqual(first, base)

		self._make_receipt(base_number=base, paid=100.0, coverage="PARTIAL")
		self.assertEqual(_next_receipt_number(base, None), f"{base}-1")

	def test_third_receipt_skips_a_used_suffix(self):
		base = f"RCP-TST-{frappe.generate_hash(length=6)}"
		self._make_receipt(base_number=base, paid=100.0, coverage="PARTIAL")
		self._make_receipt(base_number=f"{base}-1", paid=100.0, coverage="PARTIAL")
		self.assertEqual(_next_receipt_number(base, None), f"{base}-2")

	# cumulative collection

	def test_running_total_starts_with_this_payment(self):
		self.assertEqual(_cumulative_paid_amount(self.invoice, None, 300.0), 300.0)

	def test_refreshing_the_same_receipt_does_not_double_count(self):
		receipt = self._make_receipt(paid=100.0, coverage="PARTIAL")
		self.assertEqual(
			_cumulative_paid_amount(self.invoice, receipt.name, 100.0), 100.0
		)

	def test_a_second_receipt_adds_to_the_first(self):
		self._make_receipt(paid=250.0, coverage="PARTIAL")
		self.assertEqual(_cumulative_paid_amount(self.invoice, None, 400.0), 650.0)

	def test_three_partials_accumulate(self):
		self._make_receipt(paid=250.0, coverage="PARTIAL")
		self._make_receipt(paid=250.0, coverage="PARTIAL")
		self.assertEqual(_cumulative_paid_amount(self.invoice, None, 500.0), 1000.0)

	def test_a_full_receipt_settles_the_whole_total(self):
		self._make_receipt(paid=1000.0, coverage="FULL", total=1000.0)
		# A FULL receipt wins over any smaller rows.
		self.assertEqual(_cumulative_paid_amount(self.invoice, None, 0.0), 1000.0)

	def test_failed_receipts_never_count(self):
		self._make_receipt(paid=100.0, coverage="PARTIAL", status="Failed")
		self.assertEqual(_cumulative_paid_amount(self.invoice, None, 200.0), 200.0)

	def test_cancelled_receipts_never_count(self):
		receipt = self._make_receipt(paid=100.0, coverage="PARTIAL")
		self.assertEqual(_cumulative_paid_amount(self.invoice, None, 200.0), 300.0)

		receipt.submit()
		receipt.cancel()
		self.assertEqual(_cumulative_paid_amount(self.invoice, None, 200.0), 200.0)

	# MoR payload arithmetic
	#
	# MoR treats each receipt independently: InvoicePaidAmount is the amount
	# THIS payment entry collected, never a running total, and CollectedAmount
	# must equal it. PaymentCoverage is FULL only for the first receipt of an
	# IRN, and only when it discharges the invoice.

	def test_interim_receipt_declares_the_individual_amount(self):
		# Second instalment: this receipt collected 450 of 1000, so PARTIAL.
		# The 250 from the earlier receipt must NOT be summed in.
		receipt = self._make_receipt(paid=450.0, coverage="PARTIAL", total=1000.0)
		self._make_receipt(paid=250.0, coverage="PARTIAL", total=1000.0)
		row = receipt.invoices_covered[0]
		row.invoice_paid_amount = 450.0
		row.receipt_paid_amount = 450.0
		row.mor_collected_amount = 450.0
		row.remaining_amount = 550.0

		payload = _invoice_payload_row(row)

		self.assertEqual(payload["InvoicePaidAmount"], 450.0)
		self.assertEqual(payload["PaymentCoverage"], "PARTIAL")
		self.assertEqual(payload["RemainingAmount"], 550.0)
		self.assertEqual(payload["TotalAmount"], 1000.0)

	def test_later_receipt_uses_the_individual_amount_not_the_running_total(self):
		# The closing receipt of an instalment sequence must declare what THIS
		# payment entry collected (40,000), not the cumulative 84,150.70.
		# Summing is what earned the 406.
		registered = 86404.7325
		withheld = 2254.04
		prior = 44150.7
		cash = 40000.0
		paid_to_date = prior + cash
		remaining = max(registered - cash, 0.0)

		row = self._receipt_row(registered, withheld, paid_to_date, cash,
								mor_collected=cash, remaining=remaining)
		payload = _invoice_payload_row(row)

		self.assertEqual(payload["PaymentCoverage"], "PARTIAL")
		self.assertEqual(payload["InvoicePaidAmount"], 40000.0)
		self.assertAlmostEqual(payload["RemainingAmount"], 46404.7325, places=4)
		self.assertEqual(payload["TotalAmount"], 86404.7325)
		self.assertEqual(row.receipt_paid_amount, 40000.0)

	def test_first_receipt_of_withheld_invoice_carries_the_withholding(self):
		# RCP-233 was accepted with InvoicePaidAmount 86,404.7325 = the 84,150.70
		# the customer paid plus the 2,254.04 withheld tax, so a single payment
		# settles the invoice.
		registered = 86404.7325
		withheld = 2254.04
		row = self._receipt_row(registered, withheld, registered, 84150.6925,
								mor_collected=registered, remaining=0.0)
		payload = _invoice_payload_row(row)

		self.assertEqual(payload["InvoicePaidAmount"], 86404.7325)
		self.assertEqual(payload["TotalAmount"], 86404.7325)
		self.assertEqual(payload["RemainingAmount"], 0.0)
		self.assertEqual(payload["PaymentCoverage"], "FULL")
		self.assertAlmostEqual(row.receipt_paid_amount, 84150.6925, places=4)

	def test_first_receipt_without_withholding_declares_the_cash(self):
		registered = 1000.0
		row = self._receipt_row(registered, 0.0, 1000.0, 1000.0, remaining=0.0)
		payload = _invoice_payload_row(row)

		self.assertEqual(payload["InvoicePaidAmount"], 1000.0)
		self.assertEqual(payload["PaymentCoverage"], "FULL")

	def test_payload_amounts_are_always_numbers(self):
		receipt = self._make_receipt(paid=100.0, coverage="PARTIAL", total=1000.0)
		for field in ("receipt_paid_amount", "mor_collected_amount", "invoice_paid_amount",
					  "discount_amount", "remaining_amount", "total_amount"):
			setattr(receipt.invoices_covered[0], field, None)

		row = _invoice_payload_row(receipt.invoices_covered[0])

		for key in ("InvoicePaidAmount", "DiscountAmount", "RemainingAmount", "TotalAmount"):
			self.assertIsInstance(row[key], float, f"{key} must be a float, not null")

	def test_payload_preserves_registered_total_without_rounding(self):
		receipt = self._make_receipt(paid=25000.0, coverage="PARTIAL", total=86404.7325)
		receipt.invoices_covered[0].receipt_paid_amount = 25000.0
		receipt.invoices_covered[0].mor_collected_amount = 86404.7325
		receipt.invoices_covered[0].remaining_amount = 0.0

		row = _invoice_payload_row(receipt.invoices_covered[0])

		self.assertEqual(row["TotalAmount"], 86404.7325)
		self.assertEqual(row["InvoicePaidAmount"], 86404.7325)
		self.assertEqual(row["RemainingAmount"], 0.0)

	# withheld tax
	#
	# Withheld tax is deducted by the buyer and remitted to the tax authority,
	# so it is never payable to the seller. The reference row therefore carries
	# the business view alongside the MoR (registered-basis) view.

	def _receipt_row(self, registered, withheld, paid_to_date, receipt_paid,
					 mor_collected=None, remaining=None):
		"""A reference row as `fetch_payment_entry_details` builds it."""
		collectible = max(registered - withheld, 0.0)
		collectible_remaining = max(collectible - paid_to_date, 0.0)
		if remaining is None:
			remaining = max(registered - paid_to_date, 0.0)
		return SimpleNamespace(
			invoice_irn="test-abc",
			payment_coverage="FULL" if remaining <= 0 else "PARTIAL",
			invoice_paid_amount=paid_to_date,
			receipt_paid_amount=receipt_paid,
			mor_collected_amount=receipt_paid if mor_collected is None else mor_collected,
			discount_amount=4428.98,
			remaining_amount=remaining,
			total_amount=registered,
			taxable_amount=75134.55,
			withheld_amount=withheld,
			collectible_amount=collectible,
			collectible_remaining_amount=collectible_remaining,
			collectible_coverage="FULL" if collectible_remaining <= 0 else "PARTIAL",
		)

	def test_midway_receipt_declares_cumulative_paid_and_stays_partial(self):
		registered = 86404.7325
		withheld = 2254.04
		row = self._receipt_row(registered, withheld, 59150.7, 45000.0,
								mor_collected=59150.7,
								remaining=max(registered - 59150.7, 0.0))
		payload = _invoice_payload_row(row)

		self.assertEqual(payload["PaymentCoverage"], "PARTIAL")
		self.assertEqual(payload["InvoicePaidAmount"], 59150.7)
		self.assertAlmostEqual(payload["RemainingAmount"], 27254.0325, places=4)

	def test_collectible_amount_excludes_withheld_tax(self):
		row = self._withholding_row(registered=86404.7325, withheld=2254.04, paid_to_date=84150.7)

		self.assertAlmostEqual(row.collectible_amount, 84150.6925, places=2)
		self.assertAlmostEqual(row.withheld_amount, 2254.04, places=2)
		self.assertAlmostEqual(row.collectible_remaining_amount, 0.0, places=2)
		self.assertEqual(row.collectible_coverage, "FULL")

	def test_mor_remaining_still_uses_the_registered_basis(self):
		# `remaining_amount` is the invoice balance after this receipt, on the
		# registered basis, and `payment_coverage` stays on that basis too.
		row = self._withholding_row(
			registered=86404.7325, withheld=2254.04, paid_to_date=84150.7, receipt_paid=25000.0
		)

		self.assertAlmostEqual(row.remaining_amount, 2254.0325, places=2)
		self.assertEqual(row.payment_coverage, "PARTIAL")
		payload = _invoice_payload_row(row)
		# Per-receipt amount, not the running total: this is what keeps
		# CollectedAmount and InvoicePaidAmount in agreement.
		self.assertEqual(payload["InvoicePaidAmount"], 25000.0)
		self.assertAlmostEqual(payload["RemainingAmount"], 2254.0325, places=4)
		self.assertEqual(payload["TotalAmount"], 86404.7325)

	def test_collectible_stays_partial_while_money_is_outstanding(self):
		row = self._withholding_row(registered=86404.7325, withheld=2254.04, paid_to_date=59150.7)

		self.assertAlmostEqual(row.collectible_remaining_amount, 24999.9925, places=2)
		self.assertEqual(row.collectible_coverage, "PARTIAL")

	# helpers

	def _withholding_row(self, registered, withheld, paid_to_date, receipt_paid=None):
		collectible = registered - withheld
		remaining = max(registered - paid_to_date, 0.0)
		collectible_remaining = max(collectible - paid_to_date, 0.0)
		return SimpleNamespace(
			invoice_irn="test-abc",
			payment_coverage="FULL" if remaining <= 0 else "PARTIAL",
			# running total across all receipts...
			invoice_paid_amount=paid_to_date,
			# ...vs what this one receipt collected
			receipt_paid_amount=paid_to_date if receipt_paid is None else receipt_paid,
			discount_amount=4428.98,
			remaining_amount=remaining,
			total_amount=registered,
			withheld_amount=withheld,
			collectible_amount=collectible,
			collectible_remaining_amount=collectible_remaining,
			collectible_coverage="FULL" if collectible_remaining <= 0 else "PARTIAL",
		)
	def _pick_invoice(self):
		"""A submitted Sales Invoice that has no receipts yet, so the
		cumulative total starts from a known zero."""
		return frappe.db.sql(
			"""
			SELECT si.name
			FROM `tabSales Invoice` si
			LEFT JOIN `tabEIMS Invoice Receipt Reference` ref
				ON ref.sales_invoice = si.name
			WHERE si.docstatus = 1 AND ref.name IS NULL
			ORDER BY si.creation DESC
			LIMIT 1
			""",
		)[0][0]

	def _make_receipt(
		self, paid, coverage, total=1000.0, status="Active", base_number=None
	):
		base_number = base_number or f"RCP-TST-{frappe.generate_hash(length=8)}"
		receipt = frappe.get_doc(
			{
				"doctype": "EIMS Invoice Receipt",
				"receipt_number": base_number,
				"receipt_type": "Sales Receipts",
				"mode_of_payment": "CASH",
				"collected_amount": paid,
				"eims_status": status,
				"invoices_covered": [
					{
						"sales_invoice": self.invoice,
						"invoice_irn": frappe.db.get_value(
							"Sales Invoice", self.invoice, "custom_irn"
						),
						"payment_coverage": coverage,
						"invoice_paid_amount": paid,
						"remaining_amount": max(total - paid, 0.0),
						"total_amount": total,
					}
				],
			}
		).insert(ignore_permissions=True)
		return receipt

	def _cleanup_receipts(self):
		parents = frappe.get_all(
			"EIMS Invoice Receipt Reference",
			filters={"sales_invoice": self.invoice},
			pluck="parent",
		)
		only_ours = [
			p
			for p in parents
			if (frappe.db.get_value("EIMS Invoice Receipt", p, "receipt_number") or "")
			.startswith("RCP-TST-")
		]
		for parent in only_ours:
			frappe.delete_doc("EIMS Invoice Receipt", parent, ignore_permissions=True, force=True)
		frappe.db.commit()

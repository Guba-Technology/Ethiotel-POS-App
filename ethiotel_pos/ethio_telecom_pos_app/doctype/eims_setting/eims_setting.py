# Copyright (c) 2026, Guba Technology and contributors
# For license information, please see license.txt

import frappe

from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from ethiotel_pos.eims.audit import log_audit


class EIMSSetting(Document):
	def validate(self):
		self._enforce_single_default_client()
		self._validate_tax_code_config()

	def _validate_tax_code_config(self):
		"""The Account <-> Tax Code mapping must be strictly one-to-one.

		Saving a mapping with a blank cell, one account carrying two codes, or
		one code claimed by two accounts makes the TaxCode sent to MoR
		ambiguous or empty, so reject it at the configuration screen instead of
		at invoice save / registration.
		"""
		account_codes = {}
		code_accounts = {}
		for row in self.tax_code_config:
			account = (row.account or "").strip()
			code = (row.tax_code or "").strip()
			if not account:
				frappe.throw(
					_("Row {0}: <b>Account</b> is required in the Account Config table.").format(
						row.idx
					),
					title=_("EIMS Tax Code Mapping Error"),
				)
			if not code:
				frappe.throw(
					_(
						"Row {0} (<b>{1}</b>): <b>Tax Code</b> is required. Every tax account must be mapped to an EIMS tax code."
					).format(row.idx, account),
					title=_("EIMS Tax Code Mapping Error"),
				)

			# One tax code must belong to exactly one tax account. A repeated
			# account+code pair is rejected too: the extra row is redundant and
			# would make the mapping ambiguous when read back.
			owner = code_accounts.get(code)
			if owner:
				if owner == account:
					frappe.throw(
						_(
							"Row {0}: <b>{1}</b> is already mapped to <b>{2}</b>. Each tax account must appear exactly once in the Account Config table."
						).format(row.idx, account, code),
						title=_("EIMS Tax Code Mapping Error"),
					)
				frappe.throw(
					_(
						"<b>Tax Code {0}</b> is mapped to two different tax accounts: <b>{1}</b> and <b>{2}</b>. Each tax code must belong to exactly one account."
					).format(code, owner, account),
					title=_("EIMS Tax Code Mapping Error"),
				)
			code_accounts[code] = account

			# One tax account must carry exactly one tax code. Both the Account
			# document name and its account_name are checked so two rows that
			# point at the same account cannot slip through.
			account_name = (frappe.db.get_value("Account", account, "account_name") or "").strip()
			for alias in {account, account_name} - {""}:
				existing = account_codes.get(alias)
				if existing and existing != code:
					frappe.throw(
						_(
							"<b>{0}</b> is mapped to two different tax codes: <b>{1}</b> and <b>{2}</b>. Keep exactly one row per tax account."
						).format(alias, existing, code),
						title=_("EIMS Tax Code Mapping Error"),
					)
				account_codes[alias] = code

		# Exactly one row must be flagged as the default tax code: it is the
		# fallback when an invoice line carries no resolvable tax code, so
		# having none leaves the payload ambiguous while having several makes
		# the fallback non-deterministic.
		defaults = [row for row in self.tax_code_config if int(row.is_default or 0) == 1]
		if not self.tax_code_config:
			return
		if len(defaults) == 0:
			frappe.throw(
				_(
					"You must mark exactly one row as <b>Default</b> in the Account Config table. The default tax code is used when an invoice line has no tax code of its own."
				),
				title=_("EIMS Tax Code Mapping Error"),
			)
		if len(defaults) > 1:
			frappe.throw(
				_("Only one row can be marked as <b>Default</b> in the Account Config table."),
				title=_("EIMS Tax Code Mapping Error"),
			)

		self._validate_default_item_tax_template(defaults[0])

	def _validate_default_item_tax_template(self, default_row):
		"""The Default row is applied to invoice items that carry no tax of
		their own, and it is applied through an Item Tax Template so ERPNext
		posts the tax and recalculates the invoice total.

		Three things must line up, otherwise the invoice total and the tax
		amount sent to MoR would disagree:
		  - the template exists and is enabled for the same company,
		  - it taxes exactly the Default row's account,
		  - its rate matches that Account's own tax_rate.
		"""
		template_name = (default_row.item_tax_template or "").strip()
		account = (default_row.account or "").strip()
		if not template_name:
			frappe.throw(
				_(
					"Row {0} (<b>{1}</b>) is the <b>Default</b> row, so it needs an <b>Item Tax Template</b>. It is what gets applied to invoice items that carry no tax code of their own."
				).format(default_row.idx, account),
				title=_("EIMS Tax Code Mapping Error"),
			)

		template = frappe.get_cached_doc("Item Tax Template", template_name)
		if template.disabled:
			frappe.throw(
				_("Item Tax Template <b>{0}</b> is disabled.").format(template_name),
				title=_("EIMS Tax Code Mapping Error"),
			)

		company = frappe.db.get_value("Account", account, "company")
		if template.company != company:
			frappe.throw(
				_(
					"Item Tax Template <b>{0}</b> belongs to <b>{1}</b> but the Default tax account <b>{2}</b> belongs to <b>{3}</b>."
				).format(template_name, template.company, account, company),
				title=_("EIMS Tax Code Mapping Error"),
			)

		template_rates = {
			row.tax_type: flt(row.tax_rate) for row in (template.taxes or []) if row.tax_type
		}
		if account not in template_rates:
			frappe.throw(
				_(
					"Item Tax Template <b>{0}</b> does not tax account <b>{1}</b>. The Default row's template must tax the same account that the row maps, otherwise the invoice would post one tax account while MoR is told about another."
				).format(template_name, account),
				title=_("EIMS Tax Code Mapping Error"),
			)

		account_rate = flt(frappe.db.get_value("Account", account, "tax_rate"))
		if template_rates[account] != account_rate:
			frappe.throw(
				_(
					"Item Tax Template <b>{0}</b> rates account <b>{1}</b> at <b>{2}</b>%, but the Account itself is <b>{3}</b>%. ERPNext posts the template rate while MoR is sent the Account rate, so these must match."
				).format(template_name, account, template_rates[account], account_rate),
				title=_("EIMS Tax Code Mapping Error"),
			)

	def _enforce_single_default_client(self):
		"""Server-side guarantee that exactly one Client Data row is default,
		that default_system_number mirrors it, and that the parent
		last_document_number follows the active System Number's own counter
		(each System Number keeps an independent MoR document sequence)."""
		defaults = [row for row in self.client_data_list if row.is_default == 1]
		if len(defaults) == 0:
			frappe.throw("You must mark exactly one row as default in the Client Data List.")
		if len(defaults) > 1:
			frappe.throw("Only one row can be marked as default.")
		active = defaults[0]

		self.default_system_number = active.system_number

		old_default = frappe.db.sql(
			"""SELECT name FROM `tabClient Data`
			WHERE parent = %s AND parentfield = %s AND is_default = 1""",
			(self.name, "client_data_list"),
		)
		was_already_default = bool(old_default and old_default[0][0] == active.name)

		active_last = active.last_document_number
		if active_last:
			# The active System Number has its own tracked counter: use it.
			self.last_document_number = active_last
		elif was_already_default and (self.last_document_number or 0) > 0:
			# Same default as before but never backfilled: adopt the parent's
			# current counter as this System Number's counter (one-time migration).
			active.last_document_number = self.last_document_number
		else:
			# Switching to a fresh/untracked System Number: restart at 1.
			self.last_document_number = 0
			active.last_document_number = 0

	def on_update(self):
		# Compliance trail: who changed credentials / endpoints / toggles and when.
		log_audit(
			"Configuration Change",
			success=True,
			description=f"EIMS Setting updated by {self.modified_by or frappe.session.user}",
		)


@frappe.whitelist()
def item_tax_templates_for_account(account):
	"""Enabled Item Tax Templates that tax `account` at the Account's own rate.

	Used by the Account Config grid to pre-fill the Default row's template.
	Only exact matches are returned: a template that taxes a different account,
	sits in another company, or disagrees on the rate would be rejected by
	_validate_default_item_tax_template() on save.
	"""
	account_rate = flt(frappe.db.get_value("Account", account, "tax_rate"))
	company = frappe.db.get_value("Account", account, "company")

	matching = []
	for name in frappe.get_all("Item Tax Template", filters={"disabled": 0}, pluck="name"):
		template = frappe.get_cached_doc("Item Tax Template", name)
		if template.company != company:
			continue
		rate = next(
			(flt(row.tax_rate) for row in (template.taxes or []) if row.tax_type == account),
			None,
		)
		if rate == account_rate:
			matching.append(name)
	return {"templates": matching}


@frappe.whitelist()
def send_test_sms(phone, message=None):
	"""Send a test SMS to verify the AfroMessage configuration from the
	EIMS Setting form. Requires sms_enabled + tokened/from settings.
	Only users who can write EIMS Setting may trigger a test SMS to
	avoid it being abused to burn SMS credits."""
	if not frappe.has_permission("EIMS Setting", "write"):
		frappe.throw("Insufficient permission to send a test SMS.")
	from ethiotel_pos.notify import send_sms

	return send_sms(
		phone,
		message or "Test from Ethio Telecom POS - SMS notifications are working.",
	)
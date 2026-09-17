# Copyright (c) 2026, Guba Technology and contributors
# For license information, please see license.txt

import frappe

from frappe.model.document import Document

from ethiotel_pos.eims.audit import log_audit


class EIMSSetting(Document):
	def validate(self):
		self._enforce_single_default_client()

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
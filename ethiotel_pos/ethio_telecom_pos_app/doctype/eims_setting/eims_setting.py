# Copyright (c) 2026, Guba Technology and contributors
# For license information, please see license.txt

import frappe

from frappe.model.document import Document

from ethiotel_pos.eims.audit import log_audit


class EIMSSetting(Document):
	def on_update(self):
		# Compliance trail: who changed credentials / endpoints / toggles and when.
		log_audit(
			"Configuration Change",
			success=True,
			description=f"EIMS Setting updated by {self.modified_by or frappe.session.user}",
		)
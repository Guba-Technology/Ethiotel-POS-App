# Copyright (c) 2026, Guba Technology

from frappe.www.login import get_context as frappe_login_get_context

import frappe

no_cache = True


def get_context(context):
	# Already logged in? Skip the login page and go straight to the app.
	if frappe.session.user != "Guest":
		redirect_to = frappe.local.request.args.get("redirect-to") if frappe.local.request else None
		if redirect_to and redirect_to != "login":
			frappe.local.flags.redirect_location = redirect_to
		else:
			frappe.local.flags.redirect_location = (
				"/app" if frappe.session.data.user_type == "System User" else "/"
			)
		raise frappe.Redirect

	# Build the normal Frappe login context (signup form, providers, settings...)
	frappe_login_get_context(context)

	context["app_name"] = "Ethiotel POS"
	context["title"] = "Log in - Ethiotel POS"

	
	context["logo"] = "/assets/ethiotel_pos/images/tele.jpg"

	context["page_tagline"] = (
		"Sales, purchases, inventory, and VAT-ready invoicing - all in one place."
	)

	return context
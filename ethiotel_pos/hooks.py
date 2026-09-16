from erpnext.accounts import doctype


app_name = "ethiotel_pos"
app_title = "Ethio Telecom POS App"
app_publisher = "Guba Technology"
app_description = "A POS application for front selling by ethio telecom"
app_email = "kelemu3509@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []
required_apps = ["erpnext"]

fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "name",
                "in",
                (
                    "POS Invoice-posa_pos_opening_shift",
                    "POS Profile-posa_pos_awesome_settings",
                    "POS Profile-posa_section_pricing_controls",
                    "POS Profile-posa_section_sales_returns",
                    "POS Profile-posa_section_sales_purchase",
                    "POS Profile-posa_section_inventory_controls",
                    "POS Profile-posa_section_print_delivery",
                    "POS Profile-posa_section_cash_movement",
                    "POS Profile-posa_allow_delete",
                    "POS Profile-posa_allow_user_to_edit_rate",
                    "POS Profile-posa_allow_user_to_edit_additional_discount",
                    "POS Profile-posa_allow_user_to_edit_item_discount",
                    "POS Profile-posa_display_items_in_stock",
                    "POS Profile-posa_allow_submissions_in_background_job",
                    "POS Profile-posa_allow_partial_payment",
                    "POS Profile-posa_allow_credit_sale",
                    "POS Profile-posa_pos_awesome_advance_settings",
                    "Batch-posa_batch_price",
                    "POS Profile-posa_max_discount_allowed",
                    "POS Profile-posa_allow_return",
                    "POS Profile-posa_allow_return_without_invoice",
                    "POS Profile-posa_allow_free_batch_return",
                    "POS Profile-posa_col_1",
                    "POS Profile-create_pos_invoice_instead_of_sales_invoice",
                    "POS Invoice-posa_is_printed",
                    "Sales Invoice-posa_is_printed",
                    "Sales Invoice Reference-pos_invoice",
                    "POS Profile-posa_local_storage",
                    "POS Profile-posa_force_server_items",
                    "POS Profile-posa_cash_mode_of_payment",
                    "POS Profile-use_customer_credit",
                    "POS Profile-posa_use_gift_cards",
                    "POS Profile-posa_allow_supervisor_manage_gift_cards",
                    "Sales Invoice-gift_card_redemptions",
                    "POS Invoice-gift_card_redemptions",
                    "POS Profile-use_cashback",
                    "POS Profile-posa_hide_closing_shift",
                    "Customer-posa_discount",
                    "POS Profile-posa_apply_customer_discount",
                    "Sales Invoice-posa_offers",
                    "POS Invoice-posa_offers",
                    "Sales Invoice-posa_coupons",
                    "POS Invoice-posa_coupons",
                    "Sales Invoice Item-posa_offers",
                    "POS Invoice Item-posa_offers",
                    "Sales Invoice Item-posa_row_id",
                    "POS Invoice Item-posa_row_id",
                    "Sales Invoice Item-posa_offer_applied",
                    "POS Invoice Item-posa_offer_applied",
                    "Sales Invoice Item-posa_is_offer",
                    "POS Invoice Item-posa_is_offer",
                    "Sales Invoice Item-posa_is_replace",
                    "POS Invoice Item-posa_is_replace",
                    "POS Profile-posa_auto_set_batch",
                    "POS Profile-posa_search_serial_no",
                    "Sales Invoice-posa_additional_notes_section",
                    "POS Invoice-posa_additional_notes_section",
                    "Sales Invoice-posa_notes",
                    "Sales Invoice-posa_authorization_code",
                    "POS Invoice-posa_notes",
                    "POS Invoice-posa_authorization_code",
                    "Sales Invoice-posa_column_break_111",
                    "POS Invoice-posa_column_break_111",
                    "Sales Invoice-posa_delivery_date",
                    "POS Invoice-posa_delivery_date",
                    "Sales Invoice Item-posa_notes",
                    "POS Invoice Item-posa_notes",
                    "Sales Invoice Item-posa_delivery_date",
                    "POS Invoice Item-posa_delivery_date",
                    "Sales Order-posa_additional_notes_section",
                    "Sales Order-posa_notes",
                    "Sales Order Item-posa_notes",
                    "POS Profile-posa_allow_sales_order",
                    "POS Profile-custom_allow_select_sales_order",
                    "POS Profile-posa_create_only_sales_order",
                    "POS Profile-posa_column_break_112",
                    "POS Profile-posa_show_template_items",
                    "POS Profile-posa_hide_variants_items",
                    "Customer-posa_referral_code",
                    "POS Profile-posa_fetch_coupon",
                    "Company-posa_referral_section",
                    "Company-posa_auto_referral",
                    "Company-posa_column_break_22",
                    "Company-posa_customer_offer",
                    "Company-posa_primary_offer",
                    "Company-posa_referral_campaign",
                    "Customer-posa_referral_company",
                    "Customer-posa_referral_section",
                    "Customer-posa_birthday",
                    "Sales Order-posa_offers",
                    "Sales Order-posa_coupons",
                    "Sales Order Item-posa_row_id",
                    "POS Profile-posa_tax_inclusive",
                    "POS Profile-posa_use_percentage_discount",
                    "POS Profile-posa_allow_customer_purchase_order",
                    "POS Profile-posa_allow_purchase_order",
                    "POS Profile-posa_allow_purchase_receipt",
                    "POS Profile-posa_allow_create_purchase_items",
                    "POS Profile-posa_allow_create_purchase_suppliers",
                    "POS Profile-posa_allow_print_last_invoice",
                    "POS Profile-posa_display_additional_notes",
                    "POS Profile-posa_display_authorization_code",
                    "POS Profile-posa_allow_write_off_change",
                    "POS Profile-posa_new_line",
                    "POS Profile-posa_input_qty",
                    "POS Profile-posa_display_item_code",
                    "POS Profile-posa_allow_zero_rated_items",
                    "POS Profile-posa_allow_print_draft_invoices",
                    "POS Profile-posa_allow_select_print_format_in_payments",
                    "Address-posa_delivery_charges",
                    "Sales Invoice-posa_delivery_charges",
                    "Sales Invoice-posa_delivery_charges_rate",
                    "POS Invoice-posa_delivery_charges",
                    "POS Invoice-posa_delivery_charges_rate",
                    "POS Profile-posa_auto_set_delivery_charges",
                    "POS Profile-posa_use_delivery_charges",
                    "POS Profile-hide_expected_amount",
                    "POS Profile-posa_display_discount_percentage",
                    "POS Profile-posa_display_discount_amount",
                    "POS Profile-posa_allow_change_posting_date",
                    "POS Profile-posa_default_card_view",
                    "POS Profile-posa_default_sales_order",
                    "POS Profile-column_break_dqsba",
                    "POS Profile-posa_use_server_cache",
                    "POS Profile-posa_server_cache_duration",
                    "POS Profile-posa_allow_duplicate_customer_names",
                    "POS Profile-column_break_anyol",
                    "POS Profile-pose_use_limit_search",
                    "POS Profile-posa_search_batch_no",
                    "POS Profile-pos_awesome_payments",
                    "POS Profile-posa_use_pos_awesome_payments",
                    "POS Profile-posa_allow_make_new_payments",
                    "POS Profile-posa_allow_reconcile_payments",
                    "POS Profile-column_break_uolvm",
                    "POS Profile-posa_allow_mpesa_reconcile_payments",
                    "POS Profile-posa_enable_print_audit",
                    "POS Profile-posa_default_printer_profile",
                    "POS Profile-posa_enable_camera_scanning",
                    "POS Profile-posa_camera_scan_type",
                    "POS Profile-posa_language",
                    "POS Profile-posa_enable_return_validity",
                    "POS Profile-posa_return_validity_days",
                    "POS Profile-posa_enable_cash_movement",
                    "POS Profile-posa_allow_pos_expense",
                    "POS Profile-posa_allow_cash_deposit",
                    "POS Profile-posa_default_expense_account",
                    "POS Profile-posa_allowed_expense_accounts",
                    "POS Profile-posa_default_source_account",
                    "POS Profile-posa_allow_source_account_override",
                    "POS Profile-posa_allowed_source_accounts",
                    "POS Profile-posa_back_office_cash_account",
                    "POS Profile-posa_allow_cancel_submitted_cash_movement",
                    "POS Profile-posa_allow_delete_cancelled_cash_movement",
                    "POS Profile-posa_require_cash_movement_remarks",
                    "POS Profile-posa_cash_movement_max_amount",
                    "POS Profile-posa_section_awesome_dashboard",
                    "POS Profile-posa_enable_awesome_dashboard",
                    "POS Profile-posa_allow_company_dashboard_scope",
                    "POS Profile-posa_low_stock_alert_threshold",
                    "POS Settings-posa_enable_return_validity",
                    "POS Settings-posa_return_validity_days",
                    "POS Settings-posa_section_dashboard",
                    "POS Settings-posa_enable_awesome_dashboard_global",
                    "POS Settings-posa_dashboard_default_scope",
                    "POS Settings-posa_dashboard_low_stock_alert_threshold",
                    "POS Invoice-posa_return_valid_upto",
                    "Sales Invoice-posa_return_valid_upto",
                    "User-posa_pos_pin",
                    "Mode of Payment-custom_mor_mode",
                    "POS Profile-posa_allow_multi_currency",
                    "POS Profile-posa_decimal_precision",
                    "Customer-eims_details_tab",
                    "Customer-eims_details_section",
                    "Customer-custom_eims_tin_number",
                    "Customer-custom_eims_legal_name",
                    "Customer-custom_eims_vat_number",
                    "Customer-custom_eims_region",
                    "Customer-custom_eims_zone",
                    "Customer-custom_eims_woreda",
                    "Customer-custom_eims_city",
                    "Customer-custom_eims_kebele",
                    "Customer-custom_eims_house_number",
                    "Customer-custom_eims_country",
                    "Customer-custom_eims_email",
                    "Customer-custom_eims_phone",
                    "Customer-custom_eims_id_type",
                    "Customer-custom_eims_id_number",
                    "Customer-custom_eims_sub_tin",
                    "Customer-custom_eims_trade_name",
                    "Customer-custom_eims_subcity",
                    "Customer-custom_eims_locality",
                    "Sales Invoice-custom_transaction_type",
                ),
            ]
        ],
    },
  
    {
        "doctype": "Property Setter",
        "filters": [
            [
                "name",
                "in",
                (
                    "POS Invoice-posa_pos_opening_shift-no_copy",
                    "Sales Invoice Reference-sales_invoice-reqd",
                    "Sales Invoice-update_outstanding_for_self-default",
                ),
            ]
        ],
    },
]
# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "ethiotel_pos",
# 		"logo": "/assets/ethiotel_pos/logo.png",
# 		"title": "Ethio Telecom POS App",
# 		"route": "/ethiotel_pos",
# 		"has_permission": "ethiotel_pos.api.permission.has_app_permission"
# 	}
# ]
doc_events = {
    "Sales Invoice": {
        "validate": "ethiotel_pos.api.invoice.validate",
        "before_submit": "ethiotel_pos.api.invoice.before_submit",
        "before_cancel": "ethiotel_pos.api.invoice.before_cancel",
        "on_cancel": "ethiotel_pos.api.invoice.on_cancel",
    },
    "POS Invoice": {
        "validate": "ethiotel_pos.api.invoice.validate",
        "before_submit": "ethiotel_pos.api.invoice.before_submit",
        "before_cancel": "ethiotel_pos.api.invoice.before_cancel",
        "on_cancel": "ethiotel_pos.api.invoice.on_cancel",
    },
    "Customer": {
        "validate": "ethiotel_pos.api.customer.validate",
        "after_insert": "ethiotel_pos.api.customer.after_insert",
    },
    # "Bin": {
    #     "after_insert": [
    #         "ethiotel_pos.ethiotel_pos.stock_realtime.publish_bin_stock_change",
    #         "ethiotel_pos.api.item_fetchers.clear_stock_caches",
    #     ],
    #     "on_update": [
    #         "ethiotel_pos.ethiotel_pos.stock_realtime.publish_bin_stock_change",
    #         "ethiotel_pos.api.item_fetchers.clear_stock_caches",
    #     ],
    # },
    "Stock Ledger Entry": {
        "after_insert": "ethiotel_pos.api.item_fetchers.clear_stock_caches",
        "on_cancel": "ethiotel_pos.api.item_fetchers.clear_stock_caches",
    },
    "Serial No": {
        "after_insert": "ethiotel_pos.api.item_fetchers.clear_stock_caches",
        "on_update": "ethiotel_pos.api.item_fetchers.clear_stock_caches",
    },
    "Batch": {
        "after_insert": "ethiotel_pos.api.item_fetchers.clear_stock_caches",
        "on_update": "ethiotel_pos.api.item_fetchers.clear_stock_caches",
    },
}
# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = [
    # "/assets/ethiotel_pos/css/ethiotel_branding.css",
    "/assets/ethiotel_pos/css/ethiotel_pos.css",
    
]
app_include_js = [
    "/assets/ethiotel_pos/js/ethiotel_pos.js",
    "/assets/ethiotel_pos/js/erp_pos.js",
    "/assets/ethiotel_pos/js/workspace_branding.js"
]

# Add or update the after_migrate hook
after_migrate = [
    "ethiotel_pos.workspace_setup.setup_tele_pos_workspace",
    "ethiotel_pos.prunning.run"
]
after_install = "ethiotel_pos.workspace_setup.setup_tele_pos_workspace"

override_doctype_class = {
    "Sales Invoice": "ethiotel_pos.overrides.sales_invoice.CustomSalesInvoice",
    "POS Invoice": "ethiotel_pos.overrides.pos_invoice.CustomPOSInvoice",

}
doctype_js = {
    "Sales Invoice": "public/js/sales_invoice.js",
    "Purchase Invoice": "public/js/purchase_invoice.js",
}
# include js, css files in header of web template
# web_include_css = "/assets/ethiotel_pos/css/ethiotel_pos.css"
# web_include_js = "/assets/ethiotel_pos/js/ethiotel_pos.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "ethiotel_pos/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# Override ERPNext brand assets (favicon / splash) — drop the logo files at
# apps/ethiotel_pos/ethiotel_pos/public/images/Ethiotel-logo.png
website_context = {
	"favicon": "/assets/ethiotel_pos/images/tele.jpg",
	"splash_image": "/assets/ethiotel_pos/images/tele.jpg",
}

# include js in page
# page_js = {"page" : "public/js/file.js"}
# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "ethiotel_pos/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
jinja = {
	"methods": [
		"ethiotel_pos.utils.get_invoice_qr_data_uri",
		"ethiotel_pos.utils.get_qr_img_tag",
	],
}

# Installation
# ------------

# before_install = "ethiotel_pos.install.before_install"
# after_install = "ethiotel_pos.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "ethiotel_pos.uninstall.before_uninstall"
# after_uninstall = "ethiotel_pos.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "ethiotel_pos.utils.before_app_install"
# after_app_install = "ethiotel_pos.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "ethiotel_pos.utils.before_app_uninstall"
# after_app_uninstall = "ethiotel_pos.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "ethiotel_pos.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
	"hourly": [
		"ethiotel_pos.tasks.retry_failed_eims_submissions",
	],
	"daily": [
		"ethiotel_pos.tasks.report_device_locations",
	],
}

# Testing
# -------

# before_tests = "ethiotel_pos.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "ethiotel_pos.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "ethiotel_pos.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["ethiotel_pos.utils.before_request"]
# after_request = ["ethiotel_pos.utils.after_request"]

# Job Events
# ----------
# before_job = ["ethiotel_pos.utils.before_job"]
# after_job = ["ethiotel_pos.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"ethiotel_pos.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []


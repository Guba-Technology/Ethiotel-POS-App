import json
import re


from frappe.utils import get_datetime, now_datetime

from .constants import (
    ID_TYPE_ALIASES,
    ID_TYPES,
    MOR_PAYMENT_MODES,
    VALID_UNITS,
    WALK_IN_CUSTOMER,
)

import frappe


def _is_consolidated(doc):
    """True for the Sales Invoice ERPNext builds when it consolidates POS Invoices
    at shift close.

    That document is a pure accounting artifact: the tax rows, customer data and
    EIMS registration all live on the original POS Invoices, and the consolidated
    copy is never registered with MoR. Validating it would fail shift close for
    reasons the cashier cannot act on.
    """
    if doc.doctype != "Sales Invoice":
        return False

    if getattr(doc, "is_consolidated", 0):
        return True

    name = getattr(doc, "name", None)
    if not name or name == "new-sales-invoice":
        return False

    if frappe.db.exists("POS Invoice Merge Log", {"consolidated_invoice": name}):
        return True

    return bool(frappe.db.exists("POS Invoice Merge Log", {"consolidated_credit_note": name}))


def _item_has_own_tax(item):
    """True when an invoice line already declares a tax of its own.

    Deliberately checks only item_tax_template, not item_tax_rate: ERPNext
    rebuilds item_tax_rate from the template on every recalculation, so the
    stored map is derived data. Trusting it would misread a line whose template
    was cleared but whose previous map had not been recalculated yet, and would
    charge the default VAT to an exempt supply.
    """
    return bool((item.get("item_tax_template") or "").strip())


def _has_tax_row(doc, account):
    return any((te.get("account_head") or "") == account for te in (doc.get("taxes") or []))


def apply_default_item_tax_template(doc):
    """Give the Default tax account to invoice lines that carry no tax at all.

    That is what the Default row on EIMS Setting is for: rather than only
    supplying a fallback tax code in the MoR payload while the invoice stays
    untaxed, the invoice itself receives the tax, so the posted total, the tax
    breakup and the payload all agree.

    It is applied through the Default row's Item Tax Template rather than by
    writing item_tax_rate directly, because update_item_tax_map() rebuilds
    item_tax_rate from item_tax_template on every recalculation and would
    discard a hand-written map.

    Returns the list of item_codes that were given the default, or an empty
    list when there was nothing to do (idempotent across repeated saves).
    """
    if doc.doctype != "Sales Invoice":
        return []
    if not (doc.get("items") or []):
        return []

    default_row = _require_default_tax_row()
    template = (default_row.get("item_tax_template") or "").strip()
    account = (default_row.get("account") or "").strip()
    if not template:
        frappe.throw(
            "The <b>Default</b> row in "
            '<a href="/app/eims-setting">EIMS Setting &rarr; Account Config</a> has no '
            "<b>Item Tax Template</b>, so it cannot be applied to invoice items that "
            "have no tax code. Set it to a template that taxes account "
            f"<b>{account}</b>.",
            title="EIMS Schema Error: Default Tax Code Has No Item Tax Template",
        )

    applied = []
    for item in doc.items:
        if _item_has_own_tax(item):
            continue
        item.item_tax_template = template
        applied.append(item.item_code)

    if not applied:
        return []

    # The template only drives the amount once a matching Taxes and Charges row
    # exists, so add it when the invoice was created without a tax template.
    if not _has_tax_row(doc, account):
        inclusive = any(
            int(te.get("included_in_print_rate") or 0) for te in (doc.get("taxes") or [])
        )
        doc.append(
            "taxes",
            {
                "charge_type": "On Net Total",
                "account_head": account,
                # Deliberately 0, mirroring ERPNext's own
                # append_taxes_from_item_tax_template(). _get_tax_rate() takes
                # the rate from each item's tax map when that account is present
                # and falls back to this row's rate when it is not. Seeding the
                # row with 15% would therefore also charge every zero-rated and
                # exempt line that does not list this account.
                "rate": 0.0,
                "description": account,
                "category": "Total",
                "add_deduct_tax": "Add",
                "included_in_print_rate": 1 if inclusive else 0,
                "set_by_item_tax_template": 1,
            },
        )

    doc.calculate_taxes_and_totals()
    return applied


def validate_invoice_for_eims(doc):
    """EIMS validations that run during Sales Invoice / POS Invoice validate
    (before save). Catches data errors early instead of at registration time."""
    settings = frappe.get_doc("EIMS Setting")
    if doc.doctype not in ("Sales Invoice", "POS Invoice"):
        return

    if _is_consolidated(doc):
        return

    is_walk_in = (doc.customer or "") == WALK_IN_CUSTOMER
    company_link = f"/app/company/{doc.company}" if doc.company else ""

    # --- TransactionType ---
    transaction_type = getattr(doc, "custom_transaction_type", "") or ""
    if not transaction_type:
        customer_type = frappe.db.get_value("Customer", doc.customer, "customer_type")
        t_map = {"Individual": "B2C", "Company": "B2B", "Government": "G2C", "Partnership": "B2B"}
        transaction_type = t_map.get(customer_type, "")
    if not transaction_type:
        if is_walk_in:
            transaction_type = "B2C"
        else:
            frappe.throw(
                "Please set the <b>Transaction Type</b> on this invoice.",
                title="EIMS Transaction Type Required",
            )

    # --- Customer Details must exist for non-walk-in ---
    if not is_walk_in:
        if not frappe.db.exists("Customer Details", doc.customer):
            frappe.throw(
                f"Please create a <b>Customer Details</b> document for "
                f"Customer <b>{doc.customer}</b> before saving.",
                title="EIMS Schema Validation Error",
            )

    # --- Customer data validations (non-walk-in only) ---
    cust_link = ""
    if not is_walk_in:
        cust_details = frappe.get_doc("Customer Details", doc.customer)
        cust_link = f"/app/customer-details/{cust_details.name}"

        # TIN: allow invoice-level override via `custom_buyer_tin`. The selected
        # raw value (invoice override if present, otherwise the stored
        # `Customer Details.tin_number`) is normalized and validated here so
        # invalid overrides are rejected early while preserving the existing
        # fallback behaviour.
        invoice_tin = getattr(doc, "custom_buyer_tin", "") or ""
        raw_tin = invoice_tin if invoice_tin else (cust_details.tin_number or "")
        clean_tin = re.sub(r"\D", "", str(raw_tin))

        # If an override was supplied on the invoice, reject it when invalid.
        if invoice_tin:
            if transaction_type not in ("B2C", "G2C"):
                if not clean_tin or len(clean_tin) < 10 or len(clean_tin) > 20:
                    frappe.throw(
                        f"<b>Invoice Buyer TIN</b> must be purely numeric and between 10 and 20 "
                        f"digits long. Found override: '{invoice_tin}'.",
                        title="EIMS Schema Error: Invalid Invoice Buyer TIN",
                    )
            elif clean_tin and (len(clean_tin) < 10 or len(clean_tin) > 20):
                frappe.throw(
                    f"<b>Invoice Buyer TIN</b> must be purely numeric and between 10 and 20 "
                    f"digits long. Found override: '{invoice_tin}'.",
                    title="EIMS Schema Error: Invalid Invoice Buyer TIN",
                )
        else:
            # No invoice override; validate the stored Customer Details TIN
            if transaction_type not in ("B2C", "G2C"):
                if not clean_tin or len(clean_tin) < 10 or len(clean_tin) > 20:
                    frappe.throw(
                        f"<b>TIN Number</b> must be purely numeric and between 10 and 20 "
                        f"digits long on <a href='{cust_link}'>{cust_details.name}</a>. "
                        f"Found: '{raw_tin}'.",
                        title="EIMS Schema Error: Invalid TIN",
                    )
            elif clean_tin and (len(clean_tin) < 10 or len(clean_tin) > 20):
                frappe.throw(
                    f"<b>TIN Number</b> must be purely numeric and between 10 and 20 "
                    f"digits long on <a href='{cust_link}'>{cust_details.name}</a>. "
                    f"Found: '{raw_tin}'.",
                    title="EIMS Schema Error: Invalid TIN",
                )

        # Email
        buyer_email = (cust_details.email or "").strip()
        if not buyer_email:
            buyer_email = (frappe.db.get_value("Customer", doc.customer, "custom_eims_email") or "").strip()
        if buyer_email and not re.match(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$", buyer_email):
            frappe.throw(
                f"<b>Email</b> is invalid on <a href='{cust_link}'>{cust_details.name}</a>. "
                f"Found: '{buyer_email}'.",
                title="EIMS Schema Error: Invalid Email",
            )

        # Region
        buyer_region = (cust_details.region or "").strip()
        if buyer_region and (not buyer_region.isdigit() or not (1 <= len(buyer_region) <= 3)):
            frappe.throw(
                f"<b>Region</b> must be a numeric code between 1 and 3 digits "
                f"on <a href='{cust_link}'>{cust_details.name}</a>. "
                f"Found: '{buyer_region}'.",
                title="EIMS Schema Error: Invalid Region Code",
            )
        elif not buyer_region:
            frappe.throw(
                f"<b>Region</b> is required for EIMS submission on "
                f"<a href='{cust_link}'>{cust_details.name}</a>.",
                title="EIMS Schema Error: Missing Region Code",
            )

    # --- CRE/DEB must reference a registered original invoice ---
    if getattr(doc, "is_return", 0) or getattr(doc, "is_debit_note", 0):
        note_type = "DEB" if getattr(doc, "is_debit_note", 0) else "CRE"
        original_name = doc.get("return_against") or ""
        if original_name:
            original_irn = (
                frappe.db.get_value("Sales Invoice", original_name, "custom_irn")
                or frappe.db.get_value("POS Invoice", original_name, "custom_irn")
            )
            if not original_irn:
                frappe.throw(
                    f"<b>{note_type}</b> notes must reference an EIRMS-registered original invoice. "
                    f"Set <b>Return Against</b> to an invoice with a populated <b>custom_irn</b>.",
                    title="EIMS Schema Error: Missing Original Invoice IRN",
                )
        else:
            frappe.throw(
                f"<b>{note_type}</b> notes require <b>Return Against</b> to be set.",
                title="EIMS Schema Error: Missing Return Against",
            )

    # --- Payment mode validation ---
    payment_entries = doc.get("payments") or []
    if payment_entries:
        payment_mode = payment_entries[0].mode_of_payment
        if payment_mode and not resolve_mor_payment_mode(payment_mode):
            frappe.throw(
                f"Unsupported <b>Mode of Payment</b>: '{payment_mode}'. "
                f"MoR accepts only: CASH, CHEQUE, CPO, Local Bank Transfer, SWIFT, "
                f"Wire Transfer, Letter of Credit, Card.",
                title="EIMS Payment Mode Error",
            )

    has_withholding = False
    for te in (doc.taxes or []):
        account = te.account_head
        if not account:
            continue
        if classify_withholding(account):
            has_withholding = True
            break
    if has_withholding and doc.doctype == "POS Invoice":
        frappe.throw(
            "Withholding tax accounts are present but this is a <b>POS Invoice</b>. "
            "POS invoices cannot carry withholding. Change the Tax Temmplate",
            title="EIMS Withholding Validation Error",
        )
    if has_withholding and doc.doctype != "POS Invoice" and not is_walk_in:
        if transaction_type not in ("B2B", "B2G"):
            frappe.throw(
                f"Withholding tax accounts are present but <b>Transaction Type</b> is "
                f"'{transaction_type}'. Withholding is only applicable for B2B or B2G.",
                title="EIMS Withholding Validation Error",
            )

        service_total = 0.0
        goods_total = 0.0
        for item in (doc.items or []):
            amount = abs(float(item.base_net_amount or item.net_amount or 0.0))
            if not amount:
                amount = abs(float(item.qty or 0.0)) * abs(float(item.base_rate or item.rate or 0.0))
            is_services = frappe.db.get_value("Item", item.item_code, "item_group") if item.item_code else None
            is_stock = True
            if is_services and is_services.lower() == "services":
                is_stock = False
            if is_stock:
                goods_total += amount
            else:
                service_total += amount
        min_withholding_goods_threshold = settings.min_with_am_goods or 20000
        min_withholding_service_threshold = settings.min_with_am_services or 10000
        if service_total <= min_withholding_service_threshold and goods_total <= min_withholding_goods_threshold:
            frappe.throw(
                "Withholding tax accounts are present but item totals do not meet the "
                "thresholds: goods must exceed <b>20,000</b> and services must exceed "
                "<b>10,000</b>. Current totals — Goods: {:,.2f}, Services: {:,.2f}.".format(
                    goods_total, service_total
                ),
                title="EIMS Withholding Threshold Error",
            )

    # --- Negative-value checks (available at validate time) ---
    # Credit notes (is_return) legitimately carry negative qty/amounts; skip.
    is_credit_note = bool(getattr(doc, "is_return", 0))
    if float(doc.discount_amount or 0) < 0:
        frappe.throw(
            "<b>Discount</b> cannot be negative for EIMS submission.",
            title="EIMS Schema Error: Negative Discount",
        )
    if not is_credit_note:
        for item in (doc.items or []):
            if float(item.qty or 0) < 0:
                frappe.throw(
                    f"<b>Quantity</b> for item <b>{item.item_code}</b> cannot be negative.",
                    title="EIMS Schema Error: Negative Quantity",
                )

    # --- CRE/DEB must mirror the original (TransactionType + ItemList order) ---
    # EIMS compares DEB/CRE lines positionally against the referenced document
    # (rule 7020) and requires the same TransactionType (rule 7030). Check at
    # save time so bad notes never even reach registration.
    note_type_here = "DEB" if getattr(doc, "is_debit_note", 0) else ("CRE" if getattr(doc, "is_return", 0) else "INV")
    if note_type_here in ("CRE", "DEB"):
        original_name = doc.get("return_against") or ""
        if original_name:
            snapshot = EIMSConnectorPayload()._note_reference_snapshot(original_name)
            if snapshot["transaction_type"] and transaction_type != snapshot["transaction_type"]:
                frappe.throw(
                    f"<b>{note_type_here}</b> notes must use the same <b>Transaction Type</b> "
                    f"as the original invoice ({original_name}). Note uses "
                    f"'{transaction_type}' but the original registered "
                    f"'{snapshot['transaction_type']}'.",
                    title="EIMS Schema Error: Note Transaction Type Mismatch",
                )
            if snapshot["item_lines"]:
                EIMSConnectorPayload()._align_note_items(
                    doc.items or [], snapshot["item_lines"], doc, note_type_here)

    # --- Give the Default tax account to lines that carry no tax of their own ---
    # Done before the mapping check below so the tax that was just applied is
    # validated as a normal mapped account, and before the per-line TaxCode
    # check so an untaxed line can no longer be the reason an invoice is
    # rejected.
    apply_default_item_tax_template(doc)

    # --- Every tax account must be mapped to an EIMS tax code ---
    # MoR only accepts registered tax codes, so an unmapped ERP account can
    # never be sent as TaxCode. Checked before save so the gap is reported in
    # the form instead of failing at registration.
    validate_tax_code_config(doc)

    # --- Every line must carry a TaxCode via the Taxes and Charges child ---
    # table. MoR rejects any line missing TaxCode/TaxAmount (schema 1028). The
    # Taxes and Charges table is the source: per-line item_tax_rate is a bonus
    # override. Runs at save time so the user is prompted before registration.
    if not _invoice_has_tax_code(doc):
        frappe.throw(
            f"<b>Tax Code required</b> for invoice <b>{doc.name}</b>.<br><br>"
            f"EIMS requires every line to carry a <b>TaxCode</b> and <b>TaxAmount</b>. Add a "
            f"tax row to the <b>Sales Taxes and Charges</b> table (e.g. <b>VAT15 - GT</b> for 15% "
            f"VAT, <b>VAT0 - GT</b> for zero-rated, or <b>VATEX - GT</b> for exempt supplies), set "
            f"an <b>Item Tax Template</b> on the items, or configure a <b>Default</b> EIMS tax code "
            f"under <b>EIMS Setting → Account Config</b>, then save again.",
            title="EIMS Schema Error: Missing Tax Code",
        )


def resolve_item_tax_rate(item_row, header_tax_code, header_tax_rate, strict=False):
    """Resolve the effective EIMS tax code + rate for one invoice line.

    Mirrors the logic used when building the registration payload so the
    same answer is produced at validate time (pre-save) and at submit time.
    item_tax_rate is a JSON map like {"VAT15 - GT": 15}; the code is still
    captured at 0% so VAT0 / VATEX lines send a valid TaxCode to MoR.

    strict=True (payload build) refuses to emit a TaxCode that is not backed
    by an EIMS Setting > Account Config row, so an unmapped account can never
    reach MoR carrying a raw ERP account name as the tax code.
    """
    line_tax_rate = header_tax_rate
    line_tax_code = header_tax_code
    line_account = None
    try:
        item_tax_rate_map = json.loads(item_row.get("item_tax_rate") or "{}") or {}
    except (ValueError, TypeError):
        item_tax_rate_map = {}
    fallback_code = None
    fallback_account = None
    for code, rate_val in item_tax_rate_map.items():
        rate_val = float(rate_val or 0)
        resolved = frappe.db.get_value("Account", code, "account_name") if code else None
        if rate_val:
            line_tax_rate = rate_val
            line_tax_code = resolved or code
            line_account = code
            break
        if fallback_code is None:
            fallback_code = resolved or code
            fallback_account = code
    else:
        # All entries are 0% (VAT0 / VATEX) — still send the code.
        if fallback_code is not None:
            line_tax_code = fallback_code
            line_account = fallback_account
            line_tax_rate = 0

    # Translate the resolved account through the configured EIMS tax code
    # mapping (EIMS Setting > Account Config). Only the configured code may be
    # sent to MoR; the raw ERP account name is never a valid tax code.
    if line_tax_code:
        configured = _tax_code_for(line_tax_code)
        if configured:
            return configured, line_tax_rate
        if strict:
            _throw_tax_code_not_configured([line_account or line_tax_code])
        return line_tax_code, line_tax_rate

    # No code on this line or the header: fall back to the single configured
    # Default EIMS tax code (rate read from its Account).
    default_row = _require_default_tax_row() if strict else _default_tax_row()
    if default_row:
        default_rate = 0.0
        if default_row.get("account"):
            default_rate = float(
                frappe.db.get_value("Account", default_row.get("account"), "tax_rate") or 0.0
            )
        return ((default_row.get("tax_code") or "").strip()), default_rate
    return line_tax_code, line_tax_rate


def _settings_tax_rows():
    """Configured EIMS tax code rows from EIMS Setting > Account Config."""
    settings = frappe.get_cached_doc("EIMS Setting")
    return settings.get("tax_code_config") or []


def _default_tax_row():
    """The single row marked Is Default (the fallback EIMS tax code).

    Returns None only when the mapping table is empty. A populated table must
    carry exactly one default (enforced by EIMS Setting validation), so when
    more than one is found we refuse to guess and return None rather than
    silently picking the first.
    """
    defaults = [
        row for row in _settings_tax_rows() if int(row.get("is_default") or 0) == 1
    ]
    if len(defaults) == 1:
        return defaults[0]
    return None


def _require_default_tax_row():
    """The default tax code row, or a clear error explaining what is missing."""
    rows = _settings_tax_rows()
    if not rows:
        frappe.throw(
            "No EIMS tax codes are configured. Add at least one row to "
            '<a href="/app/eims-setting">EIMS Setting &rarr; Account Config</a>, '
            "marking exactly one as <b>Default</b>.",
            title="EIMS Schema Error: No Default Tax Code",
        )
    defaults = [row for row in rows if int(row.get("is_default") or 0) == 1]
    if not defaults:
        frappe.throw(
            "No <b>Default</b> tax code is configured. Mark exactly one row as "
            "<b>Default</b> on "
            '<a href="/app/eims-setting">EIMS Setting &rarr; Account Config</a>. '
            "The default is used when an invoice line carries no tax code of its own.",
            title="EIMS Schema Error: No Default Tax Code",
        )
    if len(defaults) > 1:
        listed = ", ".join(
            f"<b>{(r.get('tax_code') or '').strip()}</b>" for r in defaults
        )
        frappe.throw(
            "More than one row is marked <b>Default</b> in the Account Config "
            "table: {listed}. Exactly one row must be the default.".format(listed=listed),
            title="EIMS Schema Error: Duplicate Default Tax Code",
        )
    return defaults[0]


def _tax_config_map():
    """Build the Account -> EIMS tax code mapping from EIMS Setting.

    The mapping is strictly one-to-one: each tax account maps to exactly one
    EIMS tax code, and each EIMS tax code is used by exactly one tax account.
    Both the Account document name and its account_name are indexed so callers
    can look up either form.

    Returns (mapping, account_conflicts, code_conflicts, duplicate_rows):
      mapping          alias -> tax code (first configured row wins, so payload
                       output stays deterministic)
      account_conflicts  alias -> {codes} when one account has several codes
      code_conflicts     code -> {accounts} when one code is claimed by
                       several accounts
      duplicate_rows     {(account, code)} repeated verbatim in the config
    """
    mapping = {}
    account_conflicts = {}
    code_conflicts = {}
    duplicate_rows = set()
    code_owner = {}
    seen_pairs = set()
    for row in _settings_tax_rows():
        account = (row.get("account") or "").strip()
        code = (row.get("tax_code") or "").strip()
        if not account or not code:
            continue

        pair = (account, code)
        if pair in seen_pairs:
            duplicate_rows.add(pair)
        seen_pairs.add(pair)

        owner = code_owner.get(code)
        if owner and owner != account:
            code_conflicts.setdefault(code, {owner}).add(account)
        else:
            code_owner[code] = account

        account_name = (frappe.db.get_value("Account", account, "account_name") or "").strip()
        for alias in (account, account_name):
            if not alias:
                continue
            existing = mapping.get(alias)
            if existing:
                if existing != code:
                    account_conflicts.setdefault(alias, set()).update({existing, code})
                continue
            mapping[alias] = code
    return mapping, account_conflicts, code_conflicts, duplicate_rows


def _tax_code_for(identifier):
    """Map an Account (document name or account_name) to its configured EIMS
    tax code. Returns None when no EIMS Setting > Account Config row matches —
    callers must never substitute a raw account name."""
    if not identifier:
        return None
    mapping, _account_conflicts, _code_conflicts, _duplicate_rows = _tax_config_map()
    return mapping.get(str(identifier).strip())


def _invoice_tax_accounts(doc):
    """Tax accounts referenced by the invoice, in encounter order.

    Covers the Taxes and Charges child table plus every per-line item_tax_rate
    override key.

    A row counts as a tax account when its Account is of type "Tax", rather
    than by charge_type: real invoices use charge_type "On Net Total" (not
    "On Tax"), and flat "Actual" rows can still point at a genuine Tax account,
    so keying off charge_type would both miss real taxes and misclassify
    others. Non-tax heads such as a delivery-charges shipping account are
    correctly ignored.
    """
    accounts = []

    def add(account):
        account = (account or "").strip()
        if not account or account in accounts:
            return
        if not _is_tax_account(account):
            return
        accounts.append(account)

    for te in (doc.get("taxes") or []):
        add(te.get("account_head"))

    for item in (doc.get("items") or []):
        try:
            rate_map = json.loads(item.get("item_tax_rate") or "{}") or {}
        except (ValueError, TypeError):
            continue
        if isinstance(rate_map, dict):
            for account in rate_map:
                add(account)
    return accounts


def _is_tax_account(account):
    """True when the Account exists and is of type Tax. An unknown or deleted
    Account is not treated as a tax account here; ERP validation reports it."""
    if not account:
        return False
    account_type = frappe.db.get_value("Account", account, "account_type")
    if not account_type:
        return False
    return str(account_type).strip().lower() == "tax"


def _throw_tax_code_not_configured(accounts):
    """Reject an invoice whose tax accounts are not mapped to EIMS tax codes."""
    accounts = [a for a in (accounts or []) if a]
    if not accounts:
        return
    settings_url = '<a href="/app/eims-setting">EIMS Setting &rarr; Account Config</a>'
    frappe.throw(
        "Tax account(s) <b>{accounts}</b> are not mapped to an EIMS tax code.<br><br>"
        "EIMS requires each tax account to be mapped to a valid tax code on "
        "{settings}. Add a row for each account (for example <b>VAT15 - GT</b> "
        "&rarr; <b>VAT15</b>, <b>VAT0 - GT</b> &rarr; <b>VAT0</b>, "
        "<b>VATEX - GT</b> &rarr; <b>VATEX</b>), then save the invoice again."
        .format(
            accounts=", ".join(f"<b>{a}</b>" for a in accounts),
            settings=settings_url,
        ),
        title="EIMS Schema Error: Tax Account Not Mapped",
    )


def validate_tax_code_config(doc):
    """Every tax account used by the invoice must resolve to an EIMS tax code.

    Also requires the mapping table to carry exactly one Default tax code,
    which is the fallback for any line that resolves no code of its own. Runs
    before save so configuration gaps are reported in the form, never at
    registration.
    """
    # Exactly one default tax code must exist before any invoice can be saved.
    _require_default_tax_row()

    accounts = _invoice_tax_accounts(doc)
    if not accounts:
        return
    mapping, account_conflicts, code_conflicts, duplicate_rows = _tax_config_map()

    missing = []
    for account in accounts:
        account_name = (frappe.db.get_value("Account", account, "account_name") or "").strip()
        if account not in mapping and account_name not in mapping:
            missing.append(account)

    if missing:
        _throw_tax_code_not_configured(missing)

    if account_conflicts:
        detail = ", ".join(
            "<b>{account}</b> ({codes})".format(
                account=account, codes=" / ".join(sorted(codes))
            )
            for account, codes in sorted(account_conflicts.items())
        )
        frappe.throw(
            "Conflicting EIMS tax codes are configured for the same tax account: "
            "{detail}.<br><br>Keep exactly one row per account on "
            '<a href="/app/eims-setting">EIMS Setting &rarr; Account Config</a>, '
            "then save the invoice again.".format(detail=detail),
            title="EIMS Schema Error: Duplicate Tax Account Mapping",
        )

    if code_conflicts:
        detail = ", ".join(
            "<b>{code}</b> &rarr; {accounts}".format(
                code=code,
                accounts=" / ".join(
                    f"<b>{a}</b>" for a in sorted(accounts)
                ),
            )
            for code, accounts in sorted(code_conflicts.items())
        )
        frappe.throw(
            "The same EIMS tax code is mapped to more than one tax account: "
            "{detail}.<br><br>Each tax code must belong to exactly one account. "
            "Keep exactly one row per tax code on "
            '<a href="/app/eims-setting">EIMS Setting &rarr; Account Config</a>, '
            "then save the invoice again.".format(detail=detail),
            title="EIMS Schema Error: Duplicate Tax Code Mapping",
        )

    if duplicate_rows:
        detail = ", ".join(
            f"<b>{account}</b> &rarr; <b>{code}</b>" for account, code in sorted(duplicate_rows)
        )
        frappe.throw(
            "Duplicate rows exist in the EIMS tax code mapping: {detail}.<br><br>"
            "Each tax account must appear exactly once on "
            '<a href="/app/eims-setting">EIMS Setting &rarr; Account Config</a>, '
            "then save the invoice again.".format(detail=detail),
            title="EIMS Schema Error: Duplicate Tax Code Mapping",
        )


def header_tax_info(doc):
    """Effective header-level EIMS tax code + rate from the first tax row.

    Prefers the first row that actually carries a rate (the first row may be a
    0% / exempt row on mixed invoices); falls back to the first row's code so
    lines still carry a valid TaxCode."""
    tax_type = ""
    tax_rate = 0
    tax_entries = doc.get("taxes")
    if doc.get("taxes_and_charges") and tax_entries:
        for te in tax_entries:
            account = te.account_head
            row_code = frappe.db.get_value("Account", account, "account_name")
            row_rate = float(te.rate or 0)
            if row_rate > 0:
                return row_code, row_rate
            if not tax_type:
                tax_type = row_code
    return tax_type, tax_rate


def _add_if_present(target_dict, key, value):

    if value is not None and str(value).strip() != "":
        target_dict[key] = value


def _invoice_has_tax_code(doc):
    """True if the invoice can carry a resolvable EIMS TaxCode on every line.

    Checks the Taxes and Charges child table first, then per-line
    item_tax_rate overrides, then the configured Default EIMS tax code.
    Used by validate_invoice_for_eims to prompt the user before a tax-less
    invoice ever reaches registration."""
    header_code, header_rate = header_tax_info(doc)
    if header_code:
        return True
    for item_row in (doc.get("items") or []):
        line_code, _rate = resolve_item_tax_rate(item_row, "", 0)
        if line_code:
            return True
    if _default_tax_row():
        return True
    return False


def _has_default_tax_code():
    """True when exactly one Default tax code row is configured."""
    return _default_tax_row() is not None


def resolve_mor_payment_mode(mode_of_payment):
    if not mode_of_payment:
        return None
    configured = frappe.db.get_value("Mode of Payment", mode_of_payment, "custom_mor_mode")
    if configured and str(configured).strip() in MOR_PAYMENT_MODES:
        return str(configured).strip()
    name = str(mode_of_payment).strip().upper()
    for keyword, mor_mode in _MOR_MODE_KEYWORDS:
        if keyword in name:
            return mor_mode
    return None



_MOR_MODE_KEYWORDS = (
    ("CASH", "CASH"),
    ("CHEQUE", "CHEQUE"),
    ("CHECK", "CHEQUE"),
    ("CPO", "CPO"),
    ("SWIFT", "SWIFT"),
    ("WIRE", "Wire Transfer"),
    ("LOCAL BANK", "Local Bank Transfer"),
    ("BANK TRANSFER", "Local Bank Transfer"),
    ("TRANSFER", "Local Bank Transfer"),
    ("BANK", "Local Bank Transfer"),
    ("CARD", "Card"),
    ("LETTER OF CREDIT", "Letter of Credit"),
    ("LC", "Letter of Credit"),
    ("ADVANCE", "Local Bank Transfer"),
    ("CREDIT", "Letter of Credit"),
)




WHT_TRANSACTION_CODES = ("TWTH", "TWHT", "WTHOT")
WHT_INCOME_CODES = ("IWTH", "VATWH")


def classify_withholding(account):
    """Return 'transaction_wht' or 'income_wht' for a tax Account, or None.

    Detection prefers an explicit EIRMS tax code on the Account
    (custom_eims_tax_code, when that custom field exists) and otherwise falls
    back to matching the account name / account code against the known
    withholding codes (TWTH/WTHOT = transaction, IWTH/VATWH = income).
    """
    fields = ["account_name"]
    if frappe.get_meta("Account").has_field("custom_eims_tax_code"):
        fields.append("custom_eims_tax_code")
    row = frappe.db.get_value("Account", account, fields) or (None,) * len(fields)
    data = dict(zip(fields, row))
    code = data.get("custom_eims_tax_code")
    name = data.get("account_name")
    # `account` is the account_head (the Account document name/id), which in
    # this deployment IS the tax code, so include it in the match as well.
    blob = f"{account or ''} {code or ''} {name or ''}".upper()
    if any(x in blob for x in ("IWTH", "VATWH")):
        return "income_wht"
    if any(x in blob for x in ("TWTH", "TWHT", "WTHOT")):
        return "transaction_wht"
    return None


def _row_rate(te):

    rate = getattr(te, "tax_rate", None)
    if rate in (None, ""):
        rate = getattr(te, "rate", None)
    if rate in (None, ""):
        if getattr(te, "account_head", None):
            rate = frappe.db.get_value("Account", te.account_head, "tax_rate")
    try:
        return float(rate or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _row_tax_amount(te):
    """Monetary tax amount for a Taxes and Charges row.

    With `apply_discount_on = "Grand Total"` ERPNext stores two figures per
    row: `tax_amount` is computed on the pre-discount `base_total`, while
    `tax_amount_after_discount_amount` is computed on the post-discount
    `net_total`. The latter is what the header (`total_taxes_and_charges`)
    and `grand_total` actually use, so prefer it whenever the invoice
    carries a header discount.
    """
    for attr in ("tax_amount_after_discount_amount", "tax_amount"):
        value = getattr(te, attr, None)
        if value not in (None, ""):
            return float(value or 0.0)
    return 0.0


def sum_withholding(invoice_doc, transaction_type=None):
    if transaction_type not in ("B2B", "B2G"):
        return 0.0, 0.0

    service_total = 0.0
    goods_total = 0.0
    for item in (invoice_doc.items or []):
        amount = abs(float(item.base_net_amount or item.net_amount or 0.0))
        is_stock = frappe.db.get_value("Item", item.item_code, "is_stock_item") if item.item_code else 1
        if is_stock:
            goods_total += amount
        else:
            service_total += amount

    if service_total <= 10000 and goods_total <= 20000:
        return 0.0, 0.0

    transaction_wht = 0.0
    income_wht = 0.0
    for te in (invoice_doc.taxes or []):
        account = te.account_head
        if not account:
            continue
        category = classify_withholding(account)
        # ValueDetails.TransactionWithholdValue / IncomeWithholdValue are
        # monetary amounts, NOT percentages. Reading the rate here used to
        # register "3.0" instead of the real withheld amount.
        amount = abs(_row_tax_amount(te))
        if category == "transaction_wht":
            transaction_wht += amount
        elif category == "income_wht" and transaction_type == "B2G":
            income_wht += amount
    return transaction_wht, income_wht


class EIMSConnectorPayload:
    def build_invoice_payload(self, invoice_doc, override_doc_num=None, override_prev_irn=None,
                              override_note_type=None, override_note_ref_irn=None):
        company = frappe.get_doc("Company", invoice_doc.company)
        company_link = f"/app/company/{company.name}"
        invoice_link = f"/app/sales-invoice/{invoice_doc.name}"

        is_walk_in = (invoice_doc.customer or "") == WALK_IN_CUSTOMER

        # TransactionType preference: the user-set custom field wins; otherwise
        # fall back to the customer-type mapping (preserves POS invoices which
        # don't carry the Select field). Walk-in sales are always B2C.
        transaction_type = getattr(invoice_doc, "custom_transaction_type", "") or ""
        if not transaction_type:
            customer_type = frappe.db.get_value("Customer", invoice_doc.customer, "customer_type")
            t_map = {
                "Individual": "B2C",
                "Company": "B2B",
                "Government": "G2C",
                "Partnership": "B2B",
            }
            transaction_type = t_map.get(customer_type, "")
        if not transaction_type and is_walk_in:
            transaction_type = "B2C"
        if not transaction_type:
            frappe.throw(
                "Please set the <b>Transaction Type</b> on this invoice before registering.",
                title="EIMS Transaction Type Required",
            )

        customer = frappe.get_doc("Customer", invoice_doc.customer)
        customer_link = f"/app/customer/{customer.name}"
        if is_walk_in:
            # Walk-in sales have no registered buyer: the invoice keeps the
            # walk-in name but the MoR submission is a minimal B2C with no
            # ID and no contact details. A TIN captured at the register
            # (custom_buyer_tin) is still sent when one was typed.
            cust_details = frappe._dict({
                "name": WALK_IN_CUSTOMER,
                "legal_name": None, "tin_number": "", "email": "",
                "region": "", "city": "", "country": None, "zone": None,
                "kebele": None, "woreda": None, "id_number": None,
                "id_type": None, "phone": None, "sub_tin": None,
                "trade_name": None, "sub_city": None, "house_number": None,
                "locality": None,
            })
            cust_link = customer_link
        else:
            cust_details = frappe.get_doc("Customer Details", invoice_doc.customer)
            cust_link = f"/app/customer-details/{cust_details.name}"

        # BuyerDetails.Tin — Conditional, required only if transaction is NOT B2C/G2C
        # A TIN captured at the POS register (custom_buyer_tin) takes precedence,
        # so even walk-in sales carry a buyer TIN when the cashier typed one.
        invoice_tin = getattr(invoice_doc, "custom_buyer_tin", "") or ""
        raw_tin = invoice_tin or cust_details.tin_number or ""
        clean_tin = re.sub(r"\D", "", str(raw_tin))

        buyer_email = (cust_details.email or "").strip()
        if not buyer_email and not is_walk_in:
            buyer_email = (customer.get("custom_eims_email") or "").strip()

        buyer_region = (cust_details.region or "").strip()

        seller_vat_number = company.custom_vat_number  # Conditional
        seller_email = self._require(company.email, "Email", company.name, company_link)
        seller_phone = self._require(company.phone_no, "Phone", company.name, company_link)
        seller_region = self._require(company.custom_seller_region_code, "Seller Region Code", company.name, company_link)
        seller_wereda = self._require(company.custom_seller_woreda_code, "Seller Wereda Code", company.name, company_link)
        seller_city = self._require(company.custom_city, "City", company.name, company_link)
        seller_house_number = company.custom_house_number  # Optional

        buyer_city = "" if is_walk_in else self._require(cust_details.city, "City", cust_details.name, cust_link)
        buyer_country = cust_details.country  # Optional
        buyer_zone = cust_details.zone  # Optional
        buyer_kebele = cust_details.kebele  # Optional
        buyer_woreda = "" if is_walk_in else self._require(cust_details.woreda, "Wereda", cust_details.name, cust_link)

        buyer_id_number = cust_details.id_number
        buyer_id_type = (cust_details.id_type or "").strip().upper()
        # MoR accepts only NID, KID, SID, WID, PST, DLS, MRS. Normalize
        # common human-readable labels; anything unrecognised is omitted
        # (the schema does not require an ID for B2C).
        if buyer_id_type not in ID_TYPES:
            buyer_id_type = ID_TYPE_ALIASES.get(buyer_id_type, "")

        # Walk-in sales fall back to the seller's region so the BuyerDetails
        # schema (Region is a required, numeric 1-3 digit code) stays valid.
        if is_walk_in and not buyer_region:
            buyer_region = seller_region

        buyer_vat_number = frappe.db.get_value("Customer", invoice_doc.customer, "custom_vat_number")  # Conditional

        if override_doc_num is None:
            frappe.throw(
                "Internal Error: build_invoice_payload() requires an explicit "
                "document number. Callers must peek the next number via "
                "_peek_next_document_number() (or reuse an existing invoice's "
                "custom_document_number) before building the payload.",
                title="EIMS Document Number Error"
            )
        doc_num = int(override_doc_num)

        if override_prev_irn is not None:
            prev_irn = override_prev_irn
        else:
            prev_irn = self._lookup_irn_for_doc_num(doc_num - 1)

        # Credit (CRE) / Debit (DEB) note detection, driven by ERPNext's
        # native return fields (no custom fields needed):
        #   - is_debit_note ("Is Rate Adjustment Entry (Debit Note)")
        #       -> DEB (increases the original invoice's quantity/price)
        #   - is_return (credit note) -> CRE (decreases it)
        #   - otherwise               -> INV
        # Both CRE and DEB reference the already-registered original invoice
        # through RelatedDocument (the native return_against link). DEB keys
        # off is_debit_note directly (not gated on is_return) so a
        # rate-adjustment entry is always treated as a debit note against the
        # return_against invoice.
        if override_note_type:
            note_type = override_note_type.strip().upper()
        elif getattr(invoice_doc, "is_debit_note", 0):
            note_type = "DEB"
        elif getattr(invoice_doc, "is_return", 0):
            note_type = "CRE"
        else:
            note_type = "INV"
        if note_type not in ("INV", "CRE", "DEB"):
            frappe.throw(
                f"Unsupported EIMS note type '{note_type}' (expected INV, CRE or DEB).",
                title="EIMS Schema Error: Invalid Note Type",
            )

        note_ref_irn = None
        note_ref_lines = []
        original_name = invoice_doc.get("return_against") or None
        if note_type in ("CRE", "DEB"):
            if override_note_ref_irn:
                note_ref_irn = override_note_ref_irn
            else:
                note_ref_irn = self._lookup_irn_for_invoice(original_name) if original_name else None
            if not note_ref_irn:
                frappe.throw(
                    f"Validation Error on Sales Invoice ({invoice_doc.name}):<br><br>"
                    f"<b>{note_type}</b> notes must reference an EIRMS-registered original invoice. "
                    f"Set <b>Return Against</b> to the original invoice whose <b>custom_irn</b> "
                    f"is already populated, then try again.",
                    title="EIMS Schema Error: Missing Original Invoice IRN",
                )

            # MoR requires DEB/CRE notes to echo the referenced document's
            # TransactionType and to mirror its ItemList positionally; otherwise
            # registration is rejected with 7030 (transaction type does not
            # match) and/or 7020 (item mismatch at line N). Adopt ground truth
            # from the original's registered payload so the note matches.
            ref_snapshot = self._note_reference_snapshot(original_name)
            if ref_snapshot["transaction_type"]:
                transaction_type = ref_snapshot["transaction_type"]
            note_ref_lines = ref_snapshot["item_lines"]

        cashier_name = None
        sales_team_entries = invoice_doc.get("sales_team")
        if sales_team_entries:
            cashier_name = sales_team_entries[0].sales_person

        payment_mode = None
        payment_entries = invoice_doc.get("payments")
        if payment_entries:
            payment_mode = payment_entries[0].mode_of_payment
            resolved_payment_mode = resolve_mor_payment_mode(payment_mode)
            payment_mode = resolved_payment_mode or payment_mode

        raw_phone = cust_details.phone or getattr(invoice_doc, "contact_mobile", "") or ""
        clean_phone = raw_phone.replace("+251", "0").replace(" ", "")
        if clean_phone and not clean_phone.startswith("0"):
            clean_phone = "0" + clean_phone

        default_client = self.get_default_client_data()

        payload = {
            "Version": "1",
            "TransactionType": transaction_type,
            "DocumentDetails": {
                "DocumentNumber": str(doc_num),
                "Date": (get_datetime(invoice_doc.posting_date).strftime("%d-%m-%YT00:00:00")
                         if invoice_doc.posting_date else now_datetime().strftime("%d-%m-%YT00:00:00")),
                "Type": note_type
            },
            "SellerDetails": {
                "Tin": self.settings.seller_tin,
                "LegalName": company.custom_seller_legal_name or company.company_name,
                "Email": seller_email,
                "Phone": seller_phone,
                "Region": seller_region,
                "Wereda": seller_wereda,
                "City": seller_city,
            },
            "SourceSystem": {
                "SystemType": default_client.system_type,
                "SystemNumber": default_client.system_number,
                "InvoiceCounter": doc_num
            },
            "PaymentDetails": {
                "PaymentTerm": "IMMEDIATE"
            },
            "ValueDetails": {
                "InvoiceCurrency": invoice_doc.currency or "ETB",
            },
            "ReferenceDetails": {},
            "ItemList": []
        }

        # BuyerDetails — minimal LegalName for walk-in sales (no buyer exists,
        # but MoR requires the property and the LegalName field)
        if not is_walk_in:
            payload["BuyerDetails"] = {
                "City": buyer_city,
                "Region": buyer_region,
                "Wereda": buyer_woreda,
            }
        else:
            payload["BuyerDetails"] = {"LegalName": WALK_IN_CUSTOMER}
            _add_if_present(payload["BuyerDetails"], "Tin", clean_tin)

        # SellerDetails
        _add_if_present(payload["SellerDetails"], "VatNumber", seller_vat_number)
        _add_if_present(payload["SellerDetails"], "HouseNumber", seller_house_number)
        _add_if_present(payload["SellerDetails"], "TradeName", company.get("custom_trade_name"))
        _add_if_present(payload["SellerDetails"], "SubTin", company.get("custom_sub_tin"))
        _add_if_present(payload["SellerDetails"], "Country", company.get("custom_country"))
        _add_if_present(payload["SellerDetails"], "Zone", company.get("custom_zone"))
        _add_if_present(payload["SellerDetails"], "SubCity", company.get("custom_sub_city"))
        _add_if_present(payload["SellerDetails"], "Kebele", company.get("custom_kebele"))
        _add_if_present(payload["SellerDetails"], "Locality", company.get("custom_locality"))

        # BuyerDetails
        if not is_walk_in:
            _add_if_present(payload["BuyerDetails"], "LegalName", cust_details.legal_name or invoice_doc.customer_name)
            _add_if_present(payload["BuyerDetails"], "Tin", clean_tin)
            _add_if_present(payload["BuyerDetails"], "SubTin", cust_details.get("sub_tin"))
            _add_if_present(payload["BuyerDetails"], "VatNumber", buyer_vat_number)
            _add_if_present(payload["BuyerDetails"], "Email", buyer_email)
            _add_if_present(payload["BuyerDetails"], "Phone", clean_phone)
            _add_if_present(payload["BuyerDetails"], "TradeName", cust_details.get("trade_name"))
            _add_if_present(payload["BuyerDetails"], "Country", buyer_country)
            _add_if_present(payload["BuyerDetails"], "Zone", buyer_zone)
            _add_if_present(payload["BuyerDetails"], "SubCity", cust_details.get("sub_city"))
            _add_if_present(payload["BuyerDetails"], "HouseNumber", cust_details.house_number)
            _add_if_present(payload["BuyerDetails"], "Kebele", buyer_kebele)
            _add_if_present(payload["BuyerDetails"], "Locality", cust_details.get("locality"))

        if buyer_id_type in ID_TYPES and buyer_id_number:
            payload["BuyerDetails"]["IdNumber"] = buyer_id_number
            payload["BuyerDetails"]["IdType"] = buyer_id_type
        else:
            payload["BuyerDetails"]["IdNumber"] = "000000"
            payload["BuyerDetails"]["IdType"] = "KID"

        # ReferenceDetails — PreviousIrn is always required by MoR even for the
        # first invoice (it is simply empty when there is no prior registration).
        payload["ReferenceDetails"]["PreviousIrn"] = prev_irn

        if note_type in ("CRE", "DEB"):
            payload["ReferenceDetails"]["RelatedDocument"] = note_ref_irn
            payload["DocumentDetails"]["Reason"] = (
                f"CREDIT NOTE for invoice {invoice_doc.name}" if note_type == "CRE"
                else f"DEBIT NOTE for invoice {invoice_doc.name}"
            )

        # SourceSystem
        _add_if_present(payload["SourceSystem"], "CashierName", cashier_name)
        _add_if_present(payload["SourceSystem"], "SalesPersonName", cashier_name)

        # PaymentDetails
        _add_if_present(payload["PaymentDetails"], "Mode", payment_mode)

        # ValueDetails
        discount_val = float(invoice_doc.discount_amount or 0.0)
        if discount_val:
            payload["ValueDetails"]["Discount"] = discount_val

        exchange_rate = getattr(invoice_doc, "conversion_rate", None)
        if invoice_doc.currency and invoice_doc.currency != "ETB":
            _add_if_present(payload["ValueDetails"], "ExchangeRate", exchange_rate)

        excise_val = getattr(invoice_doc, "custom_excise_tax_value", None)
        _add_if_present(payload["ValueDetails"], "ExciseValue", excise_val)


        transaction_wht, income_wht = sum_withholding(invoice_doc, transaction_type)
        payload["ValueDetails"]["TransactionWithholdValue"] = round(transaction_wht, 6)
        payload["ValueDetails"]["IncomeWithholdValue"] = round(income_wht, 6)

        # Exactly one Default tax code must be configured before any payload is
        # produced. It is the fallback for lines that resolve no code of their
        # own, so building without it would leave the submission ambiguous.
        _require_default_tax_row()

        tax_type, tax_rate = header_tax_info(invoice_doc)

        note_ordered_items = list(invoice_doc.items or [])
        if note_type in ("CRE", "DEB") and note_ref_lines:
            note_ordered_items = self._align_note_items(
                note_ordered_items, note_ref_lines, invoice_doc, note_type)

        for idx, item in enumerate(note_ordered_items, start=1):
            is_note = note_type in ("CRE", "DEB")
            base_rate = abs(float(item.base_rate or 0.0))
            qty = abs(float(item.qty or 0.0))
            line_net_amount = abs(float(item.base_net_amount or item.net_amount or 0.0))

            # Per-item tax rate/code (item_tax_rate is a JSON map like
            # {"VAT15 - GT": 15}) — falls back to the header tax row. The code
            # is captured even at 0% so VAT0 / VATEX lines send a valid
            # TaxCode to MoR. strict=True refuses to emit an unmapped account.
            line_tax_code, line_tax_rate = resolve_item_tax_rate(
                item, tax_type, tax_rate, strict=True)

            line_tax = round(line_net_amount * (line_tax_rate / 100), 6)


            unit_price = round(line_net_amount / qty, 6) if qty else base_rate


            line_discount = 0.0
            pl_rate = float(item.get("price_list_rate") or 0)
            amount_incl = abs(float(item.amount or 0)) or (base_rate * qty)
            if qty and pl_rate > 0:
                disc_incl = round(pl_rate * qty - amount_incl, 2)
                if disc_incl > 0.005:
                    disc_excl = disc_incl / (1 + (line_tax_rate or 0) / 100.0)
                    unit_price = round((line_net_amount + disc_excl) / qty, 6)
                    line_discount = round(unit_price * qty - line_net_amount, 6)
            raw_uom = str(item.uom or "PCS").strip().upper()

            line_item = {
                "LineNumber": idx,
                "ItemCode": item.item_code,
                "ProductDescription": item.description or item.item_name or "string",
                "NatureOfSupplies": "goods",
                "Quantity": qty,
                "UnitPrice": unit_price,
                "PreTaxValue": round(line_net_amount, 2),
                "TaxCode": line_tax_code,
                "TaxAmount": line_tax,
                "Unit": raw_uom if raw_uom in VALID_UNITS else "PCS",
                "TotalLineAmount": round(line_net_amount + line_tax, 6)
            }

            _add_if_present(line_item, "HarmonizationCode", getattr(item, "custom_harmonization_code", None))

            if line_discount:
                line_item["Discount"] = line_discount

            excise_tax_val = getattr(item, "custom_excise_tax_value", None)
            if excise_tax_val:
                line_item["ExciseTaxValue"] = float(excise_tax_val)
            else:
                line_item["ExciseTaxValue"] = 0.0

            payload["ItemList"].append(line_item)

        payload["ValueDetails"]["TaxValue"] = round(sum(it["TaxAmount"] for it in payload["ItemList"]), 6)
        payload["ValueDetails"]["TotalValue"] = round(sum(it["TotalLineAmount"] for it in payload["ItemList"]), 6)
        total_line_discount = round(sum(it.get("Discount", 0.0) for it in payload["ItemList"]), 6)
        if total_line_discount:
            payload["ValueDetails"]["Discount"] = total_line_discount

        self._validate_payload_schema_rules(payload, invoice_doc)
        return payload

    def _note_reference_snapshot(self, original_name):
        """Return the ground-truth snapshot EIMS accepted for the referenced
        original invoice: its TransactionType and its ItemList (in registration
        order). Falls back to the original document when no audit payload."""
        ref = {"transaction_type": "", "item_lines": []}
        if not original_name:
            return ref

        if frappe.db.exists("DocType", "EIMS Audit Log"):
            rows = frappe.db.sql(
                """SELECT request_brief FROM `tabEIMS Audit Log`
                   WHERE invoice=%s AND action='Invoice Registration' AND success=1
                   ORDER BY timestamp DESC LIMIT 1""",
                original_name, as_dict=True)
            if rows:
                try:
                    payload = json.loads(rows[0].get("request_brief") or "{}")
                except (ValueError, TypeError):
                    payload = {}
                tt = (payload.get("TransactionType") or "").strip()
                if tt:
                    ref["transaction_type"] = tt
                item_list = payload.get("ItemList") or []
                if item_list:
                    ref["item_lines"] = item_list
                    return ref

        for doctype, irn_field in (("Sales Invoice", "custom_irn"), ("POS Invoice", "custom_mor_irn")):
            if frappe.db.exists(doctype, original_name):
                doc = frappe.get_doc(doctype, original_name)
                ref["transaction_type"] = (getattr(doc, "custom_transaction_type", "") or "").strip()
                for it in (doc.get("items") or []):
                    ref["item_lines"].append({
                        "ItemCode": it.item_code,
                        "Quantity": abs(float(it.qty or 0.0)),
                        "Unit": (it.uom or "PCS").strip().upper(),
                        "LineNumber": it.idx,
                    })
                break
        return ref

    def _align_note_items(self, note_items, ref_lines, invoice_doc, note_type):
        """Reorder the note's items to mirror the original invoice's registered
        ItemList order and raise clear pre-submission errors on missing, extra,
        or mismatched lines. EIMS compares DEB/CRE lines positionally against
        the referenced document (rule 7020), so the note must reproduce the
        original's lines exactly."""
        invoice_link = f"/app/sales-invoice/{invoice_doc.name}"
        ref_codes = [
            (str((line.get("ItemCode") or "")).strip()
             or (line.get("ProductDescription") or "")
             or (line.get("ItemDescription") or "")
             or "")
            for line in ref_lines
        ]

        used = set()
        ordered = []
        for pos, code in enumerate(ref_codes, start=1):
            if not code:
                continue
            candidates = [i for i, it in enumerate(note_items)
                          if it.item_code == code and i not in used]
            if not candidates:
                frappe.throw(
                    f"Validation Error on <a href='{invoice_link}'>Sales Invoice "
                    f"({invoice_doc.name})</a>:<br><br>"
                    f"<b>{note_type}</b> notes must mirror the original registered "
                    f"invoice line-by-line. Line {pos} of the original expects item "
                    f"<b>{code}</b>, which is not present on this note. Add the matching "
                    f"line (same item, quantity and unit) exactly as on the original "
                    f"invoice, then resubmit.",
                    title="EIMS Schema Error: Note Item Missing",
                )
            idx = candidates[0]
            used.add(idx)
            item = note_items[idx]
            ref_line = ref_lines[pos - 1]

            ref_qty = abs(float((ref_line.get("Quantity") or 0.0)))
            note_qty = abs(float(item.qty or 0.0))
            if abs(ref_qty - note_qty) > 0.005:
                frappe.throw(
                    f"Validation Error on <a href='{invoice_link}'>Sales Invoice "
                    f"({invoice_doc.name})</a>:<br><br>"
                    f"<b>{note_type}</b> line {pos} quantity does not match the original "
                    f"invoice: note has <b>{note_qty}</b>, original registered <b>{ref_qty}</b> "
                    f"for item <b>{item.item_code}</b>. Quantity must match the referenced "
                    f"invoice for MoR to accept the {note_type}.",
                    title="EIMS Schema Error: Note Quantity Mismatch",
                )

            ref_unit = (ref_line.get("Unit") or "PCS").strip().upper()
            note_unit = str(item.uom or "PCS").strip().upper()
            if ref_unit in VALID_UNITS and note_unit in VALID_UNITS and ref_unit != note_unit:
                frappe.throw(
                    f"Validation Error on <a href='{invoice_link}'>Sales Invoice "
                    f"({invoice_doc.name})</a>:<br><br>"
                    f"<b>{note_type}</b> line {pos} unit does not match the original "
                    f"invoice: note has <b>{note_unit}</b>, original registered <b>{ref_unit}</b> "
                    f"for item <b>{item.item_code}</b>. Use the same unit as the referenced "
                    f"invoice before resubmitting.",
                    title="EIMS Schema Error: Note Unit Mismatch",
                )

            ordered.append(item)

        extra = [it.item_code for i, it in enumerate(note_items) if i not in used]
        if extra:
            frappe.throw(
                f"Validation Error on <a href='{invoice_link}'>Sales Invoice "
                f"({invoice_doc.name})</a>:<br><br>"
                f"<b>{note_type}</b> notes must mirror the original registered invoice "
                f"line-by-line, but this note adds item(s) not on the original: "
                f"<b>{', '.join(set(extra))}</b>. Remove the extra line(s) or create the "
                f"adjustment against the correct invoice.",
                title="EIMS Schema Error: Extra Note Line",
            )

        return ordered

    def _validate_payload_schema_rules(self, payload, invoice_doc):
        invoice_link = f"/app/sales-invoice/{invoice_doc.name}"

        tax_value = payload["ValueDetails"]["TaxValue"]
        if tax_value < 0:
            frappe.throw(
                f"Validation Error on <a href='{invoice_link}'>Sales Invoice ({invoice_doc.name})</a>:<br><br>"
                f"<b>Total Tax Value</b> cannot be negative for EIMS submission. Found: {tax_value}. "
                f"This usually means the invoice's tax/charges total is negative (e.g. a discount applied "
                f"as a negative tax line). Please review the Taxes and Charges table on this invoice.",
                title="EIMS Schema Error: Negative Tax Value"
            )

        for item in payload["ItemList"]:
            tax_amount = item["TaxAmount"]
            if tax_amount < 0:
                frappe.throw(
                    f"Validation Error on <a href='{invoice_link}'>Sales Invoice ({invoice_doc.name})</a>:<br><br>"
                    f"<b>Tax Amount</b> for item <b>{item['ItemCode']}</b> (line {item['LineNumber']}) "
                    f"cannot be negative for EIMS submission. Found: {tax_amount}. "
                    f"This usually means the invoice's overall tax total is negative, which gets distributed "
                    f"proportionally across line items. Please review the Taxes and Charges table on this invoice.",
                    title="EIMS Schema Error: Negative Tax Amount"
                )

            nature = item["NatureOfSupplies"]
            if nature not in ("goods", "service"):
                frappe.throw(
                    f"Validation Error on <a href='{invoice_link}'>Sales Invoice ({invoice_doc.name})</a>:<br><br>"
                    f"<b>NatureOfSupplies</b> for item <b>{item['ItemCode']}</b> (line {item['LineNumber']}) "
                    f"must be either 'goods' or 'service'. Found: '{nature}'.",
                    title="EIMS Schema Error: Invalid Nature Of Supplies"
                )

            pre_tax_value = item["PreTaxValue"]
            if pre_tax_value < 0:
                frappe.throw(
                    f"Validation Error on <a href='{invoice_link}'>Sales Invoice ({invoice_doc.name})</a>:<br><br>"
                    f"<b>Pre-Tax Value</b> for item <b>{item['ItemCode']}</b> (line {item['LineNumber']}) "
                    f"cannot be negative for EIMS submission. Found: {pre_tax_value}.",
                    title="EIMS Schema Error: Negative Pre-Tax Value"
                )

        discount = payload["ValueDetails"].get("Discount", 0)
        if discount < 0:
            frappe.throw(
                f"Validation Error on <a href='{invoice_link}'>Sales Invoice ({invoice_doc.name})</a>:<br><br>"
                f"<b>Discount</b> cannot be negative for EIMS submission. Found: {discount}.",
                title="EIMS Schema Error: Negative Discount"
            )

        total_value = payload["ValueDetails"]["TotalValue"]
        if total_value < 0:
            frappe.throw(
                f"Validation Error on <a href='{invoice_link}'>Sales Invoice ({invoice_doc.name})</a>:<br><br>"
                f"<b>Total Value</b> cannot be negative for EIMS submission. Found: {total_value}.",
                title="EIMS Schema Error: Negative Total Value"
            )

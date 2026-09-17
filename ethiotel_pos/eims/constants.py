import re

EIMS_MIN_BULK_SIZE = 2
WALK_IN_CUSTOMER = "Walk-In Customer"

# Mission-critical MoR endpoints. Confirmed against the EIRMS mock collection:
REGISTER_ENDPOINT = "/v1/register"
CANCEL_ENDPOINT = "/v1/cancel"
BULK_CANCEL_ENDPOINT = "/v1/bulkCancel"
VERIFY_ENDPOINT = "/v1/verify"
SALES_RECEIPT_ENDPOINT = "/v1/receipt/sales"
WITHHOLDING_RECEIPT_ENDPOINT = "/v1/receipt/withholding"

ID_TYPES = {"NID", "KID", "SID", "WID", "PST", "DLS", "MRS"}

ID_TYPE_ALIASES = {
    "NATIONAL ID": "NID",
    "NATIONAL ID CARD": "NID",
    "NATIONALID": "NID",
    "KEBELE": "KID",
    "KEBELE ID": "KID",
    "KEBELE ID CARD": "KID",
    "KEBELE CARD": "KID",
    "KEDIDA": "KID",
    "STUDENT ID": "SID",
    "STUDENT": "SID",
    "WORKER ID": "WID",
    "WORKERS ID": "WID",
    "PASSPORT": "PST",
    "DRIVER LICENSE": "DLS",
    "DRIVER'S LICENSE": "DLS",
    "DRIVING LICENSE": "DLS",
    "DRIVER LICENCE": "DLS",
    "DRIVERS LICENCE": "DLS",
    "MARRIAGE CERTIFICATE": "MRS",
    "MARRIAGE CERT": "MRS",
}

# MoR accepted payment modes for receipt TransactionDetails.ModeOfPayment and
# invoice PaymentDetails.PaymentMode. Mirrors the MoR schema enum exactly:
# CASH, CHEQUE, CPO, Local Bank Transfer, SWIFT, Wire Transfer,
# Letter of Credit, Card.
MOR_PAYMENT_MODES = (
    "CASH", "CHEQUE", "CPO", "Local Bank Transfer", "SWIFT",
    "Wire Transfer", "Letter of Credit", "Card",
)

VALID_UNITS = {"LTR", "MTR", "101", "PCS", "ROL", "MTS", "PKG", "SET", "KLG"}

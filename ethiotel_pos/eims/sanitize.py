# Copyright (c) 2026, Guba Technology and contributors
# Redaction helpers used before payloads are persisted to the audit log,
# error logs, or the EIMS debug log file.

import json
import re

# Substrings that indicate a sensitive field value when found in a JSON key.
_SENSITIVE_KEY_HINTS = (
    "tin",
    "phone",
    "mobile",
    "email",
    "address",
    "idtype",
    "idnumber",
    "signature",
    "signedqr",
    "envelope",
    "secret",
    "privatekey",
    "password",
    "bankaccount",
)

# Keys that must be kept intact for audit/tracing (structural fields).
_KEEP_EXACT_KEYS = {
    "irn",
    "irnnumber",
    "documentnumber",
    "docno",
    "docnumber",
    "status",
    "statuscode",
    "conversationid",
    "conversionid",
    "transactiontype",
    "rejectionreason",
}

_ENVELOPE_LIKE = re.compile(r"^[A-Za-z0-9+/=\-_]{80,}$")


def _sensitive_key(key: str) -> bool:
    k = (key or "").lower()
    if k in _KEEP_EXACT_KEYS:
        return False
    return any(h in k for h in _SENSITIVE_KEY_HINTS)


def _mask_value(value):
    if isinstance(value, str):
        if len(value) <= 4:
            return "***"
        return f"{value[:2]}***{value[-2:]}"
    return "***"


def _redact_node(node):
    if isinstance(node, dict):
        return {
            k: _redact_node(_mask_value(v) if _sensitive_key(k) else v)
            for k, v in node.items()
        }
    if isinstance(node, list):
        return [_redact_node(v) for v in node]
    return node


def redact_payload(text) -> str:
    """Redact sensitive fields from a JSON payload string. Non-JSON input
    (e.g. a base64 signed envelope or a plain text body) is truncated and
    masked instead of being parsed."""
    if not text:
        return ""
    text = str(text)[:2000]

    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        # Not JSON - truncate aggressively and mask long/base64-looking runs.
        masked = _ENVELOPE_LIKE.sub("<redacted>", text)
        return masked[:1000]

    return json.dumps(_redact_node(data), separators=(",", ":"), default=str)
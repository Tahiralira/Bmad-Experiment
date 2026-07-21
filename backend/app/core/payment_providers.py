# Payment providers (WS10.2) — the settle-up payment-links registry.
#
# ClearDues is a GLOBAL product (CLAUDE.md ground rule #8): people settle with
# whatever their country uses. Rather than build one payment rail, we let a user
# register the handles they already have (Venmo, PayPal.Me, Cash App, Revolut,
# UPI, a bank IBAN) plus a frictionless CUSTOM path for anything else, and we
# surface those handles at the moment someone owes them money.
#
# This module is the SINGLE source of truth for two things the frontend must not
# duplicate: which provider codes are valid, and how a handle turns into a
# tappable deep link. The frontend keeps only presentation metadata (display
# names, input placeholders) — it renders the pay_url this module computes.
#
# Mirrors the app/core/currency.py pattern (curated set + validators).

from urllib.parse import quote, urlparse

# A handle is a username / cashtag / VPA / IBAN — never a free-form paragraph.
MAX_HANDLE_LENGTH = 255
# A short human label, mainly for the custom path ("Wise", "My bank").
MAX_LABEL_LENGTH = 50
# Registering more than this many handles is almost certainly a mistake; the
# settle UI only ever shows a handful.
MAX_METHODS_PER_USER = 12

# provider code -> human name. "custom" is the escape hatch: any handle or a
# full https link the user pastes.
PAYMENT_PROVIDERS: dict[str, str] = {
    "venmo": "Venmo",
    "paypal": "PayPal.Me",
    "cashapp": "Cash App",
    "revolut": "Revolut",
    "upi": "UPI",
    "iban": "Bank transfer (IBAN)",
    "custom": "Other",
}


def is_supported_provider(code: str) -> bool:
    """True if `code` is a known payment-provider code."""
    return code in PAYMENT_PROVIDERS


def provider_name(code: str) -> str:
    """Display name for a provider code (falls back to the code itself)."""
    return PAYMENT_PROVIDERS.get(code, code)


def _is_safe_http_url(value: str) -> bool:
    """Only http(s) URLs may be rendered as a link (blocks javascript: etc.).

    The custom handle is rendered as an <a href> on the frontend, so a
    `javascript:`/`data:` payload here would be a stored-XSS vector. Restrict
    to http/https with a host.
    """
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def build_pay_url(provider: str, handle: str) -> str | None:
    """Turn a stored (provider, handle) into a tappable deep link, or None.

    None means "copy only" — the UI shows the handle with a Copy button but no
    link (IBANs and plain-text custom handles have no URL scheme). Handles are
    URL-encoded so a stray character can't break out of the path; the custom
    path only echoes a link the user pasted after validating its scheme, so no
    `javascript:` payload can ride through to an href.
    """
    h = handle.strip()
    if not h:
        return None

    if provider == "venmo":
        return f"https://venmo.com/u/{quote(h.lstrip('@'), safe='')}"
    if provider == "paypal":
        return f"https://paypal.me/{quote(h.lstrip('@'), safe='')}"
    if provider == "cashapp":
        return f"https://cash.app/${quote(h.lstrip('$'), safe='')}"
    if provider == "revolut":
        return f"https://revolut.me/{quote(h.lstrip('@'), safe='')}"
    if provider == "upi":
        # UPI deep link (opens the payer's UPI app on mobile; harmless no-op on
        # desktop, where the Copy button is the real path). pa = payee address.
        return f"upi://pay?pa={quote(h, safe='')}"
    if provider == "custom":
        # Frictionless: a pasted https link becomes a button; anything else is
        # copy-only.
        return h if _is_safe_http_url(h) else None
    # iban and unknowns: copy-only.
    return None

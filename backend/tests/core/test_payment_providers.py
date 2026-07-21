"""WS10.2 — payment-provider registry unit tests.

The registry is the single source of truth for valid provider codes and for
turning a stored handle into a tappable deep link. The security-critical case
is the custom path: it must never echo a non-http(s) URL into what the frontend
renders as an href.
"""
from app.core.payment_providers import (
    build_pay_url,
    is_supported_provider,
    provider_name,
)


def test_known_providers_supported():
    for code in ("venmo", "paypal", "cashapp", "revolut", "upi", "iban", "custom"):
        assert is_supported_provider(code)


def test_unknown_provider_not_supported():
    assert not is_supported_provider("bitcoin")
    assert not is_supported_provider("")


def test_provider_name_falls_back_to_code():
    assert provider_name("venmo") == "Venmo"
    assert provider_name("unknown") == "unknown"


def test_venmo_strips_leading_at():
    assert build_pay_url("venmo", "@alice") == "https://venmo.com/u/alice"
    assert build_pay_url("venmo", "alice") == "https://venmo.com/u/alice"


def test_cashapp_prefixes_dollar():
    assert build_pay_url("cashapp", "$bob") == "https://cash.app/$bob"
    assert build_pay_url("cashapp", "bob") == "https://cash.app/$bob"


def test_paypal_and_revolut():
    assert build_pay_url("paypal", "carol") == "https://paypal.me/carol"
    assert build_pay_url("revolut", "@dave") == "https://revolut.me/dave"


def test_upi_uses_deep_link_scheme():
    assert build_pay_url("upi", "alice@okbank") == "upi://pay?pa=alice%40okbank"


def test_iban_is_copy_only():
    assert build_pay_url("iban", "GB33BUKB20201555555555") is None


def test_custom_https_url_passes_through():
    url = "https://wise.com/pay/me/alice"
    assert build_pay_url("custom", url) == url


def test_custom_plain_text_is_copy_only():
    assert build_pay_url("custom", "ask me for details") is None


def test_custom_rejects_dangerous_scheme():
    # A javascript:/data: payload must NOT become an href (stored-XSS guard).
    assert build_pay_url("custom", "javascript:alert(1)") is None
    assert build_pay_url("custom", "data:text/html,<script>1</script>") is None


def test_handle_is_url_encoded():
    # A stray slash/space cannot break out of the URL path.
    assert build_pay_url("venmo", "a b/c") == "https://venmo.com/u/a%20b%2Fc"


def test_blank_handle_returns_none():
    assert build_pay_url("venmo", "   ") is None

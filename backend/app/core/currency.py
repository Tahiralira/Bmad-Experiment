# Currency support (WS10.1) — ClearDues is a GLOBAL product: currency is a
# per-group setting, never hardcoded to one market (CLAUDE.md ground rule #8).
#
# We validate against a curated set of major ISO-4217 codes rather than the full
# ~180-code table: it covers the overwhelming majority of real usage, keeps
# garbage out of the column, and stays market-neutral. Frontend formatting uses
# Intl.NumberFormat, which knows each currency's own decimal rules (JPY/KRW have
# none), so the display layer is correct for any code the backend accepts.

DEFAULT_CURRENCY = "USD"

# code -> human name. Kept alphabetical by region groups for scanability.
SUPPORTED_CURRENCIES: dict[str, str] = {
    # Americas
    "USD": "US Dollar",
    "CAD": "Canadian Dollar",
    "MXN": "Mexican Peso",
    "BRL": "Brazilian Real",
    "ARS": "Argentine Peso",
    "CLP": "Chilean Peso",
    "COP": "Colombian Peso",
    # Europe
    "EUR": "Euro",
    "GBP": "British Pound",
    "CHF": "Swiss Franc",
    "SEK": "Swedish Krona",
    "NOK": "Norwegian Krone",
    "DKK": "Danish Krone",
    "PLN": "Polish Zloty",
    "CZK": "Czech Koruna",
    "HUF": "Hungarian Forint",
    "RON": "Romanian Leu",
    "TRY": "Turkish Lira",
    "RUB": "Russian Ruble",
    "UAH": "Ukrainian Hryvnia",
    # Middle East & Africa
    "AED": "UAE Dirham",
    "SAR": "Saudi Riyal",
    "QAR": "Qatari Riyal",
    "ILS": "Israeli New Shekel",
    "EGP": "Egyptian Pound",
    "ZAR": "South African Rand",
    "NGN": "Nigerian Naira",
    "KES": "Kenyan Shilling",
    "GHS": "Ghanaian Cedi",
    # Asia-Pacific
    "INR": "Indian Rupee",
    "PKR": "Pakistani Rupee",
    "BDT": "Bangladeshi Taka",
    "LKR": "Sri Lankan Rupee",
    "NPR": "Nepalese Rupee",
    "CNY": "Chinese Yuan",
    "JPY": "Japanese Yen",
    "KRW": "South Korean Won",
    "HKD": "Hong Kong Dollar",
    "TWD": "New Taiwan Dollar",
    "SGD": "Singapore Dollar",
    "MYR": "Malaysian Ringgit",
    "THB": "Thai Baht",
    "IDR": "Indonesian Rupiah",
    "PHP": "Philippine Peso",
    "VND": "Vietnamese Dong",
    "AUD": "Australian Dollar",
    "NZD": "New Zealand Dollar",
}


def is_supported_currency(code: str) -> bool:
    """True if `code` is an accepted ISO-4217 currency code."""
    return code in SUPPORTED_CURRENCIES


def normalize_currency(code: str | None) -> str:
    """Uppercase + validate a currency code, falling back to the default.

    Used when reading possibly-legacy/empty settings rows; never raises.
    """
    if not code:
        return DEFAULT_CURRENCY
    upper = code.upper()
    return upper if is_supported_currency(upper) else DEFAULT_CURRENCY

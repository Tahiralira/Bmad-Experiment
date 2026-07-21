// Currency formatting (WS10.1) — ClearDues is a GLOBAL product: amounts are
// denominated in each group's own ISO-4217 currency, never a hardcoded "Rs".
// Intl.NumberFormat knows every currency's own decimal rules (JPY/KRW have
// none, most have two), so we never hardcode fraction digits.

export const DEFAULT_CURRENCY = "USD"

/** Supported ISO-4217 codes — mirrors backend app/core/currency.py. Used to
 * build the currency pickers (create-group + group settings). */
export const SUPPORTED_CURRENCIES: ReadonlyArray<{ code: string; name: string }> =
  [
    { code: "USD", name: "US Dollar" },
    { code: "EUR", name: "Euro" },
    { code: "GBP", name: "British Pound" },
    { code: "CAD", name: "Canadian Dollar" },
    { code: "AUD", name: "Australian Dollar" },
    { code: "NZD", name: "New Zealand Dollar" },
    { code: "CHF", name: "Swiss Franc" },
    { code: "SEK", name: "Swedish Krona" },
    { code: "NOK", name: "Norwegian Krone" },
    { code: "DKK", name: "Danish Krone" },
    { code: "PLN", name: "Polish Zloty" },
    { code: "CZK", name: "Czech Koruna" },
    { code: "HUF", name: "Hungarian Forint" },
    { code: "RON", name: "Romanian Leu" },
    { code: "TRY", name: "Turkish Lira" },
    { code: "RUB", name: "Russian Ruble" },
    { code: "UAH", name: "Ukrainian Hryvnia" },
    { code: "MXN", name: "Mexican Peso" },
    { code: "BRL", name: "Brazilian Real" },
    { code: "ARS", name: "Argentine Peso" },
    { code: "CLP", name: "Chilean Peso" },
    { code: "COP", name: "Colombian Peso" },
    { code: "AED", name: "UAE Dirham" },
    { code: "SAR", name: "Saudi Riyal" },
    { code: "QAR", name: "Qatari Riyal" },
    { code: "ILS", name: "Israeli New Shekel" },
    { code: "EGP", name: "Egyptian Pound" },
    { code: "ZAR", name: "South African Rand" },
    { code: "NGN", name: "Nigerian Naira" },
    { code: "KES", name: "Kenyan Shilling" },
    { code: "GHS", name: "Ghanaian Cedi" },
    { code: "INR", name: "Indian Rupee" },
    { code: "PKR", name: "Pakistani Rupee" },
    { code: "BDT", name: "Bangladeshi Taka" },
    { code: "LKR", name: "Sri Lankan Rupee" },
    { code: "NPR", name: "Nepalese Rupee" },
    { code: "CNY", name: "Chinese Yuan" },
    { code: "JPY", name: "Japanese Yen" },
    { code: "KRW", name: "South Korean Won" },
    { code: "HKD", name: "Hong Kong Dollar" },
    { code: "TWD", name: "New Taiwan Dollar" },
    { code: "SGD", name: "Singapore Dollar" },
    { code: "MYR", name: "Malaysian Ringgit" },
    { code: "THB", name: "Thai Baht" },
    { code: "IDR", name: "Indonesian Rupiah" },
    { code: "PHP", name: "Philippine Peso" },
    { code: "VND", name: "Vietnamese Dong" },
  ]

const SUPPORTED_CODES = new Set(SUPPORTED_CURRENCIES.map((c) => c.code))

export interface FormatCurrencyOptions {
  /** When true, keep the sign (e.g. "-$5.00"); default false renders the
   * absolute value (direction is carried by a label in the UI). */
  signed?: boolean
  /** Override the locale used for grouping/symbol placement. Defaults to the
   * browser locale. */
  locale?: string
}

/**
 * Format a monetary amount in the given ISO-4217 currency.
 *
 * `amount` may be a Decimal STRING off the wire (e.g. "50.00") or a number.
 * Never throws in render: an unknown currency falls back to the default, and
 * a non-finite amount renders as zero.
 */
export function formatCurrency(
  amount: string | number,
  currency: string = DEFAULT_CURRENCY,
  options: FormatCurrencyOptions = {},
): string {
  const { signed = false, locale } = options
  const raw = typeof amount === "string" ? Number(amount) : amount
  const finite = Number.isFinite(raw) ? raw : 0
  const value = signed ? finite : Math.abs(finite)
  const code = SUPPORTED_CODES.has(currency) ? currency : DEFAULT_CURRENCY

  try {
    return new Intl.NumberFormat(locale, {
      style: "currency",
      currency: code,
    }).format(value)
  } catch {
    // Defensive: a runtime without the currency's data — fall back to default.
    return new Intl.NumberFormat(locale, {
      style: "currency",
      currency: DEFAULT_CURRENCY,
    }).format(value)
  }
}

/**
 * The currency's symbol ("$", "₹", "€", "kr", …) for a given ISO-4217 code,
 * for compact contexts like an input-field prefix. Falls back to the code
 * itself if a symbol can't be resolved.
 */
export function getCurrencySymbol(
  currency: string = DEFAULT_CURRENCY,
  locale?: string,
): string {
  const code = SUPPORTED_CODES.has(currency) ? currency : DEFAULT_CURRENCY
  try {
    const parts = new Intl.NumberFormat(locale, {
      style: "currency",
      currency: code,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).formatToParts(0)
    return parts.find((p) => p.type === "currency")?.value ?? code
  } catch {
    return code
  }
}

// Region -> currency for the common markets. There is no Intl API for
// "locale's currency", so we map the region subtag of navigator.language.
const REGION_CURRENCY: Record<string, string> = {
  US: "USD", CA: "CAD", MX: "MXN", BR: "BRL", AR: "ARS", CL: "CLP", CO: "COP",
  GB: "GBP", IE: "EUR", FR: "EUR", DE: "EUR", ES: "EUR", IT: "EUR", NL: "EUR",
  PT: "EUR", GR: "EUR", AT: "EUR", BE: "EUR", FI: "EUR",
  CH: "CHF", SE: "SEK", NO: "NOK", DK: "DKK", PL: "PLN", CZ: "CZK", HU: "HUF",
  RO: "RON", TR: "TRY", RU: "RUB", UA: "UAH",
  AE: "AED", SA: "SAR", QA: "QAR", IL: "ILS", EG: "EGP", ZA: "ZAR", NG: "NGN",
  KE: "KES", GH: "GHS",
  IN: "INR", PK: "PKR", BD: "BDT", LK: "LKR", NP: "NPR", CN: "CNY", JP: "JPY",
  KR: "KRW", HK: "HKD", TW: "TWD", SG: "SGD", MY: "MYR", TH: "THB", ID: "IDR",
  PH: "PHP", VN: "VND", AU: "AUD", NZ: "NZD",
}

/** Best-effort currency guess from the browser locale (for the create-group
 * default). Falls back to the global default. Never throws. */
export function guessLocaleCurrency(): string {
  try {
    const locale =
      (typeof navigator !== "undefined" && navigator.language) || "en-US"
    // e.g. "en-IN" -> "IN", "pt-BR" -> "BR"
    const region = new Intl.Locale(locale).maximize().region
    const guess = region ? REGION_CURRENCY[region] : undefined
    return guess && SUPPORTED_CODES.has(guess) ? guess : DEFAULT_CURRENCY
  } catch {
    return DEFAULT_CURRENCY
  }
}

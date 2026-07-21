// Payment providers (WS10.2) — presentation metadata for the handle editor.
//
// ClearDues is GLOBAL: instead of one payment rail, a user registers the
// handles they already have and we surface them when someone owes them money.
// This mirror holds ONLY display metadata (names, input placeholders). The
// deep-link URL is computed server-side and arrives as `pay_url` — never
// duplicate that logic here. Codes must stay in sync with the backend
// app/core/payment_providers.py registry.

export interface PaymentProviderMeta {
  code: string
  name: string
  /** Placeholder for the handle input. */
  placeholder: string
  /** Whether this provider yields a tappable deep link (informational only —
   * the backend decides the actual pay_url). */
  deepLink: boolean
  /** Optional one-line hint under the input. */
  hint?: string
}

export const PAYMENT_PROVIDERS: ReadonlyArray<PaymentProviderMeta> = [
  { code: "venmo", name: "Venmo", placeholder: "@username", deepLink: true },
  { code: "paypal", name: "PayPal.Me", placeholder: "username", deepLink: true },
  { code: "cashapp", name: "Cash App", placeholder: "$cashtag", deepLink: true },
  { code: "revolut", name: "Revolut", placeholder: "@username", deepLink: true },
  {
    code: "upi",
    name: "UPI",
    placeholder: "name@bank",
    deepLink: true,
    hint: "Opens the payer's UPI app on mobile.",
  },
  {
    code: "iban",
    name: "Bank transfer (IBAN)",
    placeholder: "IBAN or account number",
    deepLink: false,
    hint: "Shown for the payer to copy.",
  },
  {
    code: "custom",
    name: "Other",
    placeholder: "@handle or https://…",
    deepLink: false,
    hint: "Paste a payment link (becomes a button) or any handle to copy.",
  },
]

const BY_CODE = new Map(PAYMENT_PROVIDERS.map((p) => [p.code, p]))

export function getPaymentProvider(
  code: string,
): PaymentProviderMeta | undefined {
  return BY_CODE.get(code)
}

/** Display name for a provider code (falls back to the code itself). */
export function paymentProviderName(code: string): string {
  return BY_CODE.get(code)?.name ?? code
}

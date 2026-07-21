import { describe, it, expect } from "vitest"

import {
  getPaymentProvider,
  PAYMENT_PROVIDERS,
  paymentProviderName,
} from "./payment-providers"

describe("payment-providers registry", () => {
  it("covers the providers WS10.2 requires", () => {
    const codes = PAYMENT_PROVIDERS.map((p) => p.code)
    expect(codes).toEqual(
      expect.arrayContaining([
        "venmo",
        "paypal",
        "cashapp",
        "revolut",
        "upi",
        "iban",
        "custom",
      ]),
    )
  })

  it("looks up a provider's presentation metadata", () => {
    const venmo = getPaymentProvider("venmo")
    expect(venmo?.name).toBe("Venmo")
    expect(venmo?.placeholder).toBe("@username")
    expect(getPaymentProvider("bitcoin")).toBeUndefined()
  })

  it("falls back to the code for an unknown provider name", () => {
    expect(paymentProviderName("paypal")).toBe("PayPal.Me")
    expect(paymentProviderName("mystery")).toBe("mystery")
  })

  it("marks copy-only providers as non-deep-link", () => {
    expect(getPaymentProvider("iban")?.deepLink).toBe(false)
    expect(getPaymentProvider("venmo")?.deepLink).toBe(true)
  })
})

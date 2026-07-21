import { describe, it, expect } from "vitest"

import {
  DEFAULT_CURRENCY,
  SUPPORTED_CURRENCIES,
  formatCurrency,
  getCurrencySymbol,
} from "./currency"

// Assertions pin an explicit en-US locale so they don't depend on the CI
// runtime's default locale.
const L = { locale: "en-US" }

describe("formatCurrency", () => {
  it("formats a decimal-string amount in the given currency", () => {
    expect(formatCurrency("50.00", "USD", L)).toBe("$50.00")
    expect(formatCurrency("1234.5", "INR", L)).toBe("₹1,234.50")
    expect(formatCurrency("50", "EUR", L)).toBe("€50.00")
  })

  it("defaults to USD when no currency is given", () => {
    expect(formatCurrency("10", undefined, L)).toBe("$10.00")
    expect(DEFAULT_CURRENCY).toBe("USD")
  })

  it("renders the absolute value by default and keeps the sign when asked", () => {
    expect(formatCurrency(-5, "USD", L)).toBe("$5.00")
    expect(formatCurrency(-5, "USD", { ...L, signed: true })).toBe("-$5.00")
  })

  it("respects a currency's own decimal rules (JPY has none)", () => {
    expect(formatCurrency("600", "JPY", L)).toBe("¥600")
  })

  it("falls back to the default on an unknown code instead of throwing", () => {
    expect(formatCurrency("10", "XYZ", L)).toBe("$10.00")
  })

  it("renders a non-finite amount as zero", () => {
    expect(formatCurrency(Number.NaN, "USD", L)).toBe("$0.00")
  })
})

describe("getCurrencySymbol", () => {
  it("returns the symbol for a code", () => {
    expect(getCurrencySymbol("USD", "en-US")).toBe("$")
    expect(getCurrencySymbol("INR", "en-US")).toBe("₹")
  })
})

describe("SUPPORTED_CURRENCIES", () => {
  it("covers major global currencies", () => {
    const codes = SUPPORTED_CURRENCIES.map((c) => c.code)
    expect(codes).toContain("USD")
    expect(codes).toContain("EUR")
    expect(codes).toContain("INR")
    expect(codes).toContain("JPY")
  })
})

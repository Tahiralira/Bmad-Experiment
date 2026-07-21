// Currency context (WS10.1) — provides the active group's ISO-4217 currency to
// a subtree so deep money-rendering components (ledger rows, settle cards,
// activity feed) format correctly without threading a `currency` prop through
// every layer. Group-scoped screens (GroupLedgerScreen, SmartInputModal) wrap
// their subtree in <CurrencyProvider>; genuinely cross-group surfaces
// (dashboard rows, /pending cards) pass a per-item currency to formatCurrency
// directly instead.
import { createContext, useContext, type ReactNode } from "react"

import { DEFAULT_CURRENCY } from "./currency"

const CurrencyContext = createContext<string>(DEFAULT_CURRENCY)

export function CurrencyProvider({
  currency,
  children,
}: {
  currency: string | undefined
  children: ReactNode
}) {
  return (
    <CurrencyContext.Provider value={currency || DEFAULT_CURRENCY}>
      {children}
    </CurrencyContext.Provider>
  )
}

/** The active group's currency. Defaults to the global default outside a
 * provider (isolated component tests, cross-group screens). */
export function useCurrency(): string {
  return useContext(CurrencyContext)
}

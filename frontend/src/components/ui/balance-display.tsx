import { useMemo } from "react"

import { formatCurrency } from "@/lib/currency"
import { useCurrency } from "@/lib/currency-context"
import { cn } from "@/lib/utils"

/**
 * Size variants for different display contexts
 */
export type BalanceDisplayVariant = "display" | "title" | "body"

/**
 * Props for the BalanceDisplay component
 */
export interface BalanceDisplayProps {
  /**
   * The monetary amount to display (can be positive or negative)
   * Negative numbers indicate debt/owe, positive indicate credit/owed
   */
  amount: number

  /**
   * Size variant for different contexts
   * - display: 28px - dashboard balance hero
   * - title: 20px - card/row amounts
   * - body: 15px - inline amounts
   */
  variant?: BalanceDisplayVariant

  /**
   * Optional context label ("You owe" / "You're owed").
   * When present, the label carries direction and the amount renders UNSIGNED —
   * amounts are neutral facts (design v2 constitution; v1 UX-L2).
   */
  contextLabel?: string

  /**
   * Optional description for screen reader context
   * Example: "to Sam" → "You owe 450 rupees to Sam"
   */
  contextDescription?: string

  /**
   * ISO-4217 currency code (WS10.1). Defaults to the active group's currency
   * from CurrencyContext; pass explicitly on cross-group surfaces (dashboard
   * rows) where each item has its own currency.
   */
  currency?: string

  /**
   * Custom className for additional styling
   */
  className?: string
}

/**
 * Variant-specific typography classes (design v2 type scale)
 */
const variantClasses: Record<BalanceDisplayVariant, string> = {
  display: "text-display font-semibold",
  title: "text-title font-semibold",
  body: "text-body font-normal",
}

/**
 * BalanceDisplay component
 *
 * Displays monetary amounts in a consistent, neutral format.
 * Never uses red/green colors for debt - money is fact, not judgment.
 */
export function BalanceDisplay({
  amount,
  variant = "body",
  contextLabel,
  contextDescription,
  currency,
  className,
}: BalanceDisplayProps) {
  const contextCurrency = useCurrency()
  const activeCurrency = currency ?? contextCurrency

  // With a direction label, the amount is an unsigned neutral fact.
  const formattedAmount = useMemo(
    () => formatCurrency(amount, activeCurrency, { signed: !contextLabel }),
    [amount, activeCurrency, contextLabel],
  )

  // Full sentence for screen readers; the visual spans are hidden from AT so
  // nothing is announced twice (v1 UX-L3).
  const srText = useMemo(() => {
    const amountText = formatCurrency(amount, activeCurrency)
    const direction = amount < 0 ? "owe" : "are owed"

    if (contextDescription) {
      return `You ${direction} ${amountText} ${contextDescription}`
    }
    if (contextLabel) {
      return `${contextLabel} ${amountText}`
    }
    return amountText
  }, [amount, activeCurrency, contextLabel, contextDescription])

  const showLabelAbove = variant === "display" || variant === "title"

  return (
    <div className={cn("flex flex-col", className)}>
      <span className="sr-only">{srText}</span>

      {contextLabel && showLabelAbove && (
        <span
          className="text-text-secondary text-body-small font-normal mb-1"
          aria-hidden="true"
        >
          {contextLabel}
        </span>
      )}

      <span
        className={cn(
          variantClasses[variant],
          // Neutral ink, tabular figures (design v2: tabular-nums mandatory on amounts)
          "text-text-primary tabular-nums tracking-tight",
        )}
        aria-hidden="true"
      >
        {contextLabel && variant === "body" && (
          <span className="text-text-secondary font-normal mr-1">
            {contextLabel}
          </span>
        )}
        {formattedAmount}
      </span>
    </div>
  )
}

export default BalanceDisplay

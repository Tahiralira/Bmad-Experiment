import { useMemo } from "react"

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
   * Custom className for additional styling
   */
  className?: string
}

/**
 * Currency formatter with "Rs" prefix.
 * NOTE: hardcoded currency is a known WS10 item (per-group currency + formatCurrency
 * util). Do not fix here — WS3 is visual only.
 */
function formatCurrency(amount: number, signed: boolean): string {
  const absAmount = amount === 0 ? 0 : Math.abs(amount)

  const hasDecimals = absAmount % 1 !== 0
  const fractionDigits = hasDecimals ? 2 : 0

  const formatter = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  })

  let formatted = formatter.format(absAmount).replace("₹", "Rs ")

  if (signed && amount < 0) {
    formatted = `-${formatted}`
  }

  return formatted
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
  className,
}: BalanceDisplayProps) {
  // With a direction label, the amount is an unsigned neutral fact.
  const formattedAmount = useMemo(
    () => formatCurrency(amount, !contextLabel),
    [amount, contextLabel],
  )

  // Full sentence for screen readers; the visual spans are hidden from AT so
  // nothing is announced twice (v1 UX-L3).
  const srText = useMemo(() => {
    const amountText = `${Math.abs(amount)} rupees`
    const direction = amount < 0 ? "owe" : "are owed"

    if (contextDescription) {
      return `You ${direction} ${amountText} ${contextDescription}`
    }
    if (contextLabel) {
      return `${contextLabel} ${amountText}`
    }
    return amountText
  }, [amount, contextLabel, contextDescription])

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

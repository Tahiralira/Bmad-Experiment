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
   * - display: 32px - For dashboard balances, large numbers
   * - title: 24px - For card titles, section headers
   * - body: 16px - For inline amounts, list items
   */
  variant?: BalanceDisplayVariant

  /**
   * Optional context label ("You owe" / "You're owed")
   * Displayed above (display/title) or inline (body variant)
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
 * Currency formatter for Indian Rupees with "Rs" prefix
 * Handles comma separators for thousands, lakhs, crores
 * Shows decimals only for amounts with paise (e.g., Rs 100.50)
 */
function formatCurrency(amount: number): string {
  // Handle zero edge case (JavaScript has both 0 and -0)
  const absAmount = amount === 0 ? 0 : Math.abs(amount)

  // Show decimals only if amount has paise
  const hasDecimals = absAmount % 1 !== 0
  const fractionDigits = hasDecimals ? 2 : 0

  // Use Intl.NumberFormat for proper Indian locale formatting
  const formatter = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  })

  // Get formatted string (will be "₹1,500" or "₹100.50")
  let formatted = formatter.format(absAmount)

  // Replace ₹ symbol with "Rs" prefix (ClearDues brand standard)
  formatted = formatted.replace("₹", "Rs ")

  // Add negative sign if needed (format: "-Rs 450")
  if (amount < 0) {
    formatted = `-${formatted}`
  }

  return formatted // "Rs 1,500", "-Rs 450", or "Rs 100.50"
}

/**
 * Variant-specific typography classes
 * Based on ClearDues design system tokens
 */
const variantClasses: Record<BalanceDisplayVariant, string> = {
  display: "text-[32px] font-medium leading-tight", // 32px, Medium, 1.2
  title: "text-[24px] font-medium leading-snug", // 24px, Medium, 1.3
  body: "text-base font-normal leading-normal", // 16px, Regular, 1.5
}

/**
 * BalanceDisplay component
 *
 * Displays monetary amounts in a consistent, neutral format.
 * Never uses red/green colors for debt - money is fact, not judgment.
 *
 * @example
 * ```tsx
 * // Dashboard large balance
 * <BalanceDisplay
 *   amount={1500}
 *   variant="display"
 *   contextLabel="Total balance across all groups"
 * />
 *
 * // Group card balance (debt)
 * <BalanceDisplay
 *   amount={-450}
 *   variant="title"
 *   contextLabel="You owe"
 *   contextDescription="to Weekend Trip group"
 * />
 *
 * // Inline expense amount
 * <BalanceDisplay
 *   amount={375}
 *   variant="body"
 * />
 * ```
 */
export function BalanceDisplay({
  amount,
  variant = "body",
  contextLabel,
  contextDescription,
  className,
}: BalanceDisplayProps) {
  // Format the currency amount
  const formattedAmount = useMemo(() => formatCurrency(amount), [amount])

  // Build full context for screen readers
  const ariaLabel = useMemo(() => {
    const amountText = `${Math.abs(amount)} rupees`
    const direction = amount < 0 ? "owe" : "are owed"

    if (contextDescription) {
      // "You owe 450 rupees to Sam"
      return `You ${direction} ${amountText} ${contextDescription}`
    } else if (contextLabel) {
      // "You owe 450 rupees"
      return `${contextLabel} ${amountText}`
    } else {
      // "450 rupees"
      return amountText
    }
  }, [amount, contextLabel, contextDescription])

  // Determine label position based on variant
  const showLabelAbove = variant === "display" || variant === "title"

  return (
    <div className={cn("flex flex-col", className)}>
      {/* Optional context label - above amount for display/title, inline for body */}
      {contextLabel && showLabelAbove && (
        <span
          className="text-text-secondary text-sm font-normal mb-1"
          aria-hidden="true"
        >
          {contextLabel}
        </span>
      )}

      {/* Amount display with accessibility */}
      <span
        className={cn(
          // Variant-specific typography
          variantClasses[variant],
          // Amount styling - neutral color strategy (CRITICAL: never red/green)
          // Use proportional-nums for natural number flow (not tabular)
          "text-text-primary proportional-nums tracking-tight"
        )}
        aria-label={ariaLabel}
        role="text"
      >
        {/* Inline context label for body variant */}
        {contextLabel && variant === "body" && (
          <span className="text-text-secondary mr-1" aria-hidden="true">
            {contextLabel}
          </span>
        )}
        {formattedAmount}
      </span>
    </div>
  )
}

export default BalanceDisplay

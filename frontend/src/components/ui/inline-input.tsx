import { useState } from "react"
import { RotateCcw } from "lucide-react"
import * as TooltipPrimitive from "@radix-ui/react-tooltip"

import { getCurrencySymbol } from "@/lib/currency"
import { useCurrency } from "@/lib/currency-context"
import { cn } from "@/lib/utils"
import { BalanceDisplay } from "./balance-display"

interface InlineEditableFieldProps {
  /** Field label */
  label: string
  /** Current value */
  value: string | number
  /** Change handler */
  onChange: (value: string | number) => void
  /** Reset handler (revert to original) */
  onReset: () => void
  /** Whether field has been edited */
  isEdited: boolean
  /** Original AI-suggested value */
  originalValue: string | number
  /** Field type */
  type: "text" | "currency"
  /** Validation errors to display */
  errors?: string[]
  /** Additional className */
  className?: string
  /** Input name attribute */
  name?: string
}

/**
 * Inline Editable Field - A form field that shows edit state and provides reset functionality.
 *
 * Features:
 * - Visual highlight when edited (subtle success background tint)
 * - Reset button to revert to AI suggestion
 * - Tooltip showing original AI value when edited
 * - Currency formatting for amount fields
 * - Inline validation errors
 *
 * @example
 * ```tsx
 * <InlineEditableField
 *   label="Amount"
 *   value={editedData.amount}
 *   onChange={(value) => handleChange('amount', value)}
 *   onReset={() => handleReset('amount')}
 *   isEdited={editedFields.has('amount')}
 *   originalValue={parsedData.amount}
 *   type="currency"
 *   errors={validationErrors.amount}
 * />
 * ```
 */
export function InlineEditableField({
  label,
  value,
  onChange,
  onReset,
  isEdited,
  originalValue,
  type,
  errors,
  className,
  name,
}: InlineEditableFieldProps) {
  const [isFocused, setIsFocused] = useState(false)
  const currency = useCurrency()

  return (
    <div
      className={cn(
        "inline-field relative rounded-md border p-3",
        "transition-colors duration-200",
        isEdited
          ? "border-action bg-success-subtle"
          : isFocused
            ? "border-action bg-surface"
            : "border-border bg-surface",
        className
      )}
    >
      {/* Label */}
      <label
        htmlFor={name}
        className="block text-xs font-medium text-text-secondary mb-1"
      >
        {label}
      </label>

      {/* Input wrapper */}
      <div className="flex items-center gap-2">
        {type === "currency" ? (
          // Currency input with BalanceDisplay formatting
          <div className="flex-1 flex items-center">
            <span className="text-text-muted mr-1">
              {getCurrencySymbol(currency)}
            </span>
            <input
              id={name}
              name={name}
              type="number"
              step="0.01"
              min="0"
              max="999999.99"
              value={value}
              onChange={(e) => {
                // Convert string to number for currency inputs to maintain type consistency
                const numValue = parseFloat(e.target.value)
                onChange(isNaN(numValue) ? "" : numValue)
              }}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              className={cn(
                "flex-1 bg-transparent outline-none",
                "text-text-primary font-medium proportional-nums",
                "placeholder:text-text-muted",
                "focus:outline-none"
              )}
              aria-label={label}
            />
          </div>
        ) : (
          // Text input
          <input
            id={name}
            name={name}
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            className={cn(
              "flex-1 bg-transparent outline-none",
              "text-text-primary",
              "placeholder:text-text-muted",
              "focus:outline-none"
            )}
            aria-label={label}
          />
        )}

        {/* Reset button - only show when edited */}
        {isEdited && (
          <TooltipPrimitive.Root>
            <TooltipPrimitive.Trigger asChild>
              <button
                type="button"
                onClick={onReset}
                className={cn(
                  "flex-shrink-0 p-1 rounded-md",
                  "text-text-secondary hover:text-text-primary",
                  "hover:bg-surface-elevated",
                  "transition-colors duration-150",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-action"
                )}
                aria-label={`Reset ${label} to AI suggestion`}
              >
                <RotateCcw className="size-4" />
              </button>
            </TooltipPrimitive.Trigger>
            <TooltipPrimitive.Portal>
              <TooltipPrimitive.Content
                side="top"
                align="center"
                className={cn(
                  "px-2 py-1 rounded-md",
                  "bg-surface-elevated border border-border",
                  "text-xs text-text-primary",
                  "shadow-md",
                  "max-w-[200px]"
                )}
              >
                Reset to AI suggestion
              </TooltipPrimitive.Content>
            </TooltipPrimitive.Portal>
          </TooltipPrimitive.Root>
        )}
      </div>

      {/* Validation errors */}
      {errors && errors.length > 0 && (
        <div className="mt-1 space-y-0.5">
          {errors.map((error, index) => (
            <p key={index} className="text-xs text-error">
              {error}
            </p>
          ))}
        </div>
      )}

      {/* Original value tooltip - only show when edited */}
      {isEdited && (
        <div className="mt-1.5 text-xs text-text-muted flex items-center gap-1">
          <span>AI suggested:</span>
          <span className="font-medium text-text-secondary">
            {type === "currency" ? (
              <BalanceDisplay amount={Number(originalValue)} />
            ) : (
              originalValue
            )}
          </span>
        </div>
      )}
    </div>
  )
}

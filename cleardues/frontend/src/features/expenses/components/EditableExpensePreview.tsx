import { useEffect, useState } from "react"
import { motion, useReducedMotion } from "framer-motion"
import * as SelectPrimitive from "@radix-ui/react-select"
import { Check, ChevronDown } from "lucide-react"

import { cn } from "@/lib/utils"
import { InlineEditableField } from "@/components/ui/inline-input"
import { useExpenseEdit } from "../hooks/useExpenseEdit"
import { useAutoConfirm } from "../hooks/useAutoConfirm"
import { useGroupMembers } from "@/features/groups/api/groups"
import type { ExpenseParseResponse, ExpenseCreate } from "../types"

interface EditableExpensePreviewProps {
  /** Parsed expense data from AI */
  parsedData: ExpenseParseResponse
  /** Called when expense is confirmed/saved */
  onConfirm: (editedData: ExpenseCreate) => Promise<void>
  /** Called when user discards the expense */
  onDiscard: () => void
  /** Group ID for fetching members */
  groupId: string
  /** Auto-confirm enabled preference (default: false) */
  autoConfirmEnabled?: boolean
  /** Additional className */
  className?: string
}

/**
 * Editable Expense Preview - Allows users to review and edit AI-parsed expenses.
 *
 * Features:
 * - Inline editing for amount, description, payer
 * - Change tracking with visual highlights
 * - Reset to AI suggestion per field
 * - Zod validation with inline errors
 * - Auto-confirm countdown (if enabled)
 * - Confirm/Discard actions
 * - Payer selection from group members
 *
 * @example
 * ```tsx
 * <EditableExpensePreview
 *   parsedData={parsedData}
 *   onConfirm={handleConfirm}
 *   onDiscard={handleDiscard}
 *   groupId="group-123"
 *   currentUserId="user-123"
 *   autoConfirmEnabled={false}
 * />
 * ```
 */
export function EditableExpensePreview({
  parsedData,
  onConfirm,
  onDiscard,
  groupId,
  autoConfirmEnabled = false,
  className,
}: EditableExpensePreviewProps) {
  const shouldReduceMotion = useReducedMotion()

  // Edit state management
  const {
    editedData,
    editedFields,
    handleChange,
    handleReset,
    isEdited,
    isValid,
    validationErrors,
  } = useExpenseEdit(parsedData)

  // Auto-confirm countdown
  const { countdown, isCountingDown, startCountdown, cancelCountdown } =
    useAutoConfirm({
      enabled: autoConfirmEnabled,
      duration: 3000,
      onCountdownComplete: () => handleConfirm(),
    })

  // Fetch group members for payer selection
  const { data: membersData, isLoading: isLoadingMembers } = useGroupMembers(groupId)
  const members = membersData?.members || []

  // Local state for tracking user interaction
  const [hasInteracted, setHasInteracted] = useState(false)

  // Start countdown on mount (if enabled)
  useEffect(() => {
    if (autoConfirmEnabled && !hasInteracted) {
      startCountdown()
    }
  }, [autoConfirmEnabled, hasInteracted, startCountdown])

  // Cancel countdown and mark interacted on any user action
  const handleUserInteraction = () => {
    if (!hasInteracted) {
      setHasInteracted(true)
      cancelCountdown()
    }
  }

  // Handle confirm action
  const handleConfirm = async () => {
    if (!isValid) return

    const expenseData: ExpenseCreate = {
      group_id: groupId,
      amount: Number(editedData.amount),
      description: editedData.description,
      payer_id: editedData.payer_id,
    }

    await onConfirm(expenseData)
  }

  // Handle field change with user interaction tracking
  const handleFieldChange = (field: keyof ExpenseParseResponse, value: string | number) => {
    handleUserInteraction()
    handleChange(field, value)
  }

  // Handle field reset with user interaction tracking
  const handleFieldReset = (field: keyof ExpenseParseResponse) => {
    handleUserInteraction()
    handleReset(field)
  }

  return (
    <motion.div
      initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.2 }}
      className={cn(
        "flex flex-col gap-3",
        "p-4 rounded-lg",
        "bg-surface-elevated border border-border",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-text-secondary">
          Review Expense
        </h3>
        {isEdited && (
          <span className="text-xs text-text-tertiary">
            Edited
          </span>
        )}
      </div>

      {/* Amount field */}
      <InlineEditableField
        label="Amount"
        value={editedData.amount}
        onChange={(value) => handleFieldChange("amount", value)}
        onReset={() => handleFieldReset("amount")}
        isEdited={editedFields.has("amount")}
        originalValue={parsedData.amount}
        type="currency"
        errors={validationErrors.amount}
        name="amount"
      />

      {/* Description field */}
      <InlineEditableField
        label="Description"
        value={editedData.description}
        onChange={(value) => handleFieldChange("description", value)}
        onReset={() => handleFieldReset("description")}
        isEdited={editedFields.has("description")}
        originalValue={parsedData.description}
        type="text"
        errors={validationErrors.description}
        name="description"
      />

      {/* Payer dropdown */}
      <div className="flex flex-col gap-1.5">
        <label className="block text-xs font-medium text-text-secondary">
          Payer
        </label>
        <SelectPrimitive.Root
          value={editedData.payer_id}
          onValueChange={(value) => handleFieldChange("payer_id", value)}
          disabled={isLoadingMembers}
        >
          <SelectPrimitive.Trigger
            className={cn(
              "flex items-center justify-between",
              "w-full px-3 py-2 rounded-md",
              "bg-surface border border-border",
              "text-text-primary text-sm",
              "focus:outline-none focus:ring-2 focus:ring-action focus:border-action",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "data-[state=open]:ring-2 data-[state=open]:ring-action",
              editedFields.has("payer_id") && "bg-success-subtle border-action"
            )}
            aria-label="Select payer"
          >
            <SelectPrimitive.Value />
            <SelectPrimitive.Icon className="ml-2">
              <ChevronDown className="size-4 text-text-secondary" />
            </SelectPrimitive.Icon>
          </SelectPrimitive.Trigger>

          <SelectPrimitive.Portal>
            <SelectPrimitive.Content
              className={cn(
                "overflow-hidden rounded-md border border-border",
                "bg-surface-elevated shadow-lg",
                "z-50 min-w-[200px]"
              )}
              position="popper"
            >
              <SelectPrimitive.Viewport className="p-1">
                {members.map((member) => (
                  <SelectPrimitive.Item
                    key={member.user_id}
                    value={member.user_id}
                    className={cn(
                      "relative flex items-center gap-2",
                      "px-3 py-2 rounded-md text-sm",
                      "text-text-primary",
                      "focus:bg-surface focus:outline-none",
                      "data-[highlighted]:bg-surface",
                      "data-[state=checked]:bg-success-subtle",
                      "cursor-pointer"
                    )}
                  >
                    <SelectPrimitive.ItemText>
                      {member.full_name || member.email}
                    </SelectPrimitive.ItemText>
                    <SelectPrimitive.ItemIndicator className="ml-auto">
                      <Check className="size-4 text-action" />
                    </SelectPrimitive.ItemIndicator>
                  </SelectPrimitive.Item>
                ))}
              </SelectPrimitive.Viewport>
            </SelectPrimitive.Content>
          </SelectPrimitive.Portal>
        </SelectPrimitive.Root>

        {/* Reset button for payer */}
        {editedFields.has("payer_id") && (
          <button
            type="button"
            onClick={() => handleFieldReset("payer_id")}
            className="self-start text-xs text-text-secondary hover:text-text-primary flex items-center gap-1 mt-1"
          >
            ↺ Reset to AI suggestion
          </button>
        )}

        {/* Validation error for payer */}
        {validationErrors.payer_id && validationErrors.payer_id.length > 0 && (
          <div className="mt-1">
            {validationErrors.payer_id.map((error, index) => (
              <p key={index} className="text-xs text-error">
                {error}
              </p>
            ))}
          </div>
        )}
      </div>

      {/* Action buttons */}
      <div className="flex gap-2 mt-2">
        <button
          type="button"
          onClick={onDiscard}
          disabled={false}
          className={cn(
            "flex-1 py-2.5 px-4 rounded-md text-sm font-medium",
            "border border-border text-text-secondary",
            "hover:bg-surface hover:text-text-primary",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-action",
            "transition-colors duration-150",
            "disabled:opacity-50 disabled:cursor-not-allowed"
          )}
        >
          Discard
        </button>

        <button
          type="button"
          onClick={handleConfirm}
          disabled={!isValid}
          className={cn(
            "flex-1 py-2.5 px-4 rounded-md text-sm font-medium",
            "bg-action text-white",
            "hover:bg-action-hover",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-action",
            "transition-colors duration-150",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            "relative overflow-hidden"
          )}
        >
          {isCountingDown ? (
            <span>Confirm ({countdown}s)</span>
          ) : (
            <span>Confirm</span>
          )}
        </button>
      </div>
    </motion.div>
  )
}

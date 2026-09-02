import { useState } from "react"
import * as SelectPrimitive from "@radix-ui/react-select"
import * as TooltipPrimitive from "@radix-ui/react-tooltip"
import { Check, ChevronDown, Lock } from "lucide-react"

import { cn } from "@/lib/utils"
import { useCurrency } from "@/lib/currency-context"
import { InlineEditableField } from "@/components/ui/inline-input"
import { useExpenseEdit } from "../hooks/useExpenseEdit"
import { useSplitState } from "../hooks/useSplitState"
import { useGroupMembers } from "@/features/groups/api/groups"
import { SplitFields } from "./SplitFields"
import { buildSplitPayload } from "../utils/buildSplitPayload"
import type {
  ExpenseParseResponse,
  ExpenseCreate,
  Expense,
  GroupMember as GroupMemberType,
} from "../types"

interface EditableExpensePreviewProps {
  /** Parsed expense data from AI (for new expenses) */
  parsedData: ExpenseParseResponse
  /** Called when the expense is confirmed/saved. The passed ExpenseCreate
   *  carries the split, so creation + split happen in one atomic call. */
  onConfirm: (editedData: ExpenseCreate) => Promise<void>
  /** Called when user discards the expense */
  onDiscard: () => void
  /** Group ID for fetching members */
  groupId: string
  /** Additional className */
  className?: string
  /** Story 4.1: Current user ID for creator check (optional) */
  currentUserId?: string
  /** Story 4.1: Existing expense being edited (optional - enables creator check) */
  expense?: Expense
}

/**
 * Editable Expense Preview — review and edit an AI-parsed expense, choose how
 * it's split, and confirm.
 *
 * The split editor is shown INLINE and always (audit F1/F4): splitting is a
 * first-class part of creating an expense, not a setting hidden behind an
 * "Edit Details" gear. Confirm bundles the split INTO the create call so the
 * expense and its splits are written in one atomic request (audit F9) — there
 * is no separate "save split" step that can silently fail after the expense
 * already exists.
 */
export function EditableExpensePreview({
  parsedData,
  onConfirm,
  onDiscard,
  groupId,
  className,
  currentUserId,
  expense,
}: EditableExpensePreviewProps) {
  // Fetch group members for payer selection and split
  const { data: membersData, isLoading: isLoadingMembers } = useGroupMembers(groupId)
  const members: GroupMemberType[] = membersData?.members || []

  // The group's currency (WS10.1) — from CurrencyProvider in SmartInputModal
  const currency = useCurrency()

  // Story 4.1: Creator check for editing existing expenses
  const isCreator = expense && currentUserId ? expense.created_by === currentUserId : true
  const isEditableStatus = expense
    ? !["confirmed", "settled"].includes(expense.status)
    : true
  const canEdit = isCreator && isEditableStatus

  // Get creator name for tooltip
  const creatorMember = expense
    ? members.find((m) => m.user_id === expense.created_by)
    : null
  const creatorName = creatorMember?.full_name || creatorMember?.email || "the creator"

  // Edit state management (amount, description, payer)
  const {
    editedData,
    editedFields,
    handleChange,
    handleReset,
    isEdited,
    isValid: isBasicValid,
    validationErrors,
  } = useExpenseEdit(parsedData)

  // Split state management — always active now (not gated behind a mode)
  const split = useSplitState({
    totalAmount: Number(editedData.amount),
    members,
    payerId: editedData.payer_id,
    currency,
    // Pre-fill from the AI's participant suggestion (audit F7). The chips show
    // it and the user confirms/adjusts before saving.
    initialExcludedMembers: parsedData.split?.excluded_user_ids,
  })

  // Local submit state: Confirm bundles create + split, so the button shows
  // progress across that single request.
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Overall validity: basic fields AND a valid split (≥2 members, sums match)
  const isValid = isBasicValid && split.isValid

  const handleConfirm = async () => {
    if (!canEdit || !isValid || isSubmitting) return

    const expenseData: ExpenseCreate = {
      group_id: groupId,
      amount: Number(editedData.amount),
      description: editedData.description,
      payer_id: editedData.payer_id,
      split: buildSplitPayload({
        splitType: split.splitType,
        excludedMembers: split.excludedMembers,
        customAmounts: split.customAmounts,
        percentages: split.percentages,
        shares: split.shares,
      }),
    }

    setIsSubmitting(true)
    try {
      // Parent creates the expense (with split) and handles success/close.
      await onConfirm(expenseData)
    } catch {
      // Parent surfaces the error toast; keep the modal open so the user can
      // retry without re-entering everything.
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleFieldChange = (
    field: keyof ExpenseParseResponse,
    value: string | number,
  ) => {
    handleChange(field, value)
  }

  const handleFieldReset = (field: keyof ExpenseParseResponse) => {
    handleReset(field)
  }

  return (
    <div
      className={cn(
        "animate-in fade-in-0 duration-150",
        "flex flex-col gap-3",
        "p-4 rounded-lg",
        "bg-surface-elevated border border-border",
        className,
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-text-secondary">Review Expense</h3>
        {isEdited && <span className="text-xs text-text-tertiary">Edited</span>}
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
        <label className="block text-xs font-medium text-text-secondary">Payer</label>
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
              editedFields.has("payer_id") && "bg-success-subtle border-action",
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
                "z-50 min-w-[200px]",
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
                      "cursor-pointer",
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

        {editedFields.has("payer_id") && (
          <button
            type="button"
            onClick={() => handleFieldReset("payer_id")}
            className="self-start text-xs text-text-secondary hover:text-text-primary flex items-center gap-1 mt-1"
          >
            ↺ Reset to AI suggestion
          </button>
        )}

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

      {/* Split editor — inline and always visible (audit F1/F4) */}
      <div className="flex flex-col gap-3 pt-3 border-t border-border">
        <SplitFields
          members={members}
          totalAmount={Number(editedData.amount)}
          split={split}
        />
      </div>

      {/* Story 4.1: Non-creator restriction notice */}
      {!canEdit && expense && (
        <div className="flex items-center gap-2 p-3 rounded-md bg-warning-subtle border border-warning">
          <Lock className="w-4 h-4 text-warning" />
          <p className="text-xs text-warning">
            {!isCreator
              ? `Only ${creatorName} can edit this expense`
              : `This expense cannot be edited (status: ${expense.status})`}
          </p>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex gap-2 mt-2">
        <button
          type="button"
          onClick={onDiscard}
          className={cn(
            "flex-1 py-2.5 px-4 rounded-md text-sm font-medium",
            "border border-border text-text-secondary",
            "hover:bg-surface hover:text-text-primary",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-action",
            "transition-colors duration-150",
          )}
        >
          Discard
        </button>

        <TooltipPrimitive.Provider>
          <TooltipPrimitive.Root delayDuration={0}>
            <TooltipPrimitive.Trigger asChild>
              <button
                type="button"
                onClick={handleConfirm}
                disabled={!canEdit || !isValid || isSubmitting}
                className={cn(
                  "flex-1 py-2.5 px-4 rounded-md text-sm font-medium",
                  "bg-action text-white",
                  "hover:bg-action-hover",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-action",
                  "transition-colors duration-150",
                  "disabled:opacity-50 disabled:cursor-not-allowed",
                  "relative overflow-hidden",
                )}
              >
                {isSubmitting ? <span>Adding…</span> : <span>Confirm</span>}
              </button>
            </TooltipPrimitive.Trigger>
            {!canEdit && (
              <TooltipPrimitive.Content
                side="top"
                className="px-2 py-1 text-xs bg-surface-elevated border border-border rounded shadow-md z-50"
              >
                {!isCreator
                  ? `Only ${creatorName} can edit this expense`
                  : `This expense cannot be edited (status: ${expense?.status})`}
              </TooltipPrimitive.Content>
            )}
          </TooltipPrimitive.Root>
        </TooltipPrimitive.Provider>
      </div>
    </div>
  )
}

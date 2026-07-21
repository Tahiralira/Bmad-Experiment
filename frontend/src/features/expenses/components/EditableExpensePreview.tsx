import { useEffect, useState } from "react"
import * as SelectPrimitive from "@radix-ui/react-select"
import * as TooltipPrimitive from "@radix-ui/react-tooltip"
import { Check, ChevronDown, ChevronUp, Settings, Lock } from "lucide-react"
import { toast } from "sonner"

import { cn } from "@/lib/utils"
import { useCurrency } from "@/lib/currency-context"
import { InlineEditableField } from "@/components/ui/inline-input"
import { useExpenseEdit } from "../hooks/useExpenseEdit"
import { useSplitState } from "../hooks/useSplitState"
import { useGroupMembers } from "@/features/groups/api/groups"
import { useUpdateExpenseSplit } from "../api/expenses"
import { SplitPicker } from "./SplitPicker"
import { MemberChips } from "./MemberChips"
import { SplitAmountsDisplay } from "./SplitAmountsDisplay"
import { UnequalSplitInputs } from "./UnequalSplitInputs"
import { PercentageSplitInputs } from "./PercentageSplitInputs"
import type { ExpenseParseResponse, ExpenseCreate, Expense, GroupMember as GroupMemberType } from "../types"

interface EditableExpensePreviewProps {
  /** Parsed expense data from AI (for new expenses) */
  parsedData: ExpenseParseResponse
  /** Called when expense is confirmed/saved - returns the created expense ID */
  onConfirm: (editedData: ExpenseCreate) => Promise<string>
  /** Called when user discards the expense */
  onDiscard: () => void
  /** Group ID for fetching members */
  groupId: string
  /** Additional className */
  className?: string
  /** Story 4.1: Current user ID for creator check (optional - for editing existing expenses) */
  currentUserId?: string
  /** Story 4.1: Existing expense being edited (optional - enables creator check) */
  expense?: Expense
}

/**
 * Editable Expense Preview - Allows users to review and edit AI-parsed expenses.
 *
 * Features:
 * - Inline editing for amount, description, payer
 * - Change tracking with visual highlights
 * - Reset to AI suggestion per field
 * - Zod validation with inline errors
 * - Confirm/Discard actions — manual confirm ONLY (UX-H6: financial records
 *   never commit on a timer)
 * - Payer selection from group members
 * - Complex edit mode: Split type selection, member exclusions (Story 3.5)
 *
 * @example
 * ```tsx
 * <EditableExpensePreview
 *   parsedData={parsedData}
 *   onConfirm={handleConfirm}
 *   onDiscard={handleDiscard}
 *   groupId="group-123"
 *   currentUserId="user-123"
 * />
 * ```
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
  // If expense is provided, check if current user is the creator
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

  // Edit state management
  const {
    editedData,
    editedFields,
    handleChange,
    handleReset,
    isEdited,
    isValid: isBasicValid,
    validationErrors,
  } = useExpenseEdit(parsedData)

  // Complex edit mode state
  const [isComplexMode, setIsComplexMode] = useState(false)

  // Split state management
  const {
    splitType,
    setSplitType,
    excludedMembers,
    toggleMemberExclusion,
    customAmounts,
    setCustomAmount,
    percentages,
    setPercentage,
    splitAmounts,
    isValid: isSplitValid,
    validationError: splitValidationError,
  } = useSplitState({
    totalAmount: Number(editedData.amount),
    members,
    payerId: editedData.payer_id,
    currency,
  })

  // Pre-populate custom amounts when switching from equal to unequal split (Story 3.6)
  useEffect(() => {
    if (splitType === "unequal" && customAmounts.size === 0 && splitAmounts.size > 0) {
      // User just switched to unequal split and no custom amounts are set yet
      // Pre-populate with current equal split amounts
      splitAmounts.forEach((amount, memberId) => {
        setCustomAmount(memberId, amount)
      })
    }
  }, [splitType, splitAmounts, customAmounts.size, setCustomAmount])

  // Pre-populate percentages when switching from equal to percentage split (Story 3.7)
  useEffect(() => {
    if (splitType === "percentage" && percentages.size === 0 && members.length > 0) {
      // User just switched to percentage split and no percentages are set yet
      // Pre-populate with equal distribution: 100 / num_members
      const equalPercentage = 100 / members.length
      members.forEach((member) => {
        const memberId = member.user_id || member.id
        setPercentage(memberId, equalPercentage)
      })
    }
  }, [splitType, percentages.size, members.length, members, setPercentage])

  // Split mutation for saving split configuration (Story 3.5)
  const updateSplitMutation = useUpdateExpenseSplit()

  // Handle confirm action
  const handleConfirm = async () => {
    if (!isBasicValid) return
    // In complex mode, also validate split
    if (isComplexMode && !isSplitValid) return

    const expenseData: ExpenseCreate = {
      group_id: groupId,
      amount: Number(editedData.amount),
      description: editedData.description,
      payer_id: editedData.payer_id,
    }

    try {
      // Create expense and get the expense ID
      const expenseId = await onConfirm(expenseData)

      // If in complex mode (split editing), save the split configuration
      if (isComplexMode) {
        // Prepare split data based on split type
        let splitData:
          | { type: "equal"; excluded_user_ids: string[] }
          | { type: "unequal"; splits: Array<{ user_id: string; amount: number }>; excluded_user_ids: string[] }
          | { type: "percentage"; splits: Array<{ user_id: string; percentage: number }>; excluded_user_ids: string[] }

        if (splitType === "equal") {
          splitData = {
            type: "equal",
            excluded_user_ids: Array.from(excludedMembers),
          }
        } else if (splitType === "unequal") {
          // Convert customAmounts Map to array format — dropping stale
          // entries of members excluded after their amount was set (S4-M2)
          splitData = {
            type: "unequal",
            splits: Array.from(customAmounts.entries())
              .filter(([user_id]) => !excludedMembers.has(user_id))
              .map(([user_id, amount]) => ({
                user_id,
                amount,
              })),
            excluded_user_ids: Array.from(excludedMembers),
          }
        } else if (splitType === "percentage") {
          // Convert percentages Map to array format (same stale-entry filter)
          splitData = {
            type: "percentage",
            splits: Array.from(percentages.entries())
              .filter(([user_id]) => !excludedMembers.has(user_id))
              .map(([user_id, percentage]) => ({
                user_id,
                percentage,
              })),
            excluded_user_ids: Array.from(excludedMembers),
          }
        } else {
          // Other split types not yet implemented
          throw new Error(`Split type "${splitType}" not yet implemented`)
        }

        await updateSplitMutation.mutateAsync({
          expenseId,
          data: splitData,
        })
        toast.success("Expense and split saved successfully!")
      }
    } catch (error) {
      // Error is already handled by parent's toast
      // Don't close modal on error
      throw error
    }
  }

  // Handle field change
  const handleFieldChange = (field: keyof ExpenseParseResponse, value: string | number) => {
    handleChange(field, value)
  }

  // Handle field reset
  const handleFieldReset = (field: keyof ExpenseParseResponse) => {
    handleReset(field)
  }

  // Toggle complex edit mode
  const toggleComplexMode = () => {
    setIsComplexMode((prev) => !prev)
  }

  // Overall validation (basic + split if in complex mode)
  const isValid = isComplexMode ? isBasicValid && isSplitValid : isBasicValid

  return (
    <div
      className={cn(
        "animate-in fade-in-0 duration-150",
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
        <div className="flex items-center gap-2">
          {isEdited && (
            <span className="text-xs text-text-tertiary">
              Edited
            </span>
          )}
          {/* Edit Details button */}
          <button
            type="button"
            onClick={toggleComplexMode}
            className={cn(
              "flex items-center gap-1 px-2 py-1 rounded text-xs",
              "text-text-secondary hover:text-text-primary",
              "hover:bg-surface transition-colors"
            )}
          >
            <Settings className="w-3 h-3" />
            {isComplexMode ? (
              <>
                <span>Simple</span>
                <ChevronUp className="w-3 h-3" />
              </>
            ) : (
              <>
                <span>Edit Details</span>
                <ChevronDown className="w-3 h-3" />
              </>
            )}
          </button>
        </div>
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

      {/* Complex Edit Mode - Split Controls (Story 3.5) */}
      {isComplexMode && (
          <div className="animate-in fade-in-0 duration-150 flex flex-col gap-3 pt-3 border-t border-border">
            {/* Split Type Picker */}
            <SplitPicker
              selectedType={splitType}
              onSelectType={setSplitType}
            />

            {/* Unequal Split Amount Inputs (Story 3.6 + 3.8 exclusions) */}
            {splitType === "unequal" && (
              <UnequalSplitInputs
                members={members}
                excludedMembers={excludedMembers}
                customAmounts={customAmounts}
                totalAmount={Number(editedData.amount)}
                onAmountChange={setCustomAmount}
              />
            )}

            {/* Percentage Split Inputs (Story 3.7 + 3.8 exclusions) */}
            {splitType === "percentage" && (
              <PercentageSplitInputs
                members={members}
                excludedMembers={excludedMembers}
                percentages={percentages}
                totalAmount={Number(editedData.amount)}
                onPercentageChange={setPercentage}
              />
            )}

            {/* Member Chips (shown for all split types) */}
            <MemberChips
              members={members}
              includedMembers={excludedMembers}
              onToggleInclude={toggleMemberExclusion}
            />

            {/* Split Amounts Display */}
            <SplitAmountsDisplay
              totalAmount={Number(editedData.amount)}
              splitAmounts={splitAmounts}
              members={members}
              includedMembers={excludedMembers}
            />

            {/* Split validation error */}
            {splitValidationError && (
              <p className="text-xs text-error">
                {splitValidationError}
              </p>
            )}

            {/* Done button (collapse complex mode) */}
            <button
              type="button"
              onClick={toggleComplexMode}
              className="w-full py-2 px-4 rounded-md text-sm font-medium border border-border text-text-secondary hover:bg-surface transition-colors"
            >
              Done
            </button>
          </div>
      )}

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

        <TooltipPrimitive.Provider>
          <TooltipPrimitive.Root delayDuration={0}>
            <TooltipPrimitive.Trigger asChild>
              <button
                type="button"
                onClick={handleConfirm}
                disabled={!canEdit || !isValid || updateSplitMutation.isPending}
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
                {updateSplitMutation.isPending ? (
                  <span>Saving...</span>
                ) : (
                  <span>Confirm</span>
                )}
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

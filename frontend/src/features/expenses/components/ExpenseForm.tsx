import { useState } from "react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"
import { EVENTS, track } from "@/lib/analytics"
import { useAuth } from "@/hooks/useAuth"
import { useCurrency } from "@/lib/currency-context"
import { useGroupMembers } from "@/features/groups/api/groups"

import { useCreateExpense } from "../api/expenses"
import { useSplitState } from "../hooks/useSplitState"
import { buildSplitPayload } from "../utils/buildSplitPayload"
import { SplitFields } from "./SplitFields"
import type { ExpenseCreate, GroupMember } from "../types"

interface ExpenseFormProps {
  groupId: string
  onSuccess?: () => void
  onCancel?: () => void
}

/**
 * Manual expense entry — the non-AI path. Now feeds the SAME split pipeline as
 * the AI preview (audit F3): amount, description, who paid (F12), and an inline
 * split editor, all submitted in one atomic create-with-split call (F9).
 */
export function ExpenseForm({ groupId, onSuccess, onCancel }: ExpenseFormProps) {
  const { user } = useAuth()
  const { data: membersData, isLoading: isLoadingMembers } = useGroupMembers(groupId)
  const members: GroupMember[] = membersData?.members || []
  const currency = useCurrency()

  const [amount, setAmount] = useState("")
  const [description, setDescription] = useState("")
  const [payerId, setPayerId] = useState<string>("")

  // The payer defaults to the current user (the common case) until they pick
  // someone else — "Sarah paid" is now expressible (audit F12).
  const effectivePayerId = payerId || user?.id || ""

  const createExpense = useCreateExpense()

  const totalAmount = parseFloat(amount) || 0
  const split = useSplitState({
    totalAmount,
    members,
    payerId: effectivePayerId,
    currency,
  })

  const amountValid = totalAmount > 0
  const descriptionValid = description.trim().length > 0
  const canSubmit =
    amountValid && descriptionValid && split.isValid && !createExpense.isPending

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!canSubmit) return

    const expenseData: ExpenseCreate = {
      group_id: groupId,
      amount: totalAmount,
      description: description.trim(),
      payer_id: effectivePayerId || undefined,
      split: buildSplitPayload({
        splitType: split.splitType,
        excludedMembers: split.excludedMembers,
        customAmounts: split.customAmounts,
        percentages: split.percentages,
        shares: split.shares,
      }),
    }

    try {
      await createExpense.mutateAsync(expenseData)
      track(EVENTS.EXPENSE_CREATED, { source: "manual" })
      setAmount("")
      setDescription("")
      setPayerId("")
      onSuccess?.()
    } catch {
      // Error surfaced by the mutation below
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Amount */}
      <div className="space-y-2">
        <Label htmlFor="amount">Amount</Label>
        <div className="relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
            $
          </span>
          <Input
            type="number"
            id="amount"
            step="0.01"
            min="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="pl-7"
            placeholder="0.00"
            required
          />
        </div>
      </div>

      {/* Description */}
      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Input
          type="text"
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="What was this expense for?"
          maxLength={500}
          required
        />
      </div>

      {/* Payer (audit F12) */}
      <div className="space-y-2">
        <Label htmlFor="payer">Paid by</Label>
        <select
          id="payer"
          value={effectivePayerId}
          onChange={(e) => setPayerId(e.target.value)}
          disabled={isLoadingMembers || members.length === 0}
          className={cn(
            "w-full px-3 py-2 rounded-md text-sm",
            "bg-surface border border-border text-text-primary",
            "focus:outline-none focus:ring-2 focus:ring-action focus:border-action",
            "disabled:opacity-50 disabled:cursor-not-allowed",
          )}
        >
          {members.map((member) => (
            <option key={member.user_id} value={member.user_id}>
              {(member.full_name || member.email) +
                (member.user_id === user?.id ? " (You)" : "")}
            </option>
          ))}
        </select>
      </div>

      {/* Split editor — same component the AI preview uses (audit F3) */}
      <div className="space-y-2 pt-2 border-t border-border">
        <SplitFields members={members} totalAmount={totalAmount} split={split} />
      </div>

      <div className="flex gap-3">
        <Button type="submit" disabled={!canSubmit} className="flex-1">
          {createExpense.isPending ? "Adding…" : "Add Expense"}
        </Button>
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        )}
      </div>

      {createExpense.isError && (
        <p className="text-sm text-destructive">
          {createExpense.error.message || "Failed to create expense"}
        </p>
      )}
    </form>
  )
}

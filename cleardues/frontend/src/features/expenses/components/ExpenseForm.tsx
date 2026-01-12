import { useState } from "react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

import { useCreateExpense } from "../api/expenses"
import type { ExpenseCreate } from "../types"

interface ExpenseFormProps {
  groupId: string
  onSuccess?: () => void
  onCancel?: () => void
}

export function ExpenseForm({ groupId, onSuccess, onCancel }: ExpenseFormProps) {
  const [amount, setAmount] = useState("")
  const [description, setDescription] = useState("")
  const createExpense = useCreateExpense()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const expenseData: ExpenseCreate = {
      group_id: groupId,
      amount: parseFloat(amount),
      description: description.trim(),
    }

    try {
      await createExpense.mutateAsync(expenseData)
      setAmount("")
      setDescription("")
      onSuccess?.()
    } catch {
      // Error handled by mutation
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
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

      <div className="flex gap-3">
        <Button
          type="submit"
          disabled={createExpense.isPending}
          className="flex-1"
        >
          {createExpense.isPending ? "Creating..." : "Add Expense"}
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

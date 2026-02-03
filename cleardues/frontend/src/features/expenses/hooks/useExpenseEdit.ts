import { useState, useCallback } from "react"
import { z } from "zod"

import type { ExpenseParseResponse } from "../types"

/**
 * Zod validation schema for expense data
 * Validates amount (positive, max 2 decimals) and description (required, length limits)
 */
const expenseDataSchema = z.object({
  amount: z
    .number({ message: "Amount must be a number" })
    .positive({ message: "Amount must be positive" })
    .max(999999.99, { message: "Amount exceeds maximum" })
    .refine(
      (val) => {
        // Check max 2 decimal places
        const decimalPlaces = val.toString().split(".")[1]?.length || 0
        return decimalPlaces <= 2
      },
      {
        message: "Amount can have maximum 2 decimal places",
      }
    ),
  description: z
    .string({ message: "Description must be text" })
    .min(2, { message: "Description must be at least 2 characters" })
    .max(200, { message: "Description must be less than 200 characters" }),
  payer_id: z.string({ message: "Payer must be selected" }),
})

export type ExpenseDataValidation = {
  amount?: string[]
  description?: string[]
  payer_id?: string[]
}

/**
 * Custom hook for managing expense edit state
 *
 * Features:
 * - Tracks original vs edited data
 * - Tracks which fields have been modified
 * - Provides change and reset handlers
 * - Validates data using Zod schema
 *
 * @example
 * ```tsx
 * const {
 *   editedData,
 *   editedFields,
 *   handleChange,
 *   handleReset,
 *   isEdited,
 *   isValid,
 *   validationErrors
 * } = useExpenseEdit(parsedData)
 * ```
 */
export function useExpenseEdit(initialData: ExpenseParseResponse) {
  const [originalData] = useState(initialData)
  const [editedData, setEditedData] = useState(initialData)
  const [editedFields, setEditedFields] = useState<Set<keyof ExpenseParseResponse>>(new Set())

  /**
   * Handle field value change
   * Updates edited data and marks field as edited
   * For amount field, converts string to number (or 0 if empty/invalid)
   */
  const handleChange = useCallback((field: keyof ExpenseParseResponse, value: string | number) => {
    // Convert amount to number if needed
    let processedValue: string | number = value
    if (field === "amount" && typeof value === "string") {
      const numValue = parseFloat(value)
      processedValue = isNaN(numValue) ? 0 : numValue
    } else if (field === "amount" && typeof value === "number") {
      processedValue = isNaN(value) ? 0 : value
    }

    setEditedData((prev) => ({ ...prev, [field]: processedValue }))
    setEditedFields((prev) => new Set([...prev, field]))
  }, [])

  /**
   * Handle field reset to original value
   * Reverts field to original AI suggestion and removes from edited set
   */
  const handleReset = useCallback((field: keyof ExpenseParseResponse) => {
    setEditedData((prev) => ({ ...prev, [field]: originalData[field] }))
    setEditedFields((prev) => {
      const newSet = new Set(prev)
      newSet.delete(field)
      return newSet
    })
  }, [originalData])

  /**
   * Validate current edited data
   * Returns true if valid, false otherwise
   */
  const validateData = useCallback((): boolean => {
    const result = expenseDataSchema.safeParse(editedData)
    return result.success
  }, [editedData])

  /**
   * Get validation errors for current edited data
   * Returns object with field names as keys and error arrays as values
   */
  const getValidationErrors = useCallback((): ExpenseDataValidation => {
    const result = expenseDataSchema.safeParse(editedData)
    if (result.success) {
      return {}
    }
    // Use flatten() to get fieldErrors in Zod v4
    const flattened = result.error.flatten()
    return {
      amount: flattened.fieldErrors.amount as string[] | undefined,
      description: flattened.fieldErrors.description as string[] | undefined,
      payer_id: flattened.fieldErrors.payer_id as string[] | undefined,
    }
  }, [editedData])

  // Computed values
  const isEdited = editedFields.size > 0
  const isValid = validateData()
  const validationErrors = getValidationErrors()

  return {
    // State
    originalData,
    editedData,
    editedFields,
    validationErrors,
    // Computed
    isEdited,
    isValid,
    // Handlers
    handleChange,
    handleReset,
  }
}

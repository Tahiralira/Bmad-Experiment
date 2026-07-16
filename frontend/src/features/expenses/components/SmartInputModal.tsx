import { useState, useEffect, useRef, useCallback } from "react"
import { useQueryClient } from "@tanstack/react-query"
import * as DialogPrimitive from "@radix-ui/react-dialog"
import { X } from "lucide-react"
import FocusTrap from "focus-trap-react"
import { toast } from "sonner"

import { cn } from "@/lib/utils"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useUserGroups } from "@/features/groups/api/groups"
import { useAuth } from "@/hooks/useAuth"
import { AICommentaryBubble } from "./AICommentaryBubble"
import { ExpensePreviewCard } from "./ExpensePreviewCard"
import { ExpenseForm } from "./ExpenseForm"
import { parseExpense, ParseError } from "../api/parse"
import { useCreateExpense } from "../api/expenses"
import type { ExpenseParseResponse, ExpenseCreate } from "../types"

// ============================================================================
// Types and Interfaces
// ============================================================================

export interface SmartInputModalProps {
  /** Whether the modal is open */
  open: boolean
  /** Called when modal should close */
  onOpenChange: (open: boolean) => void
  /** Pre-selected group ID (if provided, selector is hidden) */
  groupId?: string
  /** Entry point context - affects group selector visibility */
  entryPoint?: "dashboard" | "group"
  /** Ref to the FAB element for focus return on close */
  triggerRef?: React.RefObject<HTMLElement | null>
}

// ============================================================================
// Main SmartInputModal Component
// ============================================================================

/**
 * Smart Input Modal - The signature ClearDues expense entry experience.
 *
 * Features:
 * - Full-screen on mobile, centered dialog (600px max) on desktop
 * - Natural language input field with contextual placeholder
 * - AI commentary bubble with streaming text effect
 * - Expense preview card with editable fields (Story 3.4)
 * - Toggle between smart input and manual form
 * - Close via X button, Escape key, or backdrop tap
 * - Full keyboard accessibility with focus trap
 *
 * @example
 * ```tsx
 * <SmartInputModal
 *   open={isOpen}
 *   onOpenChange={setIsOpen}
 *   groupId="group-123"
 *   triggerRef={orbRef}
 * />
 * ```
 */
export function SmartInputModal({
  open,
  onOpenChange,
  groupId,
  entryPoint = "dashboard",
  triggerRef,
}: SmartInputModalProps) {
  // State
  const [inputText, setInputText] = useState("")
  const [mode, setMode] = useState<"smart" | "manual">("smart")
  const [isProcessing, setIsProcessing] = useState(false)
  const [parsedData, setParsedData] = useState<ExpenseParseResponse | null>(null)
  const [previewStatus, setPreviewStatus] = useState<"placeholder" | "loading" | "ready" | "error">("placeholder")

  // The real signed-in user (WS5/S4-C1 — was a hardcoded "user-123" that the
  // backend would have rejected as a non-UUID payer)
  const { user: currentUser } = useAuth()
  const currentUserId = currentUser?.id

  // Group selection (WS5/S4-C1): with no groupId prop (global FAB entry),
  // the user picks a group here; a per-group mount hides the selector
  const [selectedGroupId, setSelectedGroupId] = useState<string | undefined>(
    undefined,
  )
  const effectiveGroupId = groupId ?? selectedGroupId
  const { data: groups } = useUserGroups()

  // Query client for cache invalidation
  const queryClient = useQueryClient()

  // Expense creation mutation
  const createExpenseMutation = useCreateExpense()

  // Real AI commentary (WS7/S4-C2): word chunks streamed over SSE are
  // appended as they arrive — no simulated typing effect
  const [commentary, setCommentary] = useState("")
  // Mediator-voice message when a parse fails (quota, low confidence, ...)
  const [parseError, setParseError] = useState<string | null>(null)
  // In-flight parse — aborted when the modal closes or a new parse starts
  const abortRef = useRef<AbortController | null>(null)

  const abortParse = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
  }, [])

  // Handle smart input submission — streams the REAL parse (WS7)
  const handleSmartSubmit = async () => {
    if (!inputText.trim() || !effectiveGroupId || !currentUserId || isProcessing)
      return

    abortParse()
    const controller = new AbortController()
    abortRef.current = controller

    setIsProcessing(true)
    setPreviewStatus("loading")
    setParsedData(null)
    setParseError(null)
    setCommentary("")

    try {
      const parsed = await parseExpense({
        text: inputText,
        groupId: effectiveGroupId,
        onCommentary: (chunk) => setCommentary((prev) => prev + chunk),
        signal: controller.signal,
      })
      if (controller.signal.aborted) return
      setParsedData(parsed)
      setPreviewStatus("ready")
    } catch (error) {
      if (controller.signal.aborted) return
      setCommentary("")
      setParseError(
        error instanceof ParseError
          ? error.message
          : "Something went wrong talking to the AI. Please try again or use the manual form.",
      )
      setPreviewStatus("error")
    } finally {
      if (!controller.signal.aborted) setIsProcessing(false)
    }
  }

  // Handle confirm action from editable preview
  const handleConfirm = async (editedData: ExpenseCreate): Promise<string> => {
    if (!effectiveGroupId) {
      throw new Error("Group ID is required")
    }

    try {
      // Create expense and capture the result
      const expense = await createExpenseMutation.mutateAsync(editedData)

      // Invalidate queries to refresh expense list and group balances
      queryClient.invalidateQueries({ queryKey: ["expenses"] })
      queryClient.invalidateQueries({ queryKey: ["groups", effectiveGroupId] })

      // Show success toast (split success toast is shown separately in EditableExpensePreview)
      toast.success("Expense added successfully!")

      // Close modal
      onOpenChange(false)

      // Reset state
      setParsedData(null)
      setPreviewStatus("placeholder")
      setInputText("")

      // Return the expense ID so EditableExpensePreview can call the split API
      return expense.id
    } catch (error) {
      // Show error toast
      toast.error("Failed to add expense. Please try again.")
      console.error("Failed to create expense:", error)
      throw error // Re-throw to allow EditableExpensePreview to handle it
    }
  }

  // Handle discard action from editable preview
  const handleDiscard = () => {
    // Reset preview state
    setParsedData(null)
    setPreviewStatus("placeholder")
    setInputText("")
    setCommentary("")
    setParseError(null)
  }

  // Handle manual form success
  const handleManualSuccess = () => {
    // Close modal after successful manual form submission
    onOpenChange(false)
  }

  // Handle keyboard events in textarea
  // On desktop: Ctrl+Enter or Cmd+Enter submits (Enter alone creates new line)
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault()
      handleSmartSubmit()
    }
  }

  // Handle Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && open) {
        onOpenChange(false)
      }
    }
    window.addEventListener("keydown", handleEscape)
    return () => window.removeEventListener("keydown", handleEscape)
  }, [open, onOpenChange])

  // Handle modal close with state reset
  const handleClose = () => {
    abortParse()
    onOpenChange(false)
    // Reset state after close animation
    setTimeout(() => {
      setInputText("")
      setMode("smart")
      setIsProcessing(false)
      setCommentary("")
      setParseError(null)
      setParsedData(null)
      setPreviewStatus("placeholder")
    }, 200) // Match slide-down animation duration
  }

  // Return focus to trigger (Agent Orb) when modal closes
  // Delay must be longer than exit animation duration (200ms) to ensure smooth transition
  useEffect(() => {
    if (!open && triggerRef?.current) {
      const timeoutId = setTimeout(() => {
        triggerRef.current?.focus()
      }, 250) // 250ms > 200ms exit animation duration
      return () => clearTimeout(timeoutId)
    }
  }, [open, triggerRef])

  // Reset input when modal opens; abort any in-flight parse on close/unmount
  useEffect(() => {
    if (open) {
      setInputText("")
      setMode("smart")
      setIsProcessing(false)
      setCommentary("")
      setParseError(null)
      setParsedData(null)
      setPreviewStatus("placeholder")
      setSelectedGroupId(undefined)
    } else {
      abortParse()
    }
  }, [open, abortParse])

  useEffect(() => () => abortParse(), [abortParse])

  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <DialogPrimitive.Portal>
        {/* Backdrop overlay */}
        <DialogPrimitive.Overlay
          className={cn(
            "fixed inset-0 z-50 bg-black/30",
            "data-[state=open]:animate-in data-[state=closed]:animate-out",
            "data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0"
          )}
          onClick={handleClose}
        />

        {/* Modal content */}
        <DialogPrimitive.Content asChild>
          <div
            className={cn(
              "data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:slide-in-from-bottom-4 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:slide-out-to-bottom-4 duration-200",
              // Mobile: full-screen from bottom (responsive classes, no variant needed)
              "fixed inset-x-0 bottom-0 z-50 w-full",
              "bg-surface rounded-t-lg shadow-lg",
              // Desktop: centered dialog
              "lg:fixed lg:inset-auto lg:left-1/2 lg:top-1/2 lg:-translate-x-1/2 lg:-translate-y-1/2",
              "lg:max-w-[600px] lg:w-full lg:max-h-[80vh] lg:rounded-lg",
              "lg:border lg:border-border"
            )}
          >
            {/* Focus trap wraps all focusable content.
                focus-trap-react requires a single element child (not a render prop). */}
            <FocusTrap
              active={open}
              focusTrapOptions={{
                allowOutsideClick: true,
                // jsdom has no layout, so tabbable's display check finds zero
                // tabbable nodes and focus-trap throws. Disabling the check in
                // test mode is the workaround tabbable's docs recommend.
                ...(import.meta.env.MODE === "test" && {
                  tabbableOptions: { displayCheck: "none" as const },
                }),
              }}
            >
              {/* overflow-y-auto: with real commentary + preview the content
                  can exceed 80vh — without it Confirm is unreachable on
                  short viewports (found in WS7 browser verification) */}
              <div className="flex flex-col h-full max-h-[80vh] p-6 overflow-y-auto">
                  {/* Header */}
                  <div className="flex items-center justify-between mb-4">
                    {/* Radix DialogTitle so screen readers announce the modal */}
                    <DialogPrimitive.Title asChild>
                      <h2 className="text-title font-medium text-text-primary">
                        {entryPoint === "dashboard" ? "Add Expense" : "Add Expense to Group"}
                      </h2>
                    </DialogPrimitive.Title>
                    <DialogPrimitive.Close
                      className={cn(
                        "rounded opacity-70 transition-opacity hover:opacity-100",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      )}
                    >
                      <X className="size-5" />
                      <span className="sr-only">Close</span>
                    </DialogPrimitive.Close>
                  </div>

                  {/* Group selector — only for global entry points without
                      a pre-selected group (WS5/S4-C1) */}
                  {!groupId && (
                    <div className="mb-4 space-y-1.5">
                      <label
                        htmlFor="smart-input-group"
                        className="block text-xs font-medium text-text-secondary"
                      >
                        Group
                      </label>
                      <Select
                        value={selectedGroupId ?? ""}
                        onValueChange={(value) => setSelectedGroupId(value)}
                      >
                        <SelectTrigger
                          id="smart-input-group"
                          className="w-full"
                          aria-label="Select group for this expense"
                        >
                          <SelectValue placeholder="Choose a group" />
                        </SelectTrigger>
                        <SelectContent>
                          {(groups ?? []).map((group) => (
                            <SelectItem key={group.id} value={group.id}>
                              {group.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {!effectiveGroupId && (
                        <p className="text-xs text-text-muted">
                          Pick which group this expense belongs to.
                        </p>
                      )}
                    </div>
                  )}

                  {mode === "smart" ? (
                    <>
                      {/* AI Commentary Bubble — real streamed commentary (WS7);
                          tone follows the group's ai_personality server-side */}
                      <AICommentaryBubble
                        text={commentary}
                        isProcessing={isProcessing}
                      />

                      {/* Natural Language Input Field */}
                      <div className="space-y-4">
                        <textarea
                          value={inputText}
                          onChange={(e) => setInputText(e.target.value)}
                          onKeyDown={handleKeyDown}
                          placeholder="Paid 150 for dinner, split with everyone except Tom"
                          className={cn(
                            "w-full min-h-[120px] p-4 rounded-lg resize-none",
                            "bg-surface border border-border",
                            "text-text-primary placeholder:text-text-muted",
                            "focus:outline-none focus:ring-2 focus:ring-action focus:border-action"
                          )}
                          aria-label="Expense description in natural language"
                        />

                        {/* Fallback Button - Switch to Manual Form */}
                        <button
                          type="button"
                          onClick={() => setMode("manual")}
                          className={cn(
                            "text-sm text-text-secondary hover:text-text-primary",
                            "underline transition-colors"
                          )}
                        >
                          Switch to Manual Form
                        </button>
                      </div>

                      {/* Expense Preview Card — manual confirm only (UX-H6) */}
                      <ExpensePreviewCard
                        data={parsedData}
                        status={previewStatus}
                        onConfirm={handleConfirm}
                        onDiscard={handleDiscard}
                        groupId={effectiveGroupId}
                        errorMessage={parseError}
                      />

                      {/* Submit Button — disabled (not silently no-op, S4-C1)
                          until a group is chosen */}
                      <button
                        type="button"
                        onClick={handleSmartSubmit}
                        disabled={!inputText.trim() || isProcessing || !effectiveGroupId}
                        className={cn(
                          "mt-6 w-full py-3 rounded-lg font-medium",
                          "bg-action text-white",
                          "hover:bg-action-hover transition-colors",
                          "disabled:opacity-50 disabled:cursor-not-allowed",
                          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                        )}
                      >
                        {isProcessing ? "Processing..." : "Add Expense"}
                      </button>
                    </>
                  ) : (
                    <>
                      {/* Manual Form Mode - Reuse ExpenseForm from Story 3.1 */}
                      <div className="space-y-4">
                        <p className="text-sm text-text-secondary">
                          Fill in the details below:
                        </p>
                        {effectiveGroupId ? (
                          <ExpenseForm
                            groupId={effectiveGroupId}
                            onSuccess={handleManualSuccess}
                            onCancel={() => setMode("smart")}
                          />
                        ) : (
                          <p className="text-text-muted text-sm">
                            Choose a group above to add an expense.
                          </p>
                        )}

                        {/* Back to Smart Input button */}
                        <button
                          type="button"
                          onClick={() => setMode("smart")}
                          className={cn(
                            "w-full py-2 rounded-lg text-sm",
                            "border border-border text-text-secondary",
                            "hover:bg-surface hover:text-text-primary",
                            "transition-colors"
                          )}
                        >
                          ← Back to Smart Input
                        </button>
                      </div>
                    </>
                  )}
              </div>
            </FocusTrap>
          </div>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  )
}

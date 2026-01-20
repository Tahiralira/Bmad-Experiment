import { useState, useEffect } from "react"
import * as DialogPrimitive from "@radix-ui/react-dialog"
import { motion, type PanInfo, type TargetAndTransition, useReducedMotion, useMotionValue } from "framer-motion"
import { X } from "lucide-react"
import FocusTrap from "focus-trap-react"

import { cn } from "@/lib/utils"
import { AICommentaryBubble } from "./AICommentaryBubble"
import { ExpensePreviewCard } from "./ExpensePreviewCard"
import { ExpenseForm } from "./ExpenseForm"
import { useStreamingText } from "../hooks/useStreamingText"

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
  /** Ref to the Agent Orb element for focus return on close */
  triggerRef?: React.RefObject<HTMLElement | null>
}

// ============================================================================
// Animation Variants
// ============================================================================

// Modal animates from bottom-right (Agent Orb position)
// On mobile: slides up from bottom with origin at bottom-right
// On desktop: scales from bottom-right corner
const modalVariants = {
  hidden: {
    opacity: 0,
    y: "100%",
    x: 50, // Start slightly offset toward right (Orb is at right)
    scale: 0.9,
    originY: 1, // Origin at bottom (Agent Orb position)
    originX: 1, // Origin at right (Agent Orb is on right side)
  } as TargetAndTransition,
  visible: {
    opacity: 1,
    y: 0,
    x: 0,
    scale: 1,
    originY: 1,
    originX: 1,
    transition: {
      type: "spring" as const,
      stiffness: 300,
      damping: 30,
      duration: 0.3,
    },
  } as TargetAndTransition,
  exit: {
    opacity: 0,
    y: "100%",
    x: 50,
    scale: 0.9,
    originY: 1,
    originX: 1,
    transition: {
      duration: 0.2,
      ease: "easeIn" as const,
    },
  } as TargetAndTransition,
}

// ============================================================================
// Main SmartInputModal Component
// ============================================================================

/**
 * Smart Input Modal - The signature ClearDues expense entry experience.
 *
 * Features:
 * - Full-screen on mobile, centered dialog (600px max) on desktop
 * - Slide-up animation from Agent Orb position
 * - Natural language input field with contextual placeholder
 * - AI commentary bubble with streaming text effect
 * - Expense preview card area (placeholder for Story 3.4)
 * - Toggle between smart input and manual form
 * - Close via X button, Escape key, backdrop tap, or swipe down
 * - Full keyboard accessibility with focus trap
 * - Reduced motion support
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
  const shouldReduceMotion = useReducedMotion()

  // State
  const [inputText, setInputText] = useState("")
  const [mode, setMode] = useState<"smart" | "manual">("smart")
  const [isProcessing, setIsProcessing] = useState(false)

  // Streaming text hook
  const { streamedText, startStream, resetStream } = useStreamingText({
    speed: 40, // 40ms per character (middle of 30-50ms range)
  })
  // Note: hook also returns isStreaming, but we use component's isProcessing state instead
  // isProcessing = AI processing duration (includes streaming + simulated API call time)
  // isStreaming = text animation duration only
  // We keep isProcessing true for full 2 seconds to simulate API call, not just streaming time

  // Motion value for swipe gesture (mobile)
  const y = useMotionValue(0)
  // Swipe threshold - dismiss if dragged down more than this
  const SWIPE_DISMISS_THRESHOLD = 100

  // Handle smart input submission
  const handleSmartSubmit = async () => {
    if (!inputText.trim()) return

    setIsProcessing(true)

    // Story 3.3: Call AI parsing service
    // For now: simulate streaming with placeholder commentary
    startStream("Got it! Parsing that expense for you...")

    // Story 3.4: Show preview card and confirm
    // Reset isProcessing after streaming completes (isStreaming becomes false)
    // For now: use setTimeout to simulate processing delay
    setTimeout(() => {
      setIsProcessing(false)
      // In Story 3.4, we would show the preview card here
    }, 2000)
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

  // Handle swipe-to-dismiss gesture
  const handleDragEnd = (_: any, info: PanInfo) => {
    if (info.offset.y > SWIPE_DISMISS_THRESHOLD) {
      handleClose()
    } else {
      // Spring back to position
      y.set(0)
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
    onOpenChange(false)
    // Reset state after close animation
    setTimeout(() => {
      setInputText("")
      setMode("smart")
      setIsProcessing(false)
      resetStream()
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

  // Reset input when modal opens
  useEffect(() => {
    if (open) {
      setInputText("")
      setMode("smart")
      setIsProcessing(false)
      resetStream()
    }
  }, [open, resetStream])

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

        {/* Modal content with drag gesture on mobile */}
        <DialogPrimitive.Content asChild>
          <motion.div
            // Swipe down to dismiss on mobile/touch devices
            drag="y"
            dragConstraints={{ top: 0, bottom: 0 }}
            dragElastic={0.2}
            onDragEnd={handleDragEnd}
            style={{ y }}
            // Modal variants
            variants={shouldReduceMotion ? undefined : modalVariants}
            initial="hidden"
            animate="visible"
            exit={{ y: "100%", opacity: 0, transition: { duration: 0.2 } }}
            className={cn(
              // Mobile: full-screen from bottom (responsive classes, no variant needed)
              "fixed inset-x-0 bottom-0 z-50 w-full",
              "bg-surface rounded-t-lg shadow-lg",
              // Desktop: centered dialog
              "lg:fixed lg:inset-auto lg:left-1/2 lg:top-1/2 lg:-translate-x-1/2 lg:-translate-y-1/2",
              "lg:max-w-[600px] lg:w-full lg:max-h-[80vh] lg:rounded-lg",
              "lg:border lg:border-border"
            )}
          >
            {/* Focus trap wraps all focusable content */}
            <FocusTrap active={open}>
              {(focusTrapProps: React.HTMLAttributes<HTMLDivElement>) => (
                <div
                  {...focusTrapProps}
                  className="flex flex-col h-full max-h-[80vh] p-6"
                >
                  {/* Drag handle indicator - visual affordance for swipe gesture */}
                  <div
                    className={cn(
                      "flex justify-center pt-1 pb-2 lg:hidden",
                      "touch-none"
                    )}
                    aria-hidden="true"
                  >
                    <div className="w-12 h-1.5 bg-muted rounded-full" />
                  </div>

                  {/* Header */}
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="title text-text-primary">
                      {entryPoint === "dashboard" ? "Add Expense" : "Add Expense to Group"}
                    </h2>
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

                  {mode === "smart" ? (
                    <>
                      {/* AI Commentary Bubble */}
                      <AICommentaryBubble
                        text={streamedText}
                        isProcessing={isProcessing}
                        personality="friendly" // Will be group-specific in Story 8.1
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

                      {/* Expense Preview Card */}
                      <ExpensePreviewCard
                        data={null} // No parsed data yet (Story 3.3)
                        status="placeholder"
                      />

                      {/* Submit Button */}
                      <button
                        type="button"
                        onClick={handleSmartSubmit}
                        disabled={!inputText.trim() || isProcessing}
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
                        {groupId ? (
                          <ExpenseForm
                            groupId={groupId}
                            onSuccess={handleManualSuccess}
                            onCancel={() => setMode("smart")}
                          />
                        ) : (
                          <p className="text-text-muted text-sm">
                            Please select a group first
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
              )}
            </FocusTrap>
          </motion.div>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  )
}

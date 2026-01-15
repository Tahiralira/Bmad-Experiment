import * as React from "react"
import * as DialogPrimitive from "@radix-ui/react-dialog"
import { AnimatePresence, motion, type PanInfo, type TargetAndTransition, useReducedMotion, useMotionValue } from "framer-motion"
import { X } from "lucide-react"
import FocusTrap from "focus-trap-react"

import { cn } from "@/lib/utils"

// ============================================================================
// Types and Interfaces
// ============================================================================

export interface SmartInputModalProps {
  /** Whether the modal is open */
  isOpen: boolean
  /** Called when modal should close */
  onClose: () => void
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
// AI Commentary Bubble Sub-Component
// ============================================================================

export interface AICommentaryBubbleProps {
  children: React.ReactNode
  /** Whether the bubble is currently visible */
  isVisible?: boolean
}

/**
 * AI Commentary Bubble - displays streaming AI commentary above the input field.
 * Shows a tail pointing down toward the input.
 */
export function AICommentaryBubble({ children, isVisible = false }: AICommentaryBubbleProps) {
  const shouldReduceMotion = useReducedMotion()

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2, ease: "easeOut" }}
          className={cn(
            "mb-4 p-4 rounded-lg relative",
            "bg-surface-elevated border border-border shadow-md",
            "text-secondary text-sm"
          )}
          aria-live="polite"
        >
          {/* Tail indicator pointing down */}
          <span
            className={cn(
              "absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-full",
              "border-8 border-transparent border-t-surface-elevated"
            )}
            aria-hidden="true"
          />
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  )
}

// ============================================================================
// Expense Preview Card Sub-Component
// ============================================================================

export interface ExpensePreviewCardProps {
  /** Whether preview is in loading state */
  isLoading?: boolean
  /** Parsed amount to display */
  amount?: string
  /** Parsed description to display */
  description?: string
  /** Split type (equal, custom, etc.) */
  splitType?: string
  /** Member list with include/exclude indicators */
  members?: Array<{ name: string; included: boolean }>
}

/**
 * Expense Preview Card - displays parsed expense data below the input field.
 * Shows skeleton state while loading, populated data when ready.
 */
export function ExpensePreviewCard({
  isLoading = false,
  amount,
  description,
  splitType,
  members,
}: ExpensePreviewCardProps) {
  const shouldReduceMotion = useReducedMotion()

  if (isLoading) {
    return (
      <div className={cn("mt-4 p-4 rounded-lg", "bg-surface-elevated border border-border")}>
        <div className="animate-pulse flex space-x-4">
          <div className="flex-1 space-y-3">
            <div className="h-4 bg-muted rounded w-3/4" />
            <div className="h-4 bg-muted rounded w-1/2" />
            <div className="h-4 bg-muted rounded w-1/3" />
          </div>
        </div>
      </div>
    )
  }

  return (
    <AnimatePresence>
      {(amount || description) && (
        <motion.div
          initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0 }}
          transition={{ type: "spring", stiffness: 300, damping: 30, duration: 0.3 }}
          className={cn("mt-4 p-4 rounded-lg", "bg-surface-elevated border border-border")}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-primary font-medium">{description || "Expense"}</span>
            <span className="text-primary font-semibold">{amount || "Rs 0"}</span>
          </div>
          {splitType && <div className="text-sm text-muted">Split: {splitType}</div>}
          {members && (
            <div className="flex flex-wrap gap-1 mt-2">
              {members.map((m, i) => (
                <span
                  key={i}
                  className={cn(
                    "px-2 py-1 rounded-full text-xs",
                    m.included
                      ? "bg-action/10 text-action"
                      : "bg-muted text-muted-foreground line-through"
                  )}
                >
                  {m.name}
                </span>
              ))}
            </div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  )
}

// ============================================================================
// Group Selector Sub-Component
// ============================================================================

export interface GroupSelectorProps {
  /** Available groups to select from */
  groups: Array<{ id: string; name: string; memberCount: number }>
  /** Currently selected group ID */
  selectedGroupId?: string
  /** Called when a group is selected */
  onSelect: (groupId: string) => void
}

/**
 * Group Selector - allows user to select which group the expense belongs to.
 * Only shown when entering from dashboard (no pre-selected group).
 */
export function GroupSelector({ groups, selectedGroupId, onSelect }: GroupSelectorProps) {
  return (
    <div className="mt-4">
      <label className="block text-sm font-medium text-primary mb-2">Select Group</label>
      <div className="grid grid-cols-2 gap-2">
        {groups.map((group) => (
          <button
            key={group.id}
            type="button"
            onClick={() => onSelect(group.id)}
            className={cn(
              "p-3 rounded-lg text-left transition-colors",
              "border",
              selectedGroupId === group.id
                ? "bg-action/10 border-action text-action"
                : "bg-surface border-border hover:border-action"
            )}
          >
            <span className="block font-medium truncate">{group.name}</span>
            <span className="text-sm text-muted">{group.memberCount} members</span>
          </button>
        ))}
      </div>
    </div>
  )
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
 * - AI commentary bubble area (above input, placeholder for Epic 3)
 * - Expense preview card area (below input, placeholder for Epic 3)
 * - Group selector when entering from dashboard
 * - Close via X button, Escape key, backdrop tap, or swipe down
 * - Full keyboard accessibility with focus trap
 * - Reduced motion support
 */
export function SmartInputModal({
  isOpen,
  onClose,
  groupId,
  entryPoint = "dashboard",
  triggerRef,
}: SmartInputModalProps) {
  const shouldReduceMotion = useReducedMotion()
  const [inputValue, setInputValue] = React.useState("")
  const [selectedGroupId, setSelectedGroupId] = React.useState<string | undefined>(groupId)

  // Motion value for swipe gesture (mobile)
  const y = useMotionValue(0)
  // Swipe threshold - dismiss if dragged down more than this
  const SWIPE_DISMISS_THRESHOLD = 100

  // Handle form submission (via button or keyboard)
  const handleSubmit = React.useCallback(() => {
    if (inputValue.trim()) {
      // Placeholder for Epic 3: submit expense to AI parsing
      // For now, just clear the input and show console log
      console.log("Expense input:", inputValue)
      setInputValue("")
    }
  }, [inputValue])

  // Handle keyboard events in textarea
  // On desktop: Ctrl+Enter or Cmd+Enter submits (Enter alone creates new line)
  const handleKeyDown = React.useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault()
      handleSubmit()
    }
  }, [handleSubmit])

  // Handle swipe-to-dismiss gesture
  const handleDragEnd = (_: any, info: PanInfo) => {
    if (info.offset.y > SWIPE_DISMISS_THRESHOLD) {
      onClose()
    } else {
      // Spring back to position
      y.set(0)
    }
  }

  // Handle Escape key
  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose()
      }
    }
    window.addEventListener("keydown", handleEscape)
    return () => window.removeEventListener("keydown", handleEscape)
  }, [isOpen, onClose])

  // Return focus to trigger (Agent Orb) when modal closes
  // Delay must be longer than exit animation duration (200ms) to ensure smooth transition
  React.useEffect(() => {
    if (!isOpen && triggerRef?.current) {
      const timeoutId = setTimeout(() => {
        triggerRef.current?.focus()
      }, 250) // 250ms > 200ms exit animation duration
      return () => clearTimeout(timeoutId)
    }
  }, [isOpen, triggerRef])

  // Reset input when modal opens/closes
  React.useEffect(() => {
    if (!isOpen) {
      setInputValue("")
    }
  }, [isOpen])

  // Placeholder groups (will be replaced with real data in Epic 3)
  const mockGroups = [
    { id: "1", name: "Weekend Trip", memberCount: 4 },
    { id: "2", name: "Roommate Expenses", memberCount: 3 },
  ]

  return (
    <DialogPrimitive.Root open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogPrimitive.Portal>
        {/* Backdrop overlay */}
        <DialogPrimitive.Overlay
          className={cn(
            "fixed inset-0 z-50 bg-black/30",
            "data-[state=open]:animate-in data-[state=closed]:animate-out",
            "data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0"
          )}
          onClick={onClose}
        />

        {/* Modal content with drag gesture on mobile */}
        <DialogPrimitive.Content
          asChild
        >
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
              // Mobile: full-screen from bottom
              "fixed inset-x-0 bottom-0 z-50 w-full",
              "bg-surface rounded-t-lg shadow-lg",
              // Desktop: centered dialog
              "lg:fixed lg:inset-auto lg:left-1/2 lg:top-1/2 lg:-translate-x-1/2 lg:-translate-y-1/2",
              "lg:max-w-[600px] lg:w-full lg:max-h-[80vh] lg:rounded-lg",
              "lg:border lg:border-border"
            )}
          >
            {/* Focus trap wraps all focusable content */}
            <FocusTrap active={isOpen}>
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
                    <h2 className="text-lg font-semibold text-primary">
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

                  {/* AI Commentary Bubble Placeholder */}
                  {/* Will be populated with streaming AI text in Epic 3 */}
                  <AICommentaryBubble isVisible={false}>
                    AI commentary will appear here...
                  </AICommentaryBubble>

                  {/* Input Field */}
                  <textarea
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Paid 150 for dinner, split with everyone except Tom"
                    className={cn(
                      "w-full p-4 rounded-lg min-h-[100px] resize-none",
                      "bg-surface border border-border",
                      "text-primary placeholder:text-muted",
                      "focus:outline-none focus:ring-2 focus:ring-action focus:border-action"
                    )}
                    aria-label="Expense description"
                  />

                  {/* Preview Card Placeholder - skeleton state */}
                  {/* Will show parsed expense data in Epic 3 */}
                  <ExpensePreviewCard isLoading={false} />

                  {/* Group Selector - only on dashboard when no groupId provided */}
                  {entryPoint === "dashboard" && !groupId && (
                    <GroupSelector
                      groups={mockGroups}
                      selectedGroupId={selectedGroupId}
                      onSelect={setSelectedGroupId}
                    />
                  )}

                  {/* Submit Button */}
                  {/* Disabled/placeholder in this story - actual submission in Epic 3 */}
                  <button
                    type="button"
                    onClick={handleSubmit}
                    disabled={!inputValue.trim()}
                    className={cn(
                      "mt-6 w-full py-3 rounded-lg font-medium",
                      "bg-action text-white",
                      "hover:bg-action-hover transition-colors",
                      "disabled:opacity-50 disabled:cursor-not-allowed",
                      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    )}
                  >
                    Add Expense
                  </button>
                </div>
              )}
            </FocusTrap>
          </motion.div>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  )
}

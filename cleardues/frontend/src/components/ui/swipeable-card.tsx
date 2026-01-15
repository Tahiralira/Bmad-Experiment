import * as React from "react"
import { motion, useReducedMotion, type TargetAndTransition } from "framer-motion"
import { type LucideIcon } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "./button"

// =============================================================================
// CONSTANTS
// =============================================================================

const REVEAL_THRESHOLD = 30 // % - Reveal action at this threshold
const TRIGGER_THRESHOLD = 60 // % - Auto-trigger at this threshold
const HAPTIC_LIGHT_DURATION = 10 // ms
const HAPTIC_MEDIUM_DURATION = 20 // ms
const SNAP_BACK_DURATION = 0.3 // seconds
const SPRING_STIFFNESS = 300
const SPRING_DAMPING = 30

// =============================================================================
// TYPES
// =============================================================================

export interface SwipeableAction {
  /** Icon component to display for the action */
  icon: LucideIcon
  /** Accessible label for the action */
  label: string
  /** Callback when action is triggered (via swipe or click) */
  onTrigger: () => void
  /** Optional variant for action button (default: 'outline' for left, 'default' for right) */
  variant?: "default" | "outline" | "destructive" | "secondary" | "ghost" | "link"
}

export interface SwipeableCardProps {
  /** Card content to render */
  children: React.ReactNode
  /** Action revealed on left swipe (e.g., Edit) */
  leftAction?: SwipeableAction
  /** Action revealed on right swipe (e.g., Mark Paid) */
  rightAction?: SwipeableAction
  /** Disable swipe gestures */
  disabled?: boolean
  /** Additional className for container */
  className?: string
  /** Aria label for the card group */
  ariaLabel?: string
}

// =============================================================================
// HAPTIC FEEDBACK
// =============================================================================

function triggerHaptic(intensity: "light" | "medium" | "success") {
  if ("vibrate" in navigator) {
    const duration =
      intensity === "light" ? HAPTIC_LIGHT_DURATION : intensity === "medium" ? HAPTIC_MEDIUM_DURATION : 30
    try {
      navigator.vibrate(duration)
    } catch {
      // Silently fail if vibration not supported
    }
  }
}

// =============================================================================
// SNAP BACK ANIMATION
// =============================================================================

const snapBackAnimation: TargetAndTransition = {
  x: 0,
  transition: {
    type: "spring",
    stiffness: SPRING_STIFFNESS,
    damping: SPRING_DAMPING,
    duration: SNAP_BACK_DURATION,
  },
}

const triggerAnimation: TargetAndTransition = {
  scale: 0.95,
  opacity: 0,
  transition: {
    duration: 0.1,
    ease: "easeIn",
  },
}

// =============================================================================
// ACTION BUTTON COMPONENT
// =============================================================================

interface ActionButtonProps {
  action: SwipeableAction
  side: "left" | "right"
  isVisible: boolean
  onTrigger: () => void
}

function ActionButton({ action, side, isVisible, onTrigger }: ActionButtonProps) {
  const { icon: Icon, label, variant } = action

  return (
    <motion.button
      type="button"
      onClick={onTrigger}
      aria-label={label}
      className={cn(
        "absolute top-0 bottom-0 z-20 flex items-center justify-center px-4",
        "min-h-[44px]", // Minimum touch target
        // Base: hidden by default
        "opacity-0",
        // Desktop hover visibility (md+ breakpoint)
        "md:group-hover:opacity-100",
        // Focus visibility - buttons become visible when focused
        "focus-visible:opacity-100",
        // Mobile swipe visibility: override with !important
        isVisible && "!opacity-100",
        // Smooth transition for opacity changes
        "transition-opacity duration-150 ease-out",
        // Position
        side === "left" ? "left-0" : "right-0",
        // Focus styles
        "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-inset"
      )}
      initial={false}
      animate={{ opacity: isVisible ? 1 : 0 }}
      transition={{ duration: 0.15 }}
    >
      <Button
        variant={variant ?? (side === "left" ? "outline" : "default")}
        size="sm"
        className={cn(
          "shadow-sm",
          "h-12 min-h-[44px] px-4", // Ensure minimum touch target
          "focus-visible:ring-2 focus-visible:ring-ring"
        )}
      >
        <Icon className="size-4" aria-hidden="true" />
        <span className="sr-only">{label}</span>
      </Button>
    </motion.button>
  )
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

function SwipeableCardInner(
  {
    children,
    leftAction,
    rightAction,
    disabled = false,
    className,
    ariaLabel = "Swipeable card",
  }: SwipeableCardProps,
  forwardedRef: React.Ref<HTMLDivElement>
) {
  const shouldReduceMotion = useReducedMotion()

  // Refs
  const cardRef = React.useRef<HTMLDivElement>(null)
  const dragConstraintsRef = React.useRef({ left: 0, right: 0 })

  // Track swipe state
  const [dragOffset, setDragOffset] = React.useState(0)
  const [isDragging, setIsDragging] = React.useState(false)
  const [isLeftRevealed, setIsLeftRevealed] = React.useState(false)
  const [isRightRevealed, setIsRightRevealed] = React.useState(false)
  const [isAnimating, setIsAnimating] = React.useState(false)
  const hasTriggeredRef = React.useRef(false)

  // Combined ref handling
  React.useImperativeHandle(forwardedRef, () => cardRef.current!)

  // Calculate drag constraints based on card width
  React.useEffect(() => {
    const card = cardRef.current
    if (!card) return

    const updateConstraints = () => {
      const width = card.offsetWidth
      // Allow dragging up to 70% of card width in either direction
      const maxDrag = width * 0.7
      dragConstraintsRef.current = { left: -maxDrag, right: maxDrag }
    }

    updateConstraints()

    // Update on resize
    const resizeObserver = new ResizeObserver(updateConstraints)
    resizeObserver.observe(card)

    return () => resizeObserver.disconnect()
  }, [])

  // Calculate swipe percentage
  const getSwipePercent = React.useCallback(
    (offset: number) => {
      const card = cardRef.current
      if (!card) return 0
      const width = card.offsetWidth
      return Math.abs(offset / width) * 100
    },
    []
  )

  // Reset reveal states
  const resetRevealStates = React.useCallback(() => {
    setIsLeftRevealed(false)
    setIsRightRevealed(false)
    hasTriggeredRef.current = false
  }, [])

  // Handle drag start
  const handleDragStart = () => {
    if (disabled || isAnimating) return
    setIsDragging(true)
    hasTriggeredRef.current = false
  }

  // Handle drag - update reveal states based on thresholds
  const handleDrag = (_: unknown, info: { offset: { x: number } }) => {
    if (disabled || isAnimating || hasTriggeredRef.current) return

    const offset = info.offset.x
    setDragOffset(offset)
    const percent = getSwipePercent(offset)

    // Determine which side we're swiping
    const swipingLeft = offset < 0
    const swipingRight = offset > 0

    // Update reveal states
    if (swipingLeft && leftAction && percent >= REVEAL_THRESHOLD) {
      if (!isLeftRevealed) {
        setIsLeftRevealed(true)
        triggerHaptic("light")
      }
    } else if (swipingLeft) {
      setIsLeftRevealed(false)
    }

    if (swipingRight && rightAction && percent >= REVEAL_THRESHOLD) {
      if (!isRightRevealed) {
        setIsRightRevealed(true)
        triggerHaptic("light")
      }
    } else if (swipingRight) {
      setIsRightRevealed(false)
    }
  }

  // Handle drag end - check if we should trigger action
  const handleDragEnd = (_: unknown, info: { offset: { x: number } }) => {
    if (disabled || isAnimating || hasTriggeredRef.current) {
      setIsDragging(false)
      return
    }

    const offset = info.offset.x
    const percent = getSwipePercent(offset)

    // Check trigger threshold
    if (percent >= TRIGGER_THRESHOLD) {
      const swipingLeft = offset < 0
      const swipingRight = offset > 0

      if (swipingLeft && leftAction) {
        hasTriggeredRef.current = true
        setIsAnimating(true)
        triggerHaptic("medium")

        // Animate out then trigger
        setTimeout(() => {
          leftAction.onTrigger()
          setIsAnimating(false)
          resetRevealStates()
        }, 100)
      } else if (swipingRight && rightAction) {
        hasTriggeredRef.current = true
        setIsAnimating(true)
        triggerHaptic("medium")

        // Animate out then trigger
        setTimeout(() => {
          rightAction.onTrigger()
          setIsAnimating(false)
          resetRevealStates()
        }, 100)
      } else {
        // Snap back
        resetRevealStates()
      }
    } else {
      // Below trigger threshold - snap back
      resetRevealStates()
    }

    setIsDragging(false)
  }

  // Keyboard handler for accessibility
  const handleKeyDown = React.useCallback(
    (event: React.KeyboardEvent) => {
      if (disabled || isAnimating) return

      // Arrow keys reveal actions
      if (event.key === "ArrowLeft" && leftAction) {
        event.preventDefault()
        setIsLeftRevealed(true)
        setIsRightRevealed(false)
        triggerHaptic("light")
      } else if (event.key === "ArrowRight" && rightAction) {
        event.preventDefault()
        setIsRightRevealed(true)
        setIsLeftRevealed(false)
        triggerHaptic("light")
      } else if (event.key === "Escape") {
        resetRevealStates()
      }
      // Enter or Space triggers the currently revealed action
      else if ((event.key === "Enter" || event.key === " ") && !isAnimating) {
        if (isLeftRevealed && leftAction) {
          event.preventDefault()
          setIsAnimating(true)
          triggerHaptic("medium")
          setTimeout(() => {
            leftAction.onTrigger()
            setIsAnimating(false)
            resetRevealStates()
          }, 100)
        } else if (isRightRevealed && rightAction) {
          event.preventDefault()
          setIsAnimating(true)
          triggerHaptic("medium")
          setTimeout(() => {
            rightAction.onTrigger()
            setIsAnimating(false)
            resetRevealStates()
          }, 100)
        }
      }
    },
    [disabled, isAnimating, leftAction, rightAction, resetRevealStates, isLeftRevealed, isRightRevealed]
  )

  // Get animation for the card
  const getCardAnimation = (): TargetAndTransition | undefined => {
    if (shouldReduceMotion) return undefined
    if (isAnimating) return triggerAnimation
    return { x: dragOffset }
  }

  // Generate swipe indicator colors
  const leftIndicatorColor = leftAction
    ? "bg-action/10"
    : "bg-destructive/10"
  const rightIndicatorColor = rightAction
    ? "bg-success/10"
    : "bg-destructive/10"

  return (
    <div
      ref={cardRef}
      className={cn(
        "group relative", // For desktop hover detection
        "w-full",
        className
      )}
      role="group"
      aria-label={ariaLabel}
    >
      {/* Left swipe indicator background */}
      <motion.div
        className={cn(
          "absolute inset-y-0 left-0 z-10 rounded-lg",
          "pointer-events-none",
          leftIndicatorColor,
          "origin-left"
        )}
        animate={{
          scaleX: dragOffset < 0 ? Math.min(Math.abs(dragOffset) / (cardRef.current?.offsetWidth || 300), 0.6) : 0,
        }}
        transition={{ duration: 0.1 }}
        aria-hidden="true"
      />

      {/* Right swipe indicator background */}
      <motion.div
        className={cn(
          "absolute inset-y-0 right-0 z-10 rounded-lg",
          "pointer-events-none",
          rightIndicatorColor,
          "origin-right"
        )}
        animate={{
          scaleX: dragOffset > 0 ? Math.min(dragOffset / (cardRef.current?.offsetWidth || 300), 0.6) : 0,
        }}
        transition={{ duration: 0.1 }}
        aria-hidden="true"
      />

      {/* Left action button */}
      {leftAction && (
        <ActionButton
          action={leftAction}
          side="left"
          isVisible={isLeftRevealed}
          onTrigger={() => {
            triggerHaptic("medium")
            leftAction.onTrigger()
            resetRevealStates()
          }}
        />
      )}

      {/* Right action button */}
      {rightAction && (
        <ActionButton
          action={rightAction}
          side="right"
          isVisible={isRightRevealed}
          onTrigger={() => {
            triggerHaptic("medium")
            rightAction.onTrigger()
            resetRevealStates()
          }}
        />
      )}

      {/* Draggable card content */}
      <motion.div
        drag={disabled ? false : "x"}
        dragConstraints={shouldReduceMotion ? { left: 0, right: 0 } : dragConstraintsRef.current}
        dragElastic={0.1}
        onDragStart={handleDragStart}
        onDrag={handleDrag}
        onDragEnd={handleDragEnd}
        onKeyDown={handleKeyDown}
        animate={getCardAnimation()}
        transition={
          shouldReduceMotion
            ? { duration: 0 }
            : !isDragging && !isAnimating
              ? snapBackAnimation.transition
              : undefined
        }
        className={cn(
          "relative z-20 rounded-lg",
          "cursor-grab active:cursor-grabbing",
          disabled && "cursor-default",
          "focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2"
        )}
        style={{
          touchAction: "pan-y", // Allow vertical scrolling, handle horizontal ourselves
        }}
        tabIndex={0}
      >
        {children}
      </motion.div>

      {/* Screen reader only hint for swipe actions */}
      <div className="sr-only">
        {leftAction && `Swipe left for ${leftAction.label}`}
        {rightAction && `Swipe right for ${rightAction.label}`}
      </div>
    </div>
  )
}

// Forward ref wrapper for SwipeableCard
const SwipeableCard = React.forwardRef(SwipeableCardInner) as (
  props: SwipeableCardProps & { ref?: React.Ref<HTMLDivElement> }
) => React.JSX.Element

export { SwipeableCard }

// Display name for debugging
;(SwipeableCard as React.ForwardRefExoticComponent<SwipeableCardProps & React.RefAttributes<HTMLDivElement>>).displayName =
  "SwipeableCard"

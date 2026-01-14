import * as React from "react"
import { motion, useReducedMotion, type TargetAndTransition } from "framer-motion"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const agentOrbVariants = cva(
  // Base styles: squircle shape with proper border-radius
  "relative inline-flex items-center justify-center rounded-[28%] font-medium transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      size: {
        sm: "size-12", // 48px
        md: "size-14", // 56px
        lg: "size-16", // 64px
      },
    },
    defaultVariants: {
      size: "md",
    },
  }
)

export interface AgentOrbProps
  extends Omit<React.ComponentProps<typeof motion.button>, "size">,
    VariantProps<typeof agentOrbVariants> {
  /** Callback when the orb is clicked */
  onClick?: () => void
  /** Shows processing/loading state with faster pulse */
  isProcessing?: boolean
  /** Triggers success animation with amber flash */
  showSuccess?: boolean
  /** Custom aria-label (default: "Add new expense") */
  ariaLabel?: string
  /** Additional className for container */
  className?: string
}

// Animation definitions with proper typing
const idleAnimation: TargetAndTransition = {
  scale: [1, 1.02, 1],
  opacity: [0.95, 1, 0.95],
  transition: {
    duration: 2.5,
    repeat: Infinity,
    ease: "easeInOut",
  },
}

const processingAnimation: TargetAndTransition = {
  scale: [1, 1.03, 1],
  opacity: [0.9, 1, 0.9],
  transition: {
    duration: 0.5,
    repeat: Infinity,
    ease: "easeInOut",
  },
}

const successAnimation: TargetAndTransition = {
  scale: [1, 1.1, 1],
  transition: {
    duration: 0.3,
    ease: [0.34, 1.56, 0.64, 1], // spring easing
  },
}

// Glow animations with proper typing
const idleGlow: TargetAndTransition = {
  boxShadow: [
    "0 0 20px rgba(61, 154, 148, 0.3)",
    "0 0 30px rgba(61, 154, 148, 0.5)",
    "0 0 20px rgba(61, 154, 148, 0.3)",
  ],
  transition: {
    duration: 2.5,
    repeat: Infinity,
    ease: "easeInOut",
  },
}

const processingGlow: TargetAndTransition = {
  boxShadow: [
    "0 0 20px rgba(61, 154, 148, 0.4)",
    "0 0 35px rgba(61, 154, 148, 0.7)",
    "0 0 20px rgba(61, 154, 148, 0.4)",
  ],
  transition: {
    duration: 0.5,
    repeat: Infinity,
    ease: "easeInOut",
  },
}

const successGlow: TargetAndTransition = {
  boxShadow: [
    "0 0 0 rgba(212, 168, 87, 0)",
    "0 0 40px rgba(212, 168, 87, 0.8)",
    "0 0 0 rgba(212, 168, 87, 0)",
  ],
  transition: {
    duration: 0.3,
    ease: "easeOut",
  },
}

// Static styles for reduced motion
const staticStyles: React.CSSProperties = {
  boxShadow: "0 0 20px rgba(61, 154, 148, 0.4)",
}

function AgentOrb({
  className,
  size,
  onClick,
  isProcessing = false,
  showSuccess = false,
  ariaLabel = "Add new expense",
  ...props
}: AgentOrbProps) {
  const shouldReduceMotion = useReducedMotion()
  const [isSuccessAnimating, setIsSuccessAnimating] = React.useState(false)

  // Handle success state trigger
  React.useEffect(() => {
    if (showSuccess && !isSuccessAnimating) {
      setIsSuccessAnimating(true)
      // Auto-reset success animation after it completes
      const timer = setTimeout(() => {
        setIsSuccessAnimating(false)
      }, 300)
      return () => clearTimeout(timer)
    }
  }, [showSuccess, isSuccessAnimating])

  // Get the appropriate scale animation
  const getScaleAnimation = (): TargetAndTransition | undefined => {
    if (shouldReduceMotion) return undefined
    if (isSuccessAnimating) return successAnimation
    if (isProcessing) return processingAnimation
    return idleAnimation
  }

  // Get the appropriate glow animation
  const getGlowAnimation = (): TargetAndTransition | undefined => {
    if (shouldReduceMotion) return undefined
    if (isSuccessAnimating) return successGlow
    if (isProcessing) return processingGlow
    return idleGlow
  }

  // Handle keyboard activation
  const handleKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      onClick?.()
    }
  }

  return (
    <motion.button
      type="button"
      tabIndex={0}
      aria-label={ariaLabel}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      className={cn(
        agentOrbVariants({ size }),
        // Background gradient
        "bg-gradient-to-br from-action to-action-hover",
        // Text/icon color
        "text-white",
        className
      )}
      // Animation properties
      animate={getScaleAnimation()}
      whileHover={shouldReduceMotion ? undefined : { scale: 1.05 }}
      whileTap={shouldReduceMotion ? undefined : { scale: 0.95 }}
      transition={
        shouldReduceMotion
          ? undefined
          : {
              type: "spring",
              stiffness: 400,
              damping: 17,
            }
      }
      // Glow effect via inline style (animated separately)
      style={shouldReduceMotion ? staticStyles : undefined}
      {...props}
    >
      {/* Animated glow layer */}
      <motion.span
        className="pointer-events-none absolute inset-0 rounded-[28%]"
        animate={getGlowAnimation()}
        aria-hidden="true"
      />

      {/* Success flash overlay */}
      {isSuccessAnimating && !shouldReduceMotion && (
        <motion.span
          className="pointer-events-none absolute inset-0 rounded-[28%] bg-success"
          initial={{ opacity: 0 }}
          animate={{ opacity: [0, 0.6, 0] }}
          transition={{ duration: 0.3, ease: "easeOut" }}
          aria-hidden="true"
        />
      )}

      {/* Ripple effect container */}
      <RippleEffect shouldReduceMotion={shouldReduceMotion ?? false} />

      {/* Inner content (optional icon or spark) */}
      <span className="relative z-10">
        <SparkIcon />
      </span>
    </motion.button>
  )
}

// Ripple effect on click
function RippleEffect({ shouldReduceMotion }: { shouldReduceMotion: boolean }) {
  const [ripples, setRipples] = React.useState<{ id: number; x: number; y: number }[]>([])

  const handleClick = (event: React.MouseEvent<HTMLSpanElement>) => {
    if (shouldReduceMotion) return

    const rect = event.currentTarget.getBoundingClientRect()
    const x = event.clientX - rect.left - rect.width / 2
    const y = event.clientY - rect.top - rect.height / 2
    const id = Date.now()

    setRipples((prev) => [...prev, { id, x, y }])

    // Remove ripple after animation
    setTimeout(() => {
      setRipples((prev) => prev.filter((r) => r.id !== id))
    }, 600)
  }

  return (
    <span
      className="pointer-events-auto absolute inset-0 overflow-hidden rounded-[28%]"
      onClick={handleClick}
      aria-hidden="true"
    >
      {ripples.map((ripple) => (
        <motion.span
          key={ripple.id}
          className="absolute size-full rounded-full bg-white/30"
          initial={{ scale: 0, opacity: 0.5, x: ripple.x, y: ripple.y }}
          animate={{ scale: 2.5, opacity: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        />
      ))}
    </span>
  )
}

// Spark/star icon for the orb center
function SparkIcon() {
  return (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="size-6"
      aria-hidden="true"
    >
      <path d="M12 3v18M3 12h18M5.6 5.6l12.8 12.8M5.6 18.4l12.8-12.8" />
    </svg>
  )
}

export { AgentOrb, agentOrbVariants }

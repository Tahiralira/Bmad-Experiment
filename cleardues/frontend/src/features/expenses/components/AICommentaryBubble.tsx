import { useEffect, useState } from "react"
import { motion, useReducedMotion } from "framer-motion"

import { cn } from "@/lib/utils"

export interface AICommentaryBubbleProps {
  /** The text to display (streaming or complete) */
  text: string
  /** Whether AI is currently processing/generating text */
  isProcessing: boolean
  /** AI personality style for tone customization */
  personality: "professional" | "friendly" | "funny" | "roast"
  /** Additional className for styling */
  className?: string
}

/**
 * AI Commentary Bubble - displays streaming AI commentary above the input field.
 *
 * Features:
 * - Typing indicator (3 dots animation) before stream starts
 * - Smooth fade-in animation
 * - Tail pointing down toward input field
 * - Personality-driven styling
 * - Accessible with aria-live for screen readers
 *
 * @example
 * ```tsx
 * <AICommentaryBubble
 *   text={streamedText}
 *   isProcessing={isProcessing}
 *   personality="friendly"
 * />
 * ```
 */
export function AICommentaryBubble({
  text,
  isProcessing,
  personality: _personality, // Will be used for personality-driven styling in Story 8.1
  className,
}: AICommentaryBubbleProps) {
  const [showTypingIndicator, setShowTypingIndicator] = useState(false)
  const shouldReduceMotion = useReducedMotion()

  // Show typing indicator after 300ms of processing with no text
  useEffect(() => {
    if (isProcessing && !text) {
      const timer = setTimeout(() => setShowTypingIndicator(true), 300)
      return () => clearTimeout(timer)
    } else {
      setShowTypingIndicator(false)
    }
  }, [isProcessing, text])

  // Don't render if idle (no text and not processing)
  if (!text && !isProcessing) {
    return null
  }

  return (
    <motion.div
      initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className={cn(
        "mb-4 p-4 rounded-lg relative",
        "bg-surface-elevated border border-border shadow-sm",
        "text-text-primary text-sm",
        className
      )}
      aria-live="polite"
      aria-label="AI commentary"
    >
      {/* Tail indicator pointing down to input field */}
      <span
        className={cn(
          "absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-full",
          "border-8 border-transparent border-t-surface-elevated"
        )}
        aria-hidden="true"
      />

      {showTypingIndicator ? (
        // Typing Indicator (3 dots animation)
        <div className="flex items-center gap-1 py-1">
          <span
            className="w-2 h-2 bg-text-muted rounded-full animate-bounce"
            style={{ animationDelay: "0ms" }}
            aria-hidden="true"
          />
          <span
            className="w-2 h-2 bg-text-muted rounded-full animate-bounce"
            style={{ animationDelay: "150ms" }}
            aria-hidden="true"
          />
          <span
            className="w-2 h-2 bg-text-muted rounded-full animate-bounce"
            style={{ animationDelay: "300ms" }}
            aria-hidden="true"
          />
          <span className="sr-only">AI is thinking</span>
        </div>
      ) : (
        // Streamed Text
        <p className="text-body-small leading-relaxed">
          {text || "Processing your expense..."}
        </p>
      )}
    </motion.div>
  )
}

import { useState, useEffect, useRef, useCallback } from "react"

interface UseAutoConfirmOptions {
  /** Whether auto-confirm is enabled (user preference) */
  enabled: boolean
  /** Countdown duration in milliseconds (default: 3000ms) */
  duration?: number
  /** Callback when countdown completes */
  onCountdownComplete: () => void
}

interface UseAutoConfirmReturn {
  /** Current countdown value in seconds */
  countdown: number
  /** Whether countdown is currently in progress */
  isCountingDown: boolean
  /** Start the countdown (no-op if disabled) */
  startCountdown: () => void
  /** Cancel the countdown */
  cancelCountdown: () => void
  /** Reset countdown to initial duration */
  resetCountdown: () => void
}

/**
 * Custom hook for auto-confirm countdown functionality
 *
 * Features:
 * - Configurable countdown duration
 * - Cancel on user interaction
 * - Cleanup on unmount
 * - Respects enabled flag (disabled = manual confirm only)
 *
 * @example
 * ```tsx
 * const { countdown, isCountingDown, startCountdown, cancelCountdown } = useAutoConfirm({
 *   enabled: userPreferences.auto_confirm_enabled,
 *   duration: 3000,
 *   onCountdownComplete: () => onConfirm(editedData)
 * })
 *
 * // Start countdown when component mounts
 * useEffect(() => {
 *   startCountdown()
 * }, [])
 *
 * // Cancel countdown on user interaction
 * const handleEdit = () => {
 *   cancelCountdown()
 *   // ... handle edit
 * }
 * ```
 */
export function useAutoConfirm({
  enabled,
  duration = 3000,
  onCountdownComplete,
}: UseAutoConfirmOptions): UseAutoConfirmReturn {
  const [countdown, setCountdown] = useState(duration / 1000)
  const [isCountingDown, setIsCountingDown] = useState(false)
  const intervalRef = useRef<NodeJS.Timeout | number | null>(null)
  const onCompleteRef = useRef(onCountdownComplete)

  // Keep callback ref updated
  useEffect(() => {
    onCompleteRef.current = onCountdownComplete
  }, [onCountdownComplete])

  /**
   * Start countdown
   * No-op if auto-confirm is disabled
   */
  const startCountdown = useCallback(() => {
    if (!enabled) return

    // Clear any existing interval
    if (intervalRef.current !== null) {
      clearInterval(intervalRef.current)
    }

    setIsCountingDown(true)
    setCountdown(duration / 1000)

    intervalRef.current = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          // Countdown complete
          if (intervalRef.current !== null) {
            clearInterval(intervalRef.current)
          }
          setIsCountingDown(false)
          // Use ref to avoid stale closure
          onCompleteRef.current?.()
          return 0
        }
        return prev - 1
      })
    }, 1000)
  }, [enabled, duration])

  /**
   * Cancel countdown
   * Clears interval and resets state
   */
  const cancelCountdown = useCallback(() => {
    if (intervalRef.current !== null) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    setIsCountingDown(false)
    setCountdown(duration / 1000)
  }, [duration])

  /**
   * Reset countdown to initial duration
   * Does not start countdown automatically
   */
  const resetCountdown = useCallback(() => {
    if (intervalRef.current !== null) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    setIsCountingDown(false)
    setCountdown(duration / 1000)
  }, [duration])

  /**
   * Cleanup interval on unmount
   */
  useEffect(() => {
    return () => {
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current)
      }
    }
  }, [])

  return {
    countdown,
    isCountingDown,
    startCountdown,
    cancelCountdown,
    resetCountdown,
  }
}

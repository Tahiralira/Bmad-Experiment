import * as React from "react"

export interface UseLongPressOptions {
  /** Delay in ms before triggering long-press (default: 500) */
  delay?: number
  /** Called when user cancels (moves finger, releases early) */
  onCancel?: () => void
}

export interface LongPressHandlers {
  onMouseDown: () => void
  onMouseUp: () => void
  onMouseLeave: () => void
  onTouchStart: () => void
  onTouchEnd: () => void
  onTouchMove: () => void
}

/**
 * Detects long-press gestures on both mouse and touch devices.
 *
 * @example
 * ```tsx
 * const longPressHandlers = useLongPress(() => console.log('Long pressed!'), { delay: 500 })
 * <button {...longPressHandlers}>Hold me</button>
 * ```
 */
export function useLongPress(
  callback: () => void,
  options: UseLongPressOptions = {}
): LongPressHandlers {
  const { delay = 500, onCancel } = options
  const timeoutRef = React.useRef<ReturnType<typeof setTimeout> | null>(null)

  const start = React.useCallback(() => {
    timeoutRef.current = setTimeout(() => {
      callback()
    }, delay)
  }, [callback, delay])

  const clear = React.useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
      onCancel?.()
    }
  }, [onCancel])

  return {
    onMouseDown: start,
    onMouseUp: clear,
    onMouseLeave: clear,
    onTouchStart: start,
    onTouchEnd: clear,
    onTouchMove: clear, // Cancel on drag
  }
}

import { useState, useCallback, useRef, useEffect } from "react"

interface UseStreamingTextOptions {
  /** Streaming speed in milliseconds per character (30-50 recommended) */
  speed?: number
}

interface UseStreamingTextReturn {
  /** The currently streamed text */
  streamedText: string
  /** Start streaming the given text */
  startStream: (text: string) => void
  /** Reset the stream to empty state */
  resetStream: () => void
  /** Whether streaming is currently in progress */
  isStreaming: boolean
}

/**
 * Custom hook for streaming text character by character.
 * Creates natural reading pace effect for AI commentary.
 *
 * @param options - Configuration options
 * @param options.speed - Milliseconds per character (default: 40ms)
 *
 * @example
 * ```tsx
 * const { streamedText, startStream, resetStream, isStreaming } = useStreamingText({ speed: 40 })
 *
 * startStream("Got it! Parsing that expense for you...")
 * // streamedText will update: "G" → "Go" → "Got" ... → "Got it!..."
 * ```
 */
export function useStreamingText({
  speed = 40, // Default 40ms per character (middle of 30-50ms range)
}: UseStreamingTextOptions = {}): UseStreamingTextReturn {
  const [streamedText, setStreamedText] = useState("")
  const [isStreaming, setIsStreaming] = useState(false)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  // Use refs to avoid stale closure issues in setInterval callback
  // Without refs, the interval would capture old values of text and index from initial render
  const textRef = useRef("")
  const indexRef = useRef(0)

  const startStream = useCallback((text: string) => {
    // Clear any existing stream
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
    }

    // Reset state
    setIsStreaming(true)
    setStreamedText("")
    textRef.current = text
    indexRef.current = 0

    // Start streaming
    intervalRef.current = setInterval(() => {
      if (indexRef.current < textRef.current.length) {
        setStreamedText((prev) => prev + textRef.current[indexRef.current])
        indexRef.current++
      } else {
        // Streaming complete
        clearInterval(intervalRef.current!)
        setIsStreaming(false)
      }
    }, speed)
  }, [speed])

  const resetStream = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    setStreamedText("")
    setIsStreaming(false)
    textRef.current = ""
    indexRef.current = 0
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [])

  return { streamedText, startStream, resetStream, isStreaming }
}

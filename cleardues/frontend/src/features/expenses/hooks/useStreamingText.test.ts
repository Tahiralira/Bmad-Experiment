/**
 * useStreamingText Hook Tests
 *
 * Tests the streaming text hook that creates character-by-character text animation:
 * - Streams text at specified speed (30-50ms per character)
 * - Resets stream state
 * - Cleans up intervals on unmount
 * - Returns correct state values
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { renderHook, act } from "@testing-library/react"
import { useStreamingText } from "./useStreamingText"

// Note on timing: the hook emits one character per interval tick; the tick
// AFTER the last character clears the interval and sets isStreaming false.
// So completion for N chars needs (N + 1) ticks. All assertions are
// synchronous after advancing fake timers — waitFor polls real time and
// deadlocks under fake timers.
describe("useStreamingText", () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  // ========== Basic Streaming ==========
  describe("Basic Streaming", () => {
    it("streams text at specified speed (AC #9 - 30-50ms)", () => {
      const { result } = renderHook(() => useStreamingText({ speed: 30 }))

      act(() => {
        result.current.startStream("Test")
      })

      // Initial state
      expect(result.current.streamedText).toBe("")
      expect(result.current.isStreaming).toBe(true)

      // Advance timers character by character
      // "Test" has 4 characters, so 4 intervals of 30ms
      act(() => {
        vi.advanceTimersByTime(30) // "T"
      })
      expect(result.current.streamedText).toBe("T")

      act(() => {
        vi.advanceTimersByTime(30) // "e"
      })
      expect(result.current.streamedText).toBe("Te")

      act(() => {
        vi.advanceTimersByTime(30) // "s"
      })
      expect(result.current.streamedText).toBe("Tes")

      act(() => {
        vi.advanceTimersByTime(30) // "t"
      })
      expect(result.current.streamedText).toBe("Test")

      // One more tick completes the stream
      act(() => {
        vi.advanceTimersByTime(30)
      })
      expect(result.current.streamedText).toBe("Test")
      expect(result.current.isStreaming).toBe(false)
    })

    it("uses default speed of 40ms when not specified", () => {
      const { result } = renderHook(() => useStreamingText())

      act(() => {
        result.current.startStream("Hi")
      })

      // "Hi" has 2 characters, 2 intervals of 40ms = 80ms total
      act(() => {
        vi.advanceTimersByTime(80)
      })
      expect(result.current.streamedText).toBe("Hi")

      // Completion tick
      act(() => {
        vi.advanceTimersByTime(40)
      })
      expect(result.current.isStreaming).toBe(false)
    })

    it("streams text within AC #9 range (30-50ms)", () => {
      // Test lower bound (30ms)
      const { result: resultLower } = renderHook(() => useStreamingText({ speed: 30 }))

      act(() => {
        resultLower.current.startStream("A")
      })

      act(() => {
        vi.advanceTimersByTime(30)
      })
      expect(resultLower.current.streamedText).toBe("A")

      // Test upper bound (50ms)
      const { result: resultUpper } = renderHook(() => useStreamingText({ speed: 50 }))

      act(() => {
        resultUpper.current.startStream("B")
      })

      act(() => {
        vi.advanceTimersByTime(50)
      })
      expect(resultUpper.current.streamedText).toBe("B")
    })
  })

  // ========== State Reset ==========
  describe("State Reset", () => {
    it("resets stream state when resetStream is called", () => {
      const { result } = renderHook(() => useStreamingText({ speed: 30 }))

      // Start streaming
      act(() => {
        result.current.startStream("Test")
      })

      expect(result.current.isStreaming).toBe(true)
      expect(result.current.streamedText).toBe("")

      // Reset before completion
      act(() => {
        result.current.resetStream()
      })

      expect(result.current.streamedText).toBe("")
      expect(result.current.isStreaming).toBe(false)
    })

    it("clears interval when resetStream is called", () => {
      const { result } = renderHook(() => useStreamingText({ speed: 30 }))

      act(() => {
        result.current.startStream("Test")
      })

      act(() => {
        result.current.resetStream()
      })

      // Advance timers - should NOT update text since interval was cleared
      act(() => {
        vi.advanceTimersByTime(100)
      })

      expect(result.current.streamedText).toBe("")
    })

    it("starts new stream after reset", () => {
      const { result } = renderHook(() => useStreamingText({ speed: 30 }))

      // First stream
      act(() => {
        result.current.startStream("First")
      })

      act(() => {
        vi.advanceTimersByTime(30)
      })

      expect(result.current.streamedText).toBe("F")

      // Reset and start new stream
      act(() => {
        result.current.resetStream()
        result.current.startStream("Second")
      })

      act(() => {
        vi.advanceTimersByTime(30)
      })

      expect(result.current.streamedText).toBe("S")
    })
  })

  // ========== Return Values ==========
  describe("Return Values", () => {
    it("returns all four required values", () => {
      const { result } = renderHook(() => useStreamingText())

      expect(result.current).toHaveProperty("streamedText")
      expect(result.current).toHaveProperty("startStream")
      expect(result.current).toHaveProperty("resetStream")
      expect(result.current).toHaveProperty("isStreaming")
    })

    it("initializes with empty streamedText", () => {
      const { result } = renderHook(() => useStreamingText())

      expect(result.current.streamedText).toBe("")
    })

    it("initializes with isStreaming false", () => {
      const { result } = renderHook(() => useStreamingText())

      expect(result.current.isStreaming).toBe(false)
    })

    it("provides startStream function", () => {
      const { result } = renderHook(() => useStreamingText())

      expect(typeof result.current.startStream).toBe("function")
    })

    it("provides resetStream function", () => {
      const { result } = renderHook(() => useStreamingText())

      expect(typeof result.current.resetStream).toBe("function")
    })
  })

  // ========== Edge Cases ==========
  describe("Edge Cases", () => {
    it("handles empty string", () => {
      const { result } = renderHook(() => useStreamingText({ speed: 30 }))

      act(() => {
        result.current.startStream("")
      })

      // First tick finds nothing to emit and completes
      act(() => {
        vi.advanceTimersByTime(30)
      })
      expect(result.current.streamedText).toBe("")
      expect(result.current.isStreaming).toBe(false)
    })

    it("handles single character", () => {
      const { result } = renderHook(() => useStreamingText({ speed: 30 }))

      act(() => {
        result.current.startStream("A")
      })

      act(() => {
        vi.advanceTimersByTime(30) // emit "A"
      })
      expect(result.current.streamedText).toBe("A")

      act(() => {
        vi.advanceTimersByTime(30) // completion tick
      })
      expect(result.current.isStreaming).toBe(false)
    })

    it("handles long text", () => {
      const longText = "A".repeat(100)
      const { result } = renderHook(() => useStreamingText({ speed: 10 }))

      act(() => {
        result.current.startStream(longText)
      })

      // Advance all 100 characters + the completion tick
      act(() => {
        vi.advanceTimersByTime(10 * 101)
      })
      expect(result.current.streamedText).toBe(longText)
      expect(result.current.isStreaming).toBe(false)
    })

    it("handles special characters", () => {
      const { result } = renderHook(() => useStreamingText({ speed: 30 }))

      act(() => {
        result.current.startStream("Hello\nWorld\t!")
      })

      // Stream all 13 characters + the completion tick
      act(() => {
        vi.advanceTimersByTime(30 * 14)
      })
      expect(result.current.streamedText).toBe("Hello\nWorld\t!")
      expect(result.current.isStreaming).toBe(false)
    })
  })

  // ========== Cleanup ==========
  describe("Cleanup", () => {
    it("clears interval on unmount", () => {
      const { result, unmount } = renderHook(() => useStreamingText({ speed: 30 }))

      act(() => {
        result.current.startStream("Test")
      })

      expect(result.current.isStreaming).toBe(true)

      // Unmount component
      unmount()

      // Advance timers - interval should be cleared
      act(() => {
        vi.advanceTimersByTime(100)
      })

      // No errors should occur
    })

    it("clears interval when starting new stream", () => {
      const { result } = renderHook(() => useStreamingText({ speed: 30 }))

      // Start first stream
      act(() => {
        result.current.startStream("First")
      })

      // Start second stream before first completes
      act(() => {
        result.current.startStream("Second")
      })

      act(() => {
        vi.advanceTimersByTime(30 * 7) // "Second" (6 chars) + completion tick
      })

      // Should have "Second", not mix with "First"
      expect(result.current.streamedText).toBe("Second")
      expect(result.current.isStreaming).toBe(false)
    })
  })
})

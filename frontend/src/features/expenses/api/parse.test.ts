/**
 * Tests for the SSE parse client (WS7).
 *
 * Exercises the real stream-reading path: fetch is stubbed to return SSE
 * frames the way the backend emits them (word-level commentary chunks, then
 * one complete event; errors either as HTTP status or mid-stream events).
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"

import { parseExpense, ParseError } from "./parse"

function sseResponse(frames: string[], init?: ResponseInit): Response {
  const encoder = new TextEncoder()
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const frame of frames) controller.enqueue(encoder.encode(frame))
      controller.close()
    },
  })
  return new Response(body, {
    status: 200,
    headers: { "Content-Type": "text/event-stream" },
    ...init,
  })
}

const COMPLETE_EVENT =
  'data: {"type":"complete","data":{"amount":"60.00","description":"Lunch",' +
  '"payer_id":"11111111-1111-1111-1111-111111111111",' +
  '"confidence_score":0.95,"commentary":"Got it!"}}\n\n'

describe("parseExpense", () => {
  const fetchMock = vi.fn()

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock)
    localStorage.setItem("access_token", "test-token")
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    localStorage.clear()
    fetchMock.mockReset()
  })

  it("collects commentary chunks and returns the complete payload", async () => {
    fetchMock.mockResolvedValue(
      sseResponse([
        'data: {"type":"commentary","data":{"text":"Got "}}\n\n',
        'data: {"type":"commentary","data":{"text":"it!"}}\n\n',
        COMPLETE_EVENT,
      ])
    )

    const chunks: string[] = []
    const result = await parseExpense({
      text: "Paid 60 for lunch",
      groupId: "group-1",
      onCommentary: (chunk) => chunks.push(chunk),
    })

    expect(chunks).toEqual(["Got ", "it!"])
    expect(result.amount).toBe(60) // decimal string converted for the editor
    expect(result.description).toBe("Lunch")
    expect(result.confidence_score).toBe(0.95)

    // request shape: POST with bearer token and snake_case body
    const [url, init] = fetchMock.mock.calls[0]
    expect(String(url)).toContain("/api/v1/expenses/parse")
    expect(init.method).toBe("POST")
    expect(init.headers.Authorization).toBe("Bearer test-token")
    expect(JSON.parse(init.body)).toEqual({
      text: "Paid 60 for lunch",
      group_id: "group-1",
    })
  })

  it("handles frames split across network chunks", async () => {
    const whole =
      'data: {"type":"commentary","data":{"text":"Hello "}}\n\n' + COMPLETE_EVENT
    // split mid-JSON to prove buffering works
    fetchMock.mockResolvedValue(
      sseResponse([whole.slice(0, 25), whole.slice(25, 60), whole.slice(60)])
    )

    const chunks: string[] = []
    const result = await parseExpense({
      text: "x",
      groupId: "g",
      onCommentary: (chunk) => chunks.push(chunk),
    })
    expect(chunks).toEqual(["Hello "])
    expect(result.description).toBe("Lunch")
  })

  it("throws ParseError with the event message on a mid-stream error", async () => {
    fetchMock.mockResolvedValue(
      sseResponse([
        'data: {"type":"error","error":"I couldn\'t quite understand that expense."}\n\n',
      ])
    )

    await expect(
      parseExpense({ text: "asdf", groupId: "g" })
    ).rejects.toThrow(/couldn't quite understand/)
  })

  it("throws ParseError with the HTTP detail on pre-stream errors", async () => {
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify({
          detail: "You've used all your free AI parses for this month",
        }),
        { status: 429, headers: { "Content-Type": "application/json" } }
      )
    )

    await expect(parseExpense({ text: "x", groupId: "g" })).rejects.toThrow(
      /free AI parses/
    )
  })

  it("throws ParseError when the stream ends without a complete event", async () => {
    fetchMock.mockResolvedValue(
      sseResponse(['data: {"type":"commentary","data":{"text":"Hmm"}}\n\n'])
    )

    await expect(parseExpense({ text: "x", groupId: "g" })).rejects.toThrow(
      ParseError
    )
  })
})

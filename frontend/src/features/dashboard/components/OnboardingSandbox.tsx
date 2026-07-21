import { Link } from "@tanstack/react-router"
import { useCallback, useEffect, useRef, useState } from "react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { formatCurrency, guessLocaleCurrency } from "@/lib/currency"
import { AICommentaryBubble } from "@/features/expenses/components/AICommentaryBubble"
import { parseExpense, ParseError } from "@/features/expenses/api/parse"
import type { ExpenseParseResponse } from "@/features/expenses/types"

type SandboxStatus = "idle" | "loading" | "ready" | "error"

const EXAMPLE = "Paid 40 for pizza, split with Sam and Alex"

/**
 * Onboarding sandbox (WS10.4 / S2 §6) — the organic-path "aha" moment.
 *
 * A first-time user who arrives WITHOUT an invite lands on an empty dashboard.
 * Instead of a bare "create a group" wall, we let them feel the product's
 * signature move first: type an expense in plain words and watch the AI read
 * it into a clean entry. The parse is a real hosted call but PURELY a demo —
 * nothing is persisted and no group is required (backend skips the membership
 * check when no group_id is sent). The "Create your first group" CTA is always
 * present, so the empty state names the next action whether or not they try it.
 */
export function OnboardingSandbox() {
  const [text, setText] = useState("")
  const [status, setStatus] = useState<SandboxStatus>("idle")
  const [commentary, setCommentary] = useState("")
  const [parsed, setParsed] = useState<ExpenseParseResponse | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // Demo amounts have no group currency; show them in the user's locale
  // currency so the number reads naturally. Computed once.
  const currencyRef = useRef<string>(guessLocaleCurrency())

  const abortRef = useRef<AbortController | null>(null)
  const abort = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
  }, [])
  useEffect(() => () => abort(), [abort])

  const handleTry = async () => {
    if (!text.trim() || status === "loading") return

    abort()
    const controller = new AbortController()
    abortRef.current = controller

    setStatus("loading")
    setCommentary("")
    setParsed(null)
    setErrorMessage(null)

    try {
      const result = await parseExpense({
        text,
        // No groupId → sandbox parse.
        onCommentary: (chunk) => setCommentary((prev) => prev + chunk),
        signal: controller.signal,
      })
      if (controller.signal.aborted) return
      setParsed(result)
      setStatus("ready")
    } catch (error) {
      if (controller.signal.aborted) return
      setCommentary("")
      setErrorMessage(
        error instanceof ParseError
          ? error.message
          : "Something went wrong reaching the AI. You can still create a group and add expenses by hand.",
      )
      setStatus("error")
    }
  }

  const handleReset = () => {
    abort()
    setText("")
    setStatus("idle")
    setCommentary("")
    setParsed(null)
    setErrorMessage(null)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault()
      handleTry()
    }
  }

  const isLoading = status === "loading"

  return (
    <div className="space-y-8 py-6">
      <header className="space-y-2 text-center">
        <h1 className="text-title font-semibold text-text-primary">
          Welcome to ClearDues
        </h1>
        <p className="text-body text-text-secondary">
          Type an expense the way you&apos;d say it out loud — I&apos;ll turn it
          into a clean entry. No setup needed to try it.
        </p>
      </header>

      <section
        aria-label="Try an expense"
        className="rounded-lg border border-border bg-surface p-5 space-y-4"
      >
        <AICommentaryBubble text={commentary} isProcessing={isLoading} />

        <div className="space-y-3">
          <label htmlFor="sandbox-input" className="sr-only">
            Describe an expense in plain words
          </label>
          <textarea
            id="sandbox-input"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={EXAMPLE}
            className={cn(
              "w-full min-h-[96px] p-4 rounded-lg resize-none",
              "bg-surface border border-border",
              "text-text-primary placeholder:text-text-muted",
              "focus:outline-none focus:ring-2 focus:ring-action focus:border-action",
            )}
            aria-label="Describe an expense in plain words"
          />

          <Button
            type="button"
            onClick={handleTry}
            disabled={!text.trim() || isLoading}
            className="w-full"
          >
            {isLoading ? "Reading it…" : "Try it"}
          </Button>
        </div>

        {/* Aha: the parsed result, read-only — this is a demo, not a save. */}
        {status === "ready" && parsed && (
          <div
            className="rounded-lg border border-border bg-surface-elevated p-4 space-y-2"
            aria-live="polite"
          >
            <p className="text-caption font-medium uppercase tracking-[0.06em] text-text-muted">
              Here&apos;s what I read
            </p>
            <div className="flex items-baseline justify-between gap-4">
              <span className="text-body font-medium text-text-primary">
                {parsed.description}
              </span>
              <span className="text-title font-semibold tabular-nums text-text-primary">
                {formatCurrency(parsed.amount, currencyRef.current)}
              </span>
            </div>
            <p className="text-body-small text-text-secondary">
              That&apos;s the idea — your words, read into a clean expense.
              Create a group to save real ones.
            </p>
            <button
              type="button"
              onClick={handleReset}
              className="text-sm text-text-secondary underline hover:text-text-primary transition-colors"
            >
              Try another
            </button>
          </div>
        )}

        {/* Mediator-voice failure (quota/low-confidence/AI-down). */}
        {status === "error" && errorMessage && (
          <p
            role="alert"
            className="rounded-lg border border-border bg-surface-elevated p-4 text-body-small text-text-primary"
          >
            {errorMessage}
          </p>
        )}
      </section>

      {/* The next action — always present, so the empty state is never a
          dead end whether or not the sandbox was used. */}
      <div className="space-y-3 text-center">
        <p className="text-body-small text-text-secondary">
          Ready for the real thing? Groups are how you split and settle with
          other people.
        </p>
        <Button asChild variant={status === "ready" ? "default" : "outline"}>
          <Link to="/groups">Create your first group</Link>
        </Button>
      </div>
    </div>
  )
}

export default OnboardingSandbox

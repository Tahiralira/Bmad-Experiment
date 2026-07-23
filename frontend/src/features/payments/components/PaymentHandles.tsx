import { Check, Copy, ExternalLink } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import { EVENTS, track } from "@/lib/analytics"

import { useCounterpartyPaymentMethods } from "../api/payments"
import type { PaymentMethod } from "../types"

interface Props {
  groupId: string
  /** The person being paid (the counterparty you owe). */
  counterpartyUserId: string
  counterpartyName: string
}

/**
 * Counterparty payment handles surfaced at the moment you settle (WS10.2 —
 * "universal mark-as-paid"). For each handle: a "Pay" button that opens the
 * provider deep link where one exists, and always a Copy button (IBANs and
 * plain-text handles have no link). Fetched lazily — only mounted when the
 * settle UI actually asks to pay someone.
 */
export function PaymentHandles({
  groupId,
  counterpartyUserId,
  counterpartyName,
}: Props) {
  const { data, isLoading, error } = useCounterpartyPaymentMethods(
    groupId,
    counterpartyUserId,
    true,
  )

  if (isLoading) {
    return (
      <p className="text-body-small text-text-secondary">
        Loading payment options…
      </p>
    )
  }

  // Non-fatal: settling doesn't depend on handles being loadable.
  if (error) return null

  const methods = data?.data ?? []

  if (methods.length === 0) {
    return (
      <p className="text-body-small text-text-secondary">
        {counterpartyName} hasn't added a payment method yet — ask them how
        they'd like to be paid.
      </p>
    )
  }

  return (
    <div className="space-y-1.5">
      <p className="text-caption font-medium uppercase tracking-[0.06em] text-text-muted">
        Pay {counterpartyName}
      </p>
      <ul className="space-y-1.5">
        {methods.map((method) => (
          <PaymentHandleRow key={method.id} method={method} />
        ))}
      </ul>
    </div>
  )
}

function PaymentHandleRow({ method }: { method: PaymentMethod }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(method.handle)
      // WS10.6: settle-moment payment intent (the copy path — IBANs, custom)
      track(EVENTS.PAYMENT_HANDLE_COPIED, { provider: method.provider })
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Clipboard blocked (insecure context / denied) — the handle is still
      // visible on screen to copy manually.
    }
  }

  return (
    <li className="flex items-center justify-between gap-2 rounded-md border border-border bg-surface-elevated px-3 py-2">
      <div className="min-w-0">
        <p className="text-body-small font-medium text-text-primary">
          {method.provider_name}
        </p>
        <p className="text-caption text-text-secondary truncate">
          {method.label ? `${method.label} · ` : ""}
          {method.handle}
        </p>
      </div>
      <div className="flex shrink-0 items-center gap-1.5">
        {method.pay_url && (
          <Button asChild size="sm" variant="outline">
            <a
              href={method.pay_url}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={`Pay via ${method.provider_name}`}
              onClick={() =>
                // WS10.6: settle-moment payment intent (the deep-link path)
                track(EVENTS.PAYMENT_LINK_CLICKED, { provider: method.provider })
              }
            >
              <ExternalLink className="h-3.5 w-3.5" />
              Pay
            </a>
          </Button>
        )}
        <Button
          size="sm"
          variant="ghost"
          onClick={handleCopy}
          aria-label={`Copy ${method.provider_name} handle`}
        >
          {copied ? (
            <Check className="h-3.5 w-3.5" />
          ) : (
            <Copy className="h-3.5 w-3.5" />
          )}
          {copied ? "Copied" : "Copy"}
        </Button>
      </div>
    </li>
  )
}

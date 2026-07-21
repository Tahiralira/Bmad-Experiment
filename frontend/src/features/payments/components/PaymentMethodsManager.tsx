import { Trash2 } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LoadingButton } from "@/components/ui/loading-button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { getPaymentProvider, PAYMENT_PROVIDERS } from "@/lib/payment-providers"

import {
  useCreatePaymentMethod,
  useDeletePaymentMethod,
  useMyPaymentMethods,
} from "../api/payments"

/**
 * Manage your own payment handles (WS10.2). These are GLOBAL — they appear to
 * anyone in your groups who owes you money, at the moment they settle up.
 * Add + remove; to change a handle, remove it and add the new one.
 */
export function PaymentMethodsManager() {
  const { data, isLoading } = useMyPaymentMethods()
  const create = useCreatePaymentMethod()
  const remove = useDeletePaymentMethod()

  const [provider, setProvider] = useState("venmo")
  const [handle, setHandle] = useState("")
  const [label, setLabel] = useState("")

  const meta = getPaymentProvider(provider)
  const methods = data?.data ?? []

  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = handle.trim()
    if (!trimmed) return
    create.mutate(
      { provider, handle: trimmed, label: label.trim() || null },
      {
        onSuccess: () => {
          setHandle("")
          setLabel("")
        },
      },
    )
  }

  return (
    <div className="max-w-md space-y-6">
      <div>
        <h3 className="text-lg font-semibold">Payment methods</h3>
        <p className="text-body-small text-text-secondary">
          Add the ways people can pay you back. These show up when someone in
          your group settles up with you.
        </p>
      </div>

      {/* Current handles */}
      {isLoading ? (
        <div
          className="h-12 animate-pulse rounded bg-border"
          aria-hidden="true"
        />
      ) : methods.length === 0 ? (
        <p className="text-body-small text-text-secondary">
          No payment methods yet.
        </p>
      ) : (
        <ul className="divide-y divide-border border-y border-border">
          {methods.map((method) => (
            <li
              key={method.id}
              className="flex items-center justify-between gap-3 py-3"
            >
              <div className="min-w-0">
                <p className="text-body font-medium text-text-primary">
                  {method.provider_name}
                </p>
                <p className="text-body-small text-text-secondary truncate">
                  {method.label ? `${method.label} · ` : ""}
                  {method.handle}
                </p>
              </div>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => remove.mutate(method.id)}
                disabled={remove.isPending}
                aria-label={`Remove ${method.provider_name}`}
              >
                <Trash2 className="h-4 w-4" />
                Remove
              </Button>
            </li>
          ))}
        </ul>
      )}

      {/* Add a handle */}
      <form onSubmit={handleAdd} className="space-y-3">
        <div>
          <Label htmlFor="pm-provider">Provider</Label>
          <Select value={provider} onValueChange={setProvider}>
            <SelectTrigger id="pm-provider" className="mt-1 w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {PAYMENT_PROVIDERS.map((p) => (
                <SelectItem key={p.code} value={p.code}>
                  {p.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label htmlFor="pm-handle">Handle</Label>
          <Input
            id="pm-handle"
            value={handle}
            onChange={(e) => setHandle(e.target.value)}
            placeholder={meta?.placeholder ?? ""}
            className="mt-1"
            autoComplete="off"
          />
          {meta?.hint && (
            <p className="mt-1 text-caption text-text-secondary">{meta.hint}</p>
          )}
        </div>

        <div>
          <Label htmlFor="pm-label">Label (optional)</Label>
          <Input
            id="pm-label"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            placeholder="e.g. Personal"
            className="mt-1"
            autoComplete="off"
          />
        </div>

        <LoadingButton
          type="submit"
          loading={create.isPending}
          disabled={!handle.trim()}
        >
          Add payment method
        </LoadingButton>
      </form>
    </div>
  )
}

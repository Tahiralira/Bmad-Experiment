// Payment methods (WS10.2) — wire types. Mirrors the backend PaymentMethod
// schemas (app/features/auth/models.py). `pay_url` is the server-computed deep
// link (null = copy-only); `provider_name` is the display name.

export interface PaymentMethod {
  id: string
  provider: string
  provider_name: string
  handle: string
  label: string | null
  pay_url: string | null
}

export interface PaymentMethodsResponse {
  data: PaymentMethod[]
  count: number
}

export interface PaymentMethodCreate {
  provider: string
  handle: string
  label?: string | null
}

export interface PaymentMethodUpdate {
  handle?: string
  label?: string | null
}

import { createFileRoute } from "@tanstack/react-router"
import { CheckCircle } from "lucide-react"

import { PendingConfirmationsList } from "@/features/expenses/components/PendingConfirmationsList"

export const Route = createFileRoute("/_layout/pending")({
  component: PendingConfirmations,
})

function PendingConfirmations() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-foreground flex items-center gap-3">
          <CheckCircle className="size-8 text-primary" aria-hidden="true" />
          Pending Confirmations
        </h1>
        <p className="text-muted-foreground">
          Review and confirm expenses you&apos;re involved in
        </p>
      </div>

      <PendingConfirmationsList />
    </div>
  )
}

export default PendingConfirmations

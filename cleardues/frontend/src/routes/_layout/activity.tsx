import { createFileRoute } from "@tanstack/react-router"
import { Bell } from "lucide-react"

export const Route = createFileRoute("/_layout/activity")({
  component: Activity,
})

function Activity() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">
          Activity Feed
        </h1>
        <p className="text-muted-foreground">
          Recent activity across your expense groups
        </p>
      </div>

      {/* Placeholder content - to be implemented in Epic 4 (Activity Feed) */}
      <div className="rounded-lg border border-border bg-surface p-8 text-center">
        <div className="mx-auto mb-4 size-12 rounded-full bg-muted flex items-center justify-center">
          <Bell className="size-6 text-muted-foreground" aria-hidden="true" />
        </div>
        <h3 className="text-lg font-semibold text-foreground mb-2">
          Activity Feed Coming Soon
        </h3>
        <p className="text-sm text-muted-foreground max-w-md mx-auto">
          This feature will show expense confirmations, settlements, and group
          activity once implemented in Epic 4: Trust & Confirmation Workflow.
        </p>
      </div>
    </div>
  )
}

export default Activity

import { createFileRoute } from "@tanstack/react-router"

import { Dashboard } from "@/features/dashboard"

export const Route = createFileRoute("/_layout/")({
  component: DashboardPage,
  head: () => ({
    meta: [
      {
        title: "Dashboard - ClearDues",
      },
    ],
  }),
})

function DashboardPage() {
  return <Dashboard />
}

import { createFileRoute, Outlet, redirect } from "@tanstack/react-router"

import { Footer } from "@/components/Common/Footer"
import { OrbitalNav } from "@/components/ui/orbital-nav"
import { isLoggedIn } from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout")({
  component: Layout,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({
        to: "/login",
      })
    }
  },
})

function Layout() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* Main content area - full width without sidebar */}
      <main className="flex-1 p-6 md:p-8">
        <div className="mx-auto max-w-7xl">
          <Outlet />
        </div>
      </main>

      <Footer />

      {/* OrbitalNav - wraps AgentOrb with orbital navigation */}
      {/* Note: Smart Input Modal will be connected in Story 2.5.4 via long-press */}
      <OrbitalNav />
    </div>
  )
}

export default Layout

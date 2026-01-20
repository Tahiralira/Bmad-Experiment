import {
  createFileRoute,
  Outlet,
  redirect,
  useLocation,
} from "@tanstack/react-router"
import { useCallback, useRef, useState } from "react"

import { Footer } from "@/components/Common/Footer"
import { OrbitalNav } from "@/components/ui/orbital-nav"
import { SmartInputModal } from "@/features/expenses/components"
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
  const [isSmartInputOpen, setIsSmartInputOpen] = useState(false)
  const location = useLocation()
  // Ref for Agent Orb to return focus when modal closes
  const orbRef = useRef<HTMLButtonElement>(null as HTMLButtonElement | null)

  const handleOpenSmartInput = useCallback(() => {
    setIsSmartInputOpen(true)
  }, [])

  const handleCloseSmartInput = useCallback(() => {
    setIsSmartInputOpen(false)
    // Focus return is handled by SmartInputModal using triggerRef
  }, [])

  // Determine entry point from route
  const entryPoint =
    location.pathname === "/" || location.pathname === "/dashboard"
      ? "dashboard"
      : "group"

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
      <OrbitalNav onLongPress={handleOpenSmartInput} orbRef={orbRef} />

      {/* Smart Input Modal - triggered by long-press on Agent Orb */}
      <SmartInputModal
        open={isSmartInputOpen}
        onOpenChange={(open) => !open && handleCloseSmartInput()}
        entryPoint={entryPoint}
        triggerRef={orbRef}
      />
    </div>
  )
}

export default Layout

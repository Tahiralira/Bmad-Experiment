import {
  createFileRoute,
  Outlet,
  redirect,
  useLocation,
} from "@tanstack/react-router"
import { useCallback, useRef, useState } from "react"

import { AgentOrb } from "@/components/ui/agent-orb"
import { BottomNav } from "@/components/ui/bottom-nav"
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
      {/* Main content area - bottom padding clears the fixed nav + orb */}
      <main className="flex-1 p-6 pb-28 md:p-8 md:pb-28">
        <div className="mx-auto max-w-7xl">
          <Outlet />
        </div>
      </main>

      {/* Agent Orb - floating action button, tap to add an expense */}
      <AgentOrb
        ref={orbRef}
        onClick={handleOpenSmartInput}
        className="fixed bottom-20 right-4 z-50"
      />

      {/* Persistent bottom tab bar navigation */}
      <BottomNav />

      {/* Smart Input Modal - triggered by tapping the Agent Orb */}
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

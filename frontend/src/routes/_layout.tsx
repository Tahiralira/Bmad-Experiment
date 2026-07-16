import {
  createFileRoute,
  Outlet,
  redirect,
  useLocation,
} from "@tanstack/react-router"
import { useCallback, useRef, useState } from "react"

import { BottomNav } from "@/components/ui/bottom-nav"
import { Fab } from "@/components/ui/fab"
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
  // Ref for the FAB to return focus when the modal closes
  const fabRef = useRef<HTMLButtonElement>(null as HTMLButtonElement | null)

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
      {/* Main content area - bottom padding clears the fixed nav + FAB */}
      <main className="flex-1 p-6 pb-28 md:p-8 md:pb-28">
        <div className="mx-auto max-w-2xl">
          <Outlet />
        </div>
      </main>

      {/* Floating action button — tap to add an expense */}
      <Fab
        ref={fabRef}
        onClick={handleOpenSmartInput}
        className="fixed bottom-20 right-4 z-50"
      />

      {/* Persistent bottom tab bar navigation */}
      <BottomNav />

      {/* Smart Input Modal - triggered by the FAB */}
      <SmartInputModal
        open={isSmartInputOpen}
        onOpenChange={(open) => !open && handleCloseSmartInput()}
        entryPoint={entryPoint}
        triggerRef={fabRef}
      />
    </div>
  )
}

export default Layout

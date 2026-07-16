import { Link } from "@tanstack/react-router"
import { Bell, CheckCircle, Home, User, Users, type LucideIcon } from "lucide-react"

import { cn } from "@/lib/utils"

interface BottomNavItem {
  icon: LucideIcon
  label: string
  path: "/" | "/groups" | "/pending" | "/activity" | "/settings"
  ariaLabel: string
  /** Exact-match for active state (needed for "/" so it doesn't match every route) */
  exact?: boolean
}

const navigationItems: BottomNavItem[] = [
  { icon: Home, label: "Home", path: "/", ariaLabel: "Dashboard", exact: true },
  { icon: Users, label: "Groups", path: "/groups", ariaLabel: "Expense groups" },
  { icon: CheckCircle, label: "Pending", path: "/pending", ariaLabel: "Pending confirmations" },
  { icon: Bell, label: "Activity", path: "/activity", ariaLabel: "Activity feed" },
  { icon: User, label: "Profile", path: "/settings", ariaLabel: "User settings" },
]

export interface BottomNavProps {
  className?: string
}

/**
 * BottomNav — persistent, labeled bottom tab bar.
 *
 * Replaces OrbitalNav as the app's navigation: all destinations are always
 * visible, labeled, and meet the 44px minimum touch target. The Agent Orb
 * remains a separate floating action button dedicated to expense entry.
 */
function BottomNav({ className }: BottomNavProps) {
  return (
    <nav
      aria-label="Main navigation"
      className={cn(
        "fixed inset-x-0 bottom-0 z-40",
        "border-t border-border bg-background",
        "pb-[env(safe-area-inset-bottom)]",
        className,
      )}
    >
      <ul className="mx-auto flex max-w-md items-stretch justify-around">
        {navigationItems.map((item) => {
          const Icon = item.icon
          return (
            <li key={item.path} className="flex-1">
              <Link
                to={item.path}
                aria-label={item.ariaLabel}
                activeOptions={item.exact ? { exact: true } : undefined}
                className={cn(
                  "flex min-h-14 flex-col items-center justify-center gap-1",
                  "text-text-muted transition-colors",
                  "hover:text-text-primary",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset",
                  "data-[status=active]:text-primary",
                )}
              >
                <Icon className="size-5" aria-hidden="true" />
                <span className="text-caption font-medium uppercase tracking-[0.06em] leading-none">
                  {item.label}
                </span>
              </Link>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}

export { BottomNav, navigationItems }

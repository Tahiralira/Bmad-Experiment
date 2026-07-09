import * as React from "react"
import { Plus } from "lucide-react"

import { cn } from "@/lib/utils"

export interface FabProps extends React.ComponentProps<"button"> {
  /** Custom aria-label (default: "Add an expense") */
  ariaLabel?: string
}

/**
 * Fab — the app's single floating action button. Tap = Smart Input.
 *
 * Replaces AgentOrb (WS2 decision: the "agent" lives in the mediator voice and
 * AI commentary, not in a glowing object). No idle animation by design.
 */
const Fab = React.forwardRef<HTMLButtonElement, FabProps>(
  ({ className, ariaLabel = "Add an expense", ...props }, ref) => (
    <button
      ref={ref}
      type="button"
      aria-label={ariaLabel}
      className={cn(
        "inline-flex size-14 items-center justify-center rounded-full",
        "bg-primary text-primary-foreground shadow-lg",
        "transition-[transform,background-color] duration-150 hover:bg-action-hover active:scale-95",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
        className,
      )}
      {...props}
    >
      <Plus className="size-6" aria-hidden="true" />
    </button>
  ),
)
Fab.displayName = "Fab"

export { Fab }

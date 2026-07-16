import { Link } from "@tanstack/react-router"

import { cn } from "@/lib/utils"

interface LogoProps {
  variant?: "full" | "icon" | "responsive"
  className?: string
  asLink?: boolean
}

/** The ClearDues mark: a balanced ledger ("="). Renders in the accent color. */
function LogoGlyph({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 64 64"
      aria-hidden="true"
      className={cn("size-6 shrink-0", className)}
    >
      <rect width="64" height="64" rx="14" className="fill-primary" />
      <rect x="16" y="25" width="32" height="6" rx="3" className="fill-background" />
      <rect x="16" y="37" width="32" height="6" rx="3" className="fill-background" />
    </svg>
  )
}

export function Logo({ variant = "full", className, asLink = true }: LogoProps) {
  const content =
    variant === "icon" ? (
      <LogoGlyph className={className} />
    ) : (
      <span className={cn("inline-flex items-center gap-2", className)}>
        <LogoGlyph />
        <span className="text-heading font-semibold tracking-tight text-text-primary">
          ClearDues
        </span>
      </span>
    )

  if (!asLink) {
    return content
  }

  return (
    <Link to="/" aria-label="ClearDues home">
      {content}
    </Link>
  )
}

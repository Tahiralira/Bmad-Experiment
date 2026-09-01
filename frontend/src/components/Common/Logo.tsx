import { Link } from "@tanstack/react-router"

import { cn } from "@/lib/utils"

interface LogoProps {
  className?: string
  asLink?: boolean
}

/**
 * The ClearDues brand lockup — handshake mark + wordmark (`just-logo.PNG`,
 * transparent). The art is dark monochrome ink, so `dark:invert` lifts it to
 * light ink on the dark theme's near-black ground. The file is `.PNG`
 * (uppercase) and Vercel's build is case-sensitive — keep the reference exact.
 */
export function Logo({ className, asLink = true }: LogoProps) {
  const content = (
    <img
      src="/just-logo.PNG"
      alt="ClearDues"
      className={cn("h-12 w-auto select-none dark:invert", className)}
    />
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

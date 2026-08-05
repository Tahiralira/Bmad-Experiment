import { Link } from "@tanstack/react-router"
import { useEffect } from "react"
import { Button } from "@/components/ui/button"
import { captureError } from "@/lib/sentry"

interface ErrorComponentProps {
  /** The error that tripped the route boundary — reported to Sentry (WS10.6). */
  error?: unknown
}

const ErrorComponent = ({ error }: ErrorComponentProps) => {
  useEffect(() => {
    if (error !== undefined) captureError(error)
  }, [error])

  return (
    <div
      className="flex min-h-screen items-center justify-center flex-col p-4"
      data-testid="error-component"
    >
      <div className="flex items-center z-10">
        <div className="flex flex-col ml-4 items-center justify-center p-4">
          <span className="text-6xl md:text-8xl font-semibold leading-none mb-4">
            Error
          </span>
          <span className="text-title font-semibold mb-2">Oops!</span>
        </div>
      </div>

      <p className="text-lg text-muted-foreground mb-4 text-center z-10">
        Something went wrong. Please try again.
      </p>
      <Link to="/">
        <Button>Go Home</Button>
      </Link>
    </div>
  )
}

export default ErrorComponent

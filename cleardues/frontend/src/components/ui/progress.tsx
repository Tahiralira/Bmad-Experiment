import * as React from "react"

import { cn } from "@/lib/utils"

/**
 * Props for the Progress component
 */
export interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * Progress value (0-100)
   */
  value?: number

  /**
   * Optional className for additional styling
   */
  className?: string
}

/**
 * Progress component
 *
 * Displays a horizontal progress bar with percentage completion.
 * Follows shadcn/ui patterns.
 *
 * @example
 * ```tsx
 * <Progress value={75} />
 * <Progress value={100} className="bg-success" />
 * ```
 */
const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({ className, value = 0, ...props }, ref) => {
    // Clamp value between 0 and 100
    const clampedValue = Math.max(0, Math.min(100, value || 0))

    return (
      <div
        ref={ref}
        className={cn(
          "relative h-2 w-full overflow-hidden rounded-full bg-muted",
          className
        )}
        {...props}
      >
        <div
          className="h-full bg-primary transition-all duration-300 ease-in-out"
          style={{ width: `${clampedValue}%` }}
        />
      </div>
    )
  }
)
Progress.displayName = "Progress"

export { Progress }
export default Progress

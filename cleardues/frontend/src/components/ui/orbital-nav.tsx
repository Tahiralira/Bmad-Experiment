import * as React from "react"
import { AnimatePresence, motion, useReducedMotion } from "framer-motion"
import { Bell, Home, User, Users, type LucideIcon } from "lucide-react"
import { useNavigate } from "@tanstack/react-router"

import { cn } from "@/lib/utils"
import { AgentOrb } from "./agent-orb"

// ============================================================================
// Types and Interfaces
// ============================================================================

export interface NavItem {
  icon: LucideIcon
  label: string
  path: string
  ariaLabel: string
}

export interface OrbitalNavProps {
  /** Custom navigation items (defaults to standard nav) */
  items?: NavItem[]
  /** Additional className for container */
  className?: string
  /** Whether orb is in processing state */
  isProcessing?: boolean
  /** Whether to show success state */
  showSuccess?: boolean
}

// ============================================================================
// Default Navigation Items
// ============================================================================

const defaultNavigationItems: NavItem[] = [
  { icon: Home, label: "Home", path: "/", ariaLabel: "Dashboard" },
  { icon: Users, label: "Groups", path: "/groups", ariaLabel: "Expense groups" },
  { icon: Bell, label: "Activity", path: "/activity", ariaLabel: "Activity feed" },
  { icon: User, label: "Profile", path: "/settings", ariaLabel: "User settings" },
]

// ============================================================================
// Animation Constants
// ============================================================================

const ANIMATION_CONSTANTS = {
  // Note: Spring animations use physics (stiffness/damping) rather than fixed duration.
  // The spring config (stiffness: 400, damping: 17) produces ~300ms characteristic time.
  // This creates natural, organic motion per design spec while approximating AC #8 timing.
  expandDuration: 0.3, // 300ms - used as reference; actual expand uses spring physics
  collapseDuration: 0.2, // 200ms - used for exit animation
  staggerDelay: 0.05, // 50ms between each icon (AC #2)
  autoHideDuration: 3000, // 3 seconds (AC #5)
  hoverDelay: 300, // 300ms before expanding on hover
  orbitalRadius: 72, // Distance from center in pixels
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Calculate orbital position in a radial arc around the center
 * Arc spans from -135deg (bottom-left) to +45deg (top-right)
 */
function calculateOrbitalPosition(index: number, total: number, radius: number) {
  const startAngle = -135
  const endAngle = 45
  const angleRange = endAngle - startAngle
  const angleStep = angleRange / (total - 1)
  const angle = startAngle + index * angleStep

  const radians = (angle * Math.PI) / 180
  return {
    x: Math.cos(radians) * radius,
    y: Math.sin(radians) * radius,
  }
}

// ============================================================================
// OrbitalIcon Component
// ============================================================================

interface OrbitalIconProps {
  item: NavItem
  index: number
  total: number
  isExpanded: boolean
  shouldReduceMotion: boolean | null
  onSelect: (path: string) => void
  onFocus: () => void
  /** Ref callback for focus management */
  refCallback: (el: HTMLButtonElement | null) => void
}

function OrbitalIcon({
  item,
  index,
  total,
  isExpanded,
  shouldReduceMotion,
  onSelect,
  onFocus,
  refCallback,
}: OrbitalIconProps) {
  const position = calculateOrbitalPosition(index, total, ANIMATION_CONSTANTS.orbitalRadius)
  const Icon = item.icon

  const handleClick = () => {
    onSelect(item.path)
  }

  const handleKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      onSelect(item.path)
    }
  }

  return (
    <motion.button
      ref={refCallback}
      role="menuitem"
      aria-label={item.ariaLabel}
      tabIndex={isExpanded ? 0 : -1}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      onFocus={onFocus}
      className={cn(
        // Base
        "flex items-center justify-center rounded-[28%]",
        "size-12", // 48px orbital icons
        // Colors using design tokens
        "bg-surface text-action",
        "border border-border",
        // Hover
        "hover:bg-surface-elevated hover:border-action",
        "hover:scale-110 transition-transform duration-150",
        // Focus ring - using focus-visible for keyboard navigation
        // Note: isFocused state triggers programmatic .focus() which activates :focus-visible
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        // Shadow
        "shadow-md hover:shadow-lg"
      )}
      // Animation variants
      initial={
        shouldReduceMotion
          ? { opacity: 0 }
          : {
              scale: 0,
              opacity: 0,
              x: 0,
              y: 0,
            }
      }
      animate={
        shouldReduceMotion
          ? { opacity: 1 }
          : {
              scale: 1,
              opacity: 1,
              x: position.x,
              y: position.y,
              transition: {
                type: "spring",
                stiffness: 400,
                damping: 17,
                delay: index * ANIMATION_CONSTANTS.staggerDelay,
              },
            }
      }
      exit={
        shouldReduceMotion
          ? { opacity: 0 }
          : {
              scale: 0,
              opacity: 0,
              x: 0,
              y: 0,
              transition: {
                duration: ANIMATION_CONSTANTS.collapseDuration,
              },
            }
      }
      whileHover={shouldReduceMotion ? undefined : { scale: 1.15 }}
      whileTap={shouldReduceMotion ? undefined : { scale: 0.95 }}
    >
      <Icon className="size-5" aria-hidden="true" />
      <span className="sr-only">{item.label}</span>
    </motion.button>
  )
}

// ============================================================================
// Main OrbitalNav Component
// ============================================================================

function OrbitalNav({
  items = defaultNavigationItems,
  className,
  isProcessing = false,
  showSuccess = false,
}: OrbitalNavProps) {
  const navigate = useNavigate()
  const shouldReduceMotion = useReducedMotion()

  // State
  const [isExpanded, setIsExpanded] = React.useState(false)
  const [focusedIndex, setFocusedIndex] = React.useState(-1)

  // Memoize media query check for hover-capable devices (LOW: performance optimization)
  const supportsHover = React.useMemo(
    () => typeof window !== "undefined" && window.matchMedia("(hover: hover)").matches,
    []
  )

  // Refs
  const containerRef = React.useRef<HTMLDivElement>(null)
  const hoverTimeoutRef = React.useRef<ReturnType<typeof setTimeout> | null>(null)
  const autoHideTimeoutRef = React.useRef<ReturnType<typeof setTimeout> | null>(null)
  const orbitalRefs = React.useRef<(HTMLButtonElement | null)[]>([])

  // Ref callback for focus management (CRITICAL: enables keyboard navigation)
  const setOrbitalRef = React.useCallback(
    (index: number) => (el: HTMLButtonElement | null) => {
      orbitalRefs.current[index] = el
    },
    []
  )

  // ========================================================================
  // Auto-hide timeout (AC: #5)
  // ========================================================================

  const resetAutoHideTimer = React.useCallback(() => {
    if (autoHideTimeoutRef.current) {
      clearTimeout(autoHideTimeoutRef.current)
    }
    if (isExpanded) {
      autoHideTimeoutRef.current = setTimeout(() => {
        setIsExpanded(false)
        setFocusedIndex(-1)
      }, ANIMATION_CONSTANTS.autoHideDuration)
    }
  }, [isExpanded])

  React.useEffect(() => {
    resetAutoHideTimer()
    return () => {
      if (autoHideTimeoutRef.current) {
        clearTimeout(autoHideTimeoutRef.current)
      }
    }
  }, [isExpanded, resetAutoHideTimer])

  // ========================================================================
  // Navigation handler
  // ========================================================================

  const handleNavigation = React.useCallback(
    (path: string) => {
      navigate({ to: path })
      setIsExpanded(false)
      setFocusedIndex(-1)
    },
    [navigate]
  )

  // ========================================================================
  // Mobile tap interaction (AC: #1, #3, #4)
  // ========================================================================

  const handleOrbClick = React.useCallback(() => {
    // If orbitals are expanded, clicking orb again closes them
    if (isExpanded) {
      setIsExpanded(false)
      setFocusedIndex(-1)
    } else {
      // Open orbitals
      setIsExpanded(true)
      setFocusedIndex(0) // Focus first item
    }

    // Also call external handler if provided (for Smart Input)
    // Note: Smart Input will use long-press in Story 2.5.4
    // For now, tap toggles nav
  }, [isExpanded])

  // ========================================================================
  // Desktop hover interaction (AC: #1)
  // ========================================================================

  const handleMouseEnter = React.useCallback(() => {
    // Only expand on hover for desktop (hover-capable devices)
    if (supportsHover) {
      hoverTimeoutRef.current = setTimeout(() => {
        setIsExpanded(true)
      }, ANIMATION_CONSTANTS.hoverDelay)
    }
  }, [supportsHover])

  const handleMouseLeave = React.useCallback(() => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current)
    }
    // Only auto-collapse on mouse leave for desktop
    if (supportsHover) {
      setIsExpanded(false)
      setFocusedIndex(-1)
    }
  }, [supportsHover])

  // ========================================================================
  // Click outside to dismiss (AC: #4)
  // ========================================================================

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node) &&
        isExpanded
      ) {
        setIsExpanded(false)
        setFocusedIndex(-1)
      }
    }

    document.addEventListener("mousedown", handleClickOutside)
    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [isExpanded])

  // ========================================================================
  // Keyboard navigation (AC: #6)
  // ========================================================================

  const handleKeyDown = React.useCallback(
    (event: React.KeyboardEvent<HTMLDivElement>) => {
      if (!isExpanded) {
        // If not expanded and Enter/Space pressed on orb, expand
        if (event.key === "Enter" || event.key === " ") {
          // Orb handles this internally
          return
        }
        return
      }

      resetAutoHideTimer()

      switch (event.key) {
        case "Escape":
          event.preventDefault()
          setIsExpanded(false)
          setFocusedIndex(-1)
          break
        case "ArrowRight":
        case "ArrowDown":
          event.preventDefault()
          setFocusedIndex((prev) => (prev + 1) % items.length)
          break
        case "ArrowLeft":
        case "ArrowUp":
          event.preventDefault()
          setFocusedIndex((prev) => (prev - 1 + items.length) % items.length)
          break
        case "Tab":
          // Allow tab to cycle through orbitals
          if (event.shiftKey) {
            if (focusedIndex <= 0) {
              // Tab out of orbitals
              setIsExpanded(false)
              setFocusedIndex(-1)
            } else {
              event.preventDefault()
              setFocusedIndex((prev) => prev - 1)
            }
          } else {
            if (focusedIndex >= items.length - 1) {
              // Tab out of orbitals
              setIsExpanded(false)
              setFocusedIndex(-1)
            } else {
              event.preventDefault()
              setFocusedIndex((prev) => prev + 1)
            }
          }
          break
        case "Enter":
        case " ":
          event.preventDefault()
          if (focusedIndex >= 0 && focusedIndex < items.length) {
            handleNavigation(items[focusedIndex].path)
          }
          break
        case "Home":
          event.preventDefault()
          setFocusedIndex(0)
          break
        case "End":
          event.preventDefault()
          setFocusedIndex(items.length - 1)
          break
      }
    },
    [isExpanded, items, focusedIndex, handleNavigation, resetAutoHideTimer]
  )

  // Focus management
  React.useEffect(() => {
    if (isExpanded && focusedIndex >= 0 && orbitalRefs.current[focusedIndex]) {
      orbitalRefs.current[focusedIndex]?.focus()
    }
  }, [focusedIndex, isExpanded])

  // ========================================================================
  // Interaction handlers
  // ========================================================================

  const handleInteraction = React.useCallback(() => {
    resetAutoHideTimer()
  }, [resetAutoHideTimer])

  // ========================================================================
  // Render
  // ========================================================================

  return (
    <div
      ref={containerRef}
      className={cn("fixed bottom-6 right-6 z-50", className)}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onKeyDown={handleKeyDown}
      onMouseMove={handleInteraction}
      onTouchStart={handleInteraction}
      role="navigation"
      aria-label="Main navigation"
    >
      {/* Orbital icons container */}
      <div
        className="absolute inset-0 flex items-center justify-center"
        role="menu"
        aria-label="Navigation menu"
      >
        <AnimatePresence>
          {isExpanded &&
            items.map((item, index) => (
              <OrbitalIcon
                key={item.path}
                item={item}
                index={index}
                total={items.length}
                isExpanded={isExpanded}
                shouldReduceMotion={shouldReduceMotion}
                onSelect={handleNavigation}
                onFocus={() => setFocusedIndex(index)}
                refCallback={setOrbitalRef(index)}
              />
            ))}
        </AnimatePresence>
      </div>

      {/* Agent Orb at center */}
      <AgentOrb
        onClick={handleOrbClick}
        isProcessing={isProcessing}
        showSuccess={showSuccess}
        ariaLabel={isExpanded ? "Close navigation menu" : "Open navigation menu"}
        aria-expanded={isExpanded}
        aria-haspopup="menu"
      />
    </div>
  )
}

export { OrbitalNav, defaultNavigationItems }

import { motion } from "framer-motion"
import * as Icons from "lucide-react"
import { cn } from "@/lib/utils"
import { SplitType, SPLIT_TYPE_OPTIONS } from "../types"
import type { LucideIcon } from "lucide-react"

interface SplitPickerProps {
  /** Currently selected split type */
  selectedType: SplitType
  /** Callback when user selects a different split type */
  onSelectType: (type: SplitType) => void
}

/**
 * Split Type Picker Component
 *
 * Visual card selector for choosing how to split expenses:
 * - Equal (enabled in Story 3.5)
 * - Unequal (disabled - Story 3.6)
 * - Percentage (disabled - Story 3.7)
 * - Shares (disabled - Story 3.8)
 *
 * @example
 * ```tsx
 * <SplitPicker
 *   selectedType={splitType}
 *   onSelectType={setSplitType}
 * />
 * ```
 */
export function SplitPicker({ selectedType, onSelectType }: SplitPickerProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="block text-xs font-medium text-text-secondary">
        Split Type
      </label>

      <div className="grid grid-cols-4 gap-3">
        {SPLIT_TYPE_OPTIONS.map((option) => {
          const Icon = Icons[option.icon as keyof typeof Icons] as LucideIcon
          const isSelected = selectedType === option.type

          return (
            <motion.button
              key={option.type}
              type="button"
              onClick={() => !option.disabled && onSelectType(option.type)}
              disabled={option.disabled}
              className={cn(
                "relative flex flex-col items-center justify-center",
                "p-4 rounded-lg border-2 transition-all",
                "min-h-[100px]",
                isSelected && "border-action bg-action/10",
                !isSelected && "border-border bg-surface",
                option.disabled
                  ? "opacity-50 cursor-not-allowed"
                  : "hover:border-action/50 hover:bg-action/5",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-action"
              )}
              whileHover={!option.disabled ? { scale: 1.02 } : undefined}
              whileTap={!option.disabled ? { scale: 0.98 } : undefined}
              transition={{ duration: 0.2 }}
            >
              {Icon && <Icon className="w-6 h-6 mb-2 text-text-primary" />}
              <span className="text-xs font-medium text-text-primary">
                {option.label}
              </span>

              {option.disabled && (
                <div className="absolute inset-0 flex items-center justify-center bg-surface/80 rounded-lg">
                  <span className="text-[10px] text-text-secondary text-center px-1">
                    {option.disabledReason}
                  </span>
                </div>
              )}
            </motion.button>
          )
        })}
      </div>
    </div>
  )
}

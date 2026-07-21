// Onboarding group templates (WS10.4 / S2 §6).
//
// The organic-path friction is the blank "create a group" form. These
// templates answer the two questions a first-timer shouldn't have to think
// about — what to call it, and how strict confirmation should be — with a
// one-tap preset that also SETS EXPECTATIONS via a plain-language blurb.
//
// "Social contract" today = strict_mode. The low-friction templates all start
// it OFF (expenses auto-confirm quietly unless someone objects — WS6). The
// per-template `strictMode` field is kept explicit so a future template can
// diverge, and so nudge-cadence / settlement-cycle presets can attach here
// once those features land (WS12) without reshaping the call sites.

export type GroupTemplateId = "roommates" | "trip" | "dinner"

export interface GroupTemplate {
  id: GroupTemplateId
  /** Chip label. */
  label: string
  /** Decorative emoji for the chip (aria-hidden). */
  emoji: string
  /** Prefills the (still-editable) group name. */
  suggestedName: string
  /** The social contract this template presets — today, strict_mode. */
  strictMode: boolean
  /** One-line description of the contract, shown once the chip is selected. */
  blurb: string
}

export const GROUP_TEMPLATES: readonly GroupTemplate[] = [
  {
    id: "roommates",
    label: "Roommates",
    emoji: "🏠",
    suggestedName: "Roommates",
    strictMode: false,
    blurb: "Ongoing shared costs — expenses confirm quietly, no ceremony.",
  },
  {
    id: "trip",
    label: "Trip",
    emoji: "✈️",
    suggestedName: "Trip",
    strictMode: false,
    blurb: "Lots of expenses now, settle up at the end. Low friction.",
  },
  {
    id: "dinner",
    label: "Dinner",
    emoji: "🍽️",
    suggestedName: "Dinner",
    strictMode: false,
    blurb: "A one-off to split and settle — quick and quiet.",
  },
]

/** The set of names a template can auto-fill, so the form can tell whether the
 * user has typed their own name or is still on a template default. */
export const TEMPLATE_SUGGESTED_NAMES: ReadonlySet<string> = new Set(
  GROUP_TEMPLATES.map((t) => t.suggestedName),
)

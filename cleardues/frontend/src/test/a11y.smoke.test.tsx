import { describe, expect, it } from "vitest"
import { render } from "@testing-library/react"
import { axe } from "vitest-axe"

import { BalanceDisplay } from "@/components/ui/balance-display"
import { Button } from "@/components/ui/button"
import { Fab } from "@/components/ui/fab"

// Axe smoke: catches missing labels/roles/contrast-adjacent markup regressions in
// the design-system primitives. Full-page axe runs land with the Playwright
// journeys in WS11.
//
// vitest-axe's toHaveNoViolations matcher targets an older vitest major and does
// not register under vitest 4, so we assert on the violations array directly —
// same guarantee, no matcher (fallback sanctioned by the WS3 kit).
describe("a11y smoke (design system primitives)", () => {
  it("BalanceDisplay has no violations", async () => {
    const { container } = render(
      <BalanceDisplay amount={-450} variant="title" contextLabel="You owe" />,
    )
    expect((await axe(container)).violations).toEqual([])
  })

  it("Button has no violations", async () => {
    const { container } = render(<Button>Settle up</Button>)
    expect((await axe(container)).violations).toEqual([])
  })

  it("Fab has no violations", async () => {
    const { container } = render(<Fab />)
    expect((await axe(container)).violations).toEqual([])
  })
})

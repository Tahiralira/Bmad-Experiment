import { createFileRoute } from "@tanstack/react-router"
import { LogOut } from "lucide-react"

import DeleteAccount from "@/components/UserSettings/DeleteAccount"
import UserInformation from "@/components/UserSettings/UserInformation"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { NotificationSettings } from "@/features/notifications"
import { PaymentMethodsManager } from "@/features/payments"
import useAuth from "@/hooks/useAuth"

// ClearDues is passwordless — the template's Password tab died in WS8
const tabsConfig = [
  { value: "my-profile", title: "My profile", component: UserInformation },
  {
    value: "payment-methods",
    title: "Payment methods",
    component: PaymentMethodsManager,
  },
  {
    value: "notifications",
    title: "Notifications",
    component: NotificationSettings,
  },
  { value: "danger-zone", title: "Danger zone", component: DeleteAccount },
]

export const Route = createFileRoute("/_layout/settings")({
  component: UserSettings,
  head: () => ({
    meta: [
      {
        title: "Settings - ClearDues",
      },
    ],
  }),
})

function UserSettings() {
  const { user: currentUser, logout } = useAuth()
  const finalTabs = tabsConfig

  if (!currentUser) {
    return null
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-title font-semibold tracking-tight">User Settings</h1>
          <p className="text-muted-foreground">
            Manage your account settings and preferences
          </p>
        </div>
        <Button variant="outline" onClick={logout} className="gap-2">
          <LogOut aria-hidden="true" />
          Log out
        </Button>
      </div>

      <Tabs defaultValue="my-profile">
        {/* The base TabsList is a fixed-height inline-flex, so a fourth tab
            (Notifications, WS12) pushed the strip to 420px and made the whole
            page scroll sideways at 375px — measured, not guessed. Wrapping
            keeps every tab reachable without a hidden scroll affordance;
            `h-auto` is needed because the base sets a fixed h-9. */}
        <TabsList className="h-auto flex-wrap justify-start">
          {finalTabs.map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value}>
              {tab.title}
            </TabsTrigger>
          ))}
        </TabsList>
        {finalTabs.map((tab) => (
          <TabsContent key={tab.value} value={tab.value}>
            <tab.component />
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}

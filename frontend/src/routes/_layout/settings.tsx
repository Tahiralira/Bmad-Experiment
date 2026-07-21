import { createFileRoute } from "@tanstack/react-router"

import DeleteAccount from "@/components/UserSettings/DeleteAccount"
import UserInformation from "@/components/UserSettings/UserInformation"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
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
  const { user: currentUser } = useAuth()
  const finalTabs = tabsConfig

  if (!currentUser) {
    return null
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-title font-semibold tracking-tight">User Settings</h1>
        <p className="text-muted-foreground">
          Manage your account settings and preferences
        </p>
      </div>

      <Tabs defaultValue="my-profile">
        <TabsList>
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

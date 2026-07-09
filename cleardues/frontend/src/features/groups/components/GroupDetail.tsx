import { Banknote } from "lucide-react"

import type { ExpenseGroup } from "../types"
import { GenerateInviteButton } from "./GenerateInviteButton"
import { MembersList } from "./MembersList"
import { ActivityFeed } from "@/features/expenses/components/ActivityFeed"
import { SettlementClaimsList } from "@/features/expenses/components/SettlementClaimsList"

interface Props {
  group: ExpenseGroup
}

export function GroupDetail({ group }: Props) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">{group.name}</h2>
          <p className="text-sm text-muted-foreground">
            Created {new Date(group.created_at).toLocaleDateString()}
          </p>
        </div>
        <GenerateInviteButton groupId={group.id} />
      </div>

      <div className="border-t pt-4">
        <MembersList groupId={group.id} />
      </div>

      <div className="border-t pt-4">
        <h3 className="mb-3 flex items-center gap-2 text-lg font-semibold">
          <Banknote className="h-5 w-5 text-amber-500" />
          Settlement Claims
        </h3>
        <SettlementClaimsList />
      </div>

      <div className="border-t pt-4">
        <ActivityFeed groupId={group.id} title="Recent Activity" />
      </div>
    </div>
  )
}

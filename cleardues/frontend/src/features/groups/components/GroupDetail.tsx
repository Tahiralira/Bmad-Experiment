import type { ExpenseGroup } from "../types"
import { GenerateInviteButton } from "./GenerateInviteButton"
import { MembersList } from "./MembersList"
import { ActivityFeed } from "@/features/expenses/components/ActivityFeed"

interface Props {
  group: ExpenseGroup
}

export function GroupDetail({ group }: Props) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold">{group.name}</h2>
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
        <ActivityFeed groupId={group.id} title="Recent Activity" />
      </div>
    </div>
  )
}

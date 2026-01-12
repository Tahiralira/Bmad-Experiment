import { useGroupMembers } from "../api/groups"
import type { GroupMemberPublic } from "../types"

interface Props {
  groupId: string
}

export function MembersList({ groupId }: Props) {
  const { data, isLoading, error } = useGroupMembers(groupId)

  if (isLoading) {
    return <div className="animate-pulse">Loading members...</div>
  }

  if (error) {
    return <div className="text-red-600">Failed to load members</div>
  }

  if (!data?.members.length) {
    return <div className="text-gray-500">No members found</div>
  }

  return (
    <div className="space-y-2">
      <h3 className="text-lg font-semibold">Members ({data.count})</h3>
      <ul className="divide-y divide-gray-200">
        {data.members.map((member) => (
          <MemberItem key={member.id} member={member} />
        ))}
      </ul>
    </div>
  )
}

function MemberItem({ member }: { member: GroupMemberPublic }) {
  const isOwner = member.role === "owner"

  return (
    <li className="flex items-center gap-3 py-3">
      {/* Avatar placeholder */}
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gray-200 text-gray-600">
        {member.full_name?.charAt(0)?.toUpperCase() || "?"}
      </div>

      {/* Member info */}
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="font-medium">
            {member.full_name || "Unknown User"}
          </span>
          {isOwner && (
            <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">
              Owner
            </span>
          )}
        </div>
        <span className="text-sm text-gray-500">{member.email}</span>
      </div>
    </li>
  )
}

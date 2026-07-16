import { createFileRoute } from "@tanstack/react-router"

import { GroupLedgerScreen } from "@/features/groups/components/GroupLedgerScreen"

// The trailing underscore in the filename (groups_.$groupId) opts out of
// nesting under /groups — the list route has no <Outlet/>, so this renders
// as its own full page at /groups/$groupId (WS5/S4-H3: groups get a URL).
export const Route = createFileRoute("/_layout/groups_/$groupId")({
  component: GroupDetailPage,
  head: () => ({
    meta: [
      {
        title: "Group - ClearDues",
      },
    ],
  }),
})

function GroupDetailPage() {
  const { groupId } = Route.useParams()
  return <GroupLedgerScreen groupId={groupId} />
}

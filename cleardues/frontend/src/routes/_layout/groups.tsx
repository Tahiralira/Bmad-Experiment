import { createFileRoute, Link } from "@tanstack/react-router"
import { ChevronRight, Plus, Users } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { useUserGroups } from "@/features/groups/api/groups"
import { CreateGroupForm } from "@/features/groups/components"

export const Route = createFileRoute("/_layout/groups")({
  component: Groups,
  head: () => ({
    meta: [
      {
        title: "Groups - ClearDues",
      },
    ],
  }),
})

function Groups() {
  const { data: groups, isLoading, error } = useUserGroups()
  const [createDialogOpen, setCreateDialogOpen] = useState(false)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-pulse">Loading groups...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-destructive">Failed to load groups</div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-title font-semibold tracking-tight">Expense Groups</h1>
          <p className="text-muted-foreground">
            Manage your expense groups and members
          </p>
        </div>
        <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Create Group
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Group</DialogTitle>
            </DialogHeader>
            <CreateGroupForm onSuccess={() => setCreateDialogOpen(false)} />
          </DialogContent>
        </Dialog>
      </div>

      {!groups?.length ? (
        <div className="flex flex-col items-center justify-center text-center py-12">
          <div className="rounded-full bg-muted p-4 mb-4">
            <Users className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold">No groups yet</h3>
          <p className="text-muted-foreground">
            Create a group to start tracking shared expenses
          </p>
        </div>
      ) : (
        /* Each group is a real URL now (WS5/S4-H3): deep-linkable,
           refreshable, back-button friendly — no more ephemeral useState
           snapshot detail panel */
        <ul className="border-y border-border divide-y divide-border">
          {groups.map((group) => (
            <li key={group.id}>
              <Link
                to="/groups/$groupId"
                params={{ groupId: group.id }}
                className="flex min-h-14 items-center justify-between gap-4 py-4 hover:bg-accent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset"
              >
                <div className="min-w-0 flex-1">
                  <div className="font-medium truncate">{group.name}</div>
                  <div className="text-sm text-muted-foreground">
                    {group.member_count ?? 1} member
                    {(group.member_count ?? 1) !== 1 ? "s" : ""}
                  </div>
                </div>
                <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

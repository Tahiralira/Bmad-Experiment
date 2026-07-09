import { createFileRoute } from "@tanstack/react-router"
import { Plus, Users } from "lucide-react"
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
import { CreateGroupForm, GroupDetail } from "@/features/groups/components"
import type { ExpenseGroup } from "@/features/groups/types"

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
  const [selectedGroup, setSelectedGroup] = useState<ExpenseGroup | null>(null)
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
        <div className="grid gap-6 md:grid-cols-2">
          {/* Groups List */}
          <div className="space-y-3">
            <h2 className="text-lg font-semibold">Your Groups</h2>
            <div className="space-y-2">
              {groups.map((group) => (
                <button
                  key={group.id}
                  onClick={() => setSelectedGroup(group)}
                  className={`w-full rounded-lg border p-4 text-left transition-colors hover:bg-accent ${
                    selectedGroup?.id === group.id
                      ? "border-primary bg-accent"
                      : ""
                  }`}
                >
                  <div className="font-medium">{group.name}</div>
                  <div className="text-sm text-muted-foreground">
                    {group.member_count || 1} member
                    {(group.member_count || 1) !== 1 ? "s" : ""}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Group Detail Panel */}
          <div className="rounded-lg border p-4">
            {selectedGroup ? (
              <GroupDetail group={selectedGroup} />
            ) : (
              <div className="flex h-full items-center justify-center text-muted-foreground">
                Select a group to view details
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

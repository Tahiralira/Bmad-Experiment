// Auth feature components
// Re-export all auth-related components from their current locations
// New code should import from @/features/auth/components

// User Settings components (auth-related user management)
export { default as UserInformation } from "@/components/UserSettings/UserInformation"
export { default as ChangePassword } from "@/components/UserSettings/ChangePassword"
export { default as DeleteAccount } from "@/components/UserSettings/DeleteAccount"
export { default as DeleteConfirmation } from "@/components/UserSettings/DeleteConfirmation"

// Admin components (user administration)
export { default as AddUser } from "@/components/Admin/AddUser"
export { default as EditUser } from "@/components/Admin/EditUser"
export { default as DeleteUser } from "@/components/Admin/DeleteUser"
export { UserActionsMenu } from "@/components/Admin/UserActionsMenu"
export { columns as userColumns } from "@/components/Admin/columns"

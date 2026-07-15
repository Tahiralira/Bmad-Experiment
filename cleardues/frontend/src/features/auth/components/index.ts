// Auth feature components
// Re-export all auth-related components from their current locations
// New code should import from @/features/auth/components
// (Admin + ChangePassword exports died with the WS8 template purge.)

// User Settings components (auth-related user management)
export { default as DeleteAccount } from "@/components/UserSettings/DeleteAccount"
export { default as DeleteConfirmation } from "@/components/UserSettings/DeleteConfirmation"
export { default as UserInformation } from "@/components/UserSettings/UserInformation"

// OAuth components
export { OAuthButtons } from "./OAuthButtons"

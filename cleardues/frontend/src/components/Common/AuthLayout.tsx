import { Appearance } from "@/components/Common/Appearance"
import { Logo } from "@/components/Common/Logo"

interface AuthLayoutProps {
  children: React.ReactNode
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="flex min-h-svh flex-col p-6 md:p-10">
      <div className="flex items-center justify-between">
        <Logo asLink={false} />
        <Appearance />
      </div>
      <div className="flex flex-1 items-center justify-center py-12">
        <div className="w-full max-w-xs">{children}</div>
      </div>
    </div>
  )
}

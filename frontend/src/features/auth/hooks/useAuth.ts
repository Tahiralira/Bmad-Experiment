import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"

import { request as __request } from "@/client/core/request"
import { AuthService, OpenAPI, type UserPublic, UsersService } from "@/shared/api"
import { useCustomToast } from "@/shared/hooks/useCustomToast"
import { handleError } from "@/utils"

const isLoggedIn = () => {
  return localStorage.getItem("access_token") !== null
}

const useAuth = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showErrorToast } = useCustomToast()

  const { data: user } = useQuery<UserPublic | null, Error>({
    queryKey: ["currentUser"],
    queryFn: UsersService.readUserMe,
    enabled: isLoggedIn(),
  })

  const logout = () => {
    // Revoke the token server-side (WS8/S5-H1) — clearing localStorage alone
    // would leave the JWT valid until expiry. Fire-and-forget: the local
    // sign-out must not depend on the network.
    __request(OpenAPI, {
      method: "POST",
      url: "/api/v1/auth/logout",
    }).catch(() => {})
    localStorage.removeItem("access_token")
    queryClient.removeQueries({ queryKey: ["currentUser"] })
    navigate({ to: "/login" })
  }

  // Magic link login - request login link for existing users
  const requestLoginMagicLinkMutation = useMutation({
    mutationFn: (email: string) =>
      AuthService.requestLoginMagicLink({ requestBody: { email } }),
    onError: (err: Parameters<typeof handleError>[0]) =>
      handleError(err, showErrorToast),
  })

  // Magic link login - verify token and store JWT
  const verifyLoginMagicLinkMutation = useMutation({
    mutationFn: async (token: string) => {
      const response = await AuthService.verifyLoginMagicLink({ token })
      localStorage.setItem("access_token", response.access_token)
      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["currentUser"] })
      navigate({ to: "/" })
    },
    onError: (err: Parameters<typeof handleError>[0]) =>
      handleError(err, showErrorToast),
  })

  return {
    logout,
    user,
    requestLoginMagicLinkMutation,
    verifyLoginMagicLinkMutation,
  }
}

export { isLoggedIn }
export { useAuth }
export default useAuth

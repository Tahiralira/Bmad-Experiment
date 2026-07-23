import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { useEffect } from "react"

import { request as __request } from "@/client/core/request"
import {
  EVENTS,
  identifyUser,
  resetAnalytics,
  track,
} from "@/lib/analytics"
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

  // WS10.6: tie analytics to the opaque user UUID (never email/name).
  // identifyUser dedupes repeat calls, so every useAuth mount is safe.
  useEffect(() => {
    if (user?.id) identifyUser(user.id)
  }, [user?.id])

  const logout = () => {
    // Revoke the token server-side (WS8/S5-H1) — clearing localStorage alone
    // would leave the JWT valid until expiry. Fire-and-forget: the local
    // sign-out must not depend on the network.
    __request(OpenAPI, {
      method: "POST",
      url: "/api/v1/auth/logout",
    }).catch(() => {})
    // Capture while still identified, THEN detach analytics identity so a
    // shared device doesn't cross-attribute the next session (WS10.6).
    track(EVENTS.AUTH_LOGGED_OUT)
    resetAnalytics()
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
      track(EVENTS.AUTH_LOGGED_IN, { method: "magic_link" })
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

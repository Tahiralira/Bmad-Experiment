import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"

import {
  type Body_login_login_access_token as AccessToken,
  AuthService,
  LoginService,
  type UserPublic,
  type UserRegister,
  UsersService,
} from "@/shared/api"
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

  const signUpMutation = useMutation({
    mutationFn: (data: UserRegister) =>
      UsersService.registerUser({ requestBody: data }),
    onSuccess: () => {
      navigate({ to: "/login" })
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  const login = async (data: AccessToken) => {
    const response = await LoginService.loginAccessToken({
      formData: data,
    })
    localStorage.setItem("access_token", response.access_token)
  }

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      navigate({ to: "/" })
    },
    onError: handleError.bind(showErrorToast),
  })

  const logout = () => {
    localStorage.removeItem("access_token")
    navigate({ to: "/login" })
  }

  // Magic link login - request login link for existing users
  const requestLoginMagicLinkMutation = useMutation({
    mutationFn: (email: string) =>
      AuthService.requestLoginMagicLink({ requestBody: { email } }),
    onError: handleError.bind(showErrorToast),
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
    onError: handleError.bind(showErrorToast),
  })

  return {
    signUpMutation,
    loginMutation,
    logout,
    user,
    requestLoginMagicLinkMutation,
    verifyLoginMagicLinkMutation,
  }
}

export { isLoggedIn }
export { useAuth }
export default useAuth

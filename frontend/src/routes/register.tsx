import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation } from "@tanstack/react-query"
import {
  createFileRoute,
  Link as RouterLink,
  redirect,
} from "@tanstack/react-router"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { AuthService } from "@/client"
import { AuthLayout } from "@/components/Common/AuthLayout"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import { OAuthButtons } from "@/features/auth/components"
import { isLoggedIn } from "@/hooks/useAuth"
import { useCustomToast } from "@/shared/hooks/useCustomToast"
import { handleError } from "@/utils"

const formSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
})

type FormData = z.infer<typeof formSchema>

export const Route = createFileRoute("/register")({
  component: Register,
  beforeLoad: async () => {
    if (isLoggedIn()) {
      throw redirect({
        to: "/",
      })
    }
  },
  head: () => ({
    meta: [
      {
        title: "Register - ClearDues",
      },
    ],
  }),
})

function Register() {
  const [submitted, setSubmitted] = useState(false)
  const { showErrorToast, showSuccessToast } = useCustomToast()

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      email: "",
    },
  })

  const registerMutation = useMutation({
    mutationFn: (data: { email: string }) =>
      AuthService.requestMagicLink({ requestBody: data }),
    onSuccess: () => {
      setSubmitted(true)
      showSuccessToast("Check your email for the magic link!")
    },
    onError: (err: unknown) => handleError(err, showErrorToast),
  })

  const onSubmit = (data: FormData) => {
    if (registerMutation.isPending) return
    registerMutation.mutate(data)
  }

  if (submitted) {
    return (
      <AuthLayout>
        <div className="flex flex-col items-center gap-6 text-center">
          <div className="rounded-full bg-success-subtle p-4">
            <svg
              className="h-12 w-12 text-success"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 19v-8.93a2 2 0 01.89-1.664l7-4.666a2 2 0 012.22 0l7 4.666A2 2 0 0121 10.07V19M3 19a2 2 0 002 2h14a2 2 0 002-2M3 19l6.75-4.5M21 19l-6.75-4.5M3 10l6.75 4.5M21 10l-6.75 4.5m0 0l-1.14.76a2 2 0 01-2.22 0l-1.14-.76"
              />
            </svg>
          </div>

          <div className="space-y-2">
            <h1 className="text-title font-semibold">Check your email</h1>
            <p className="text-muted-foreground">
              We've sent a magic link to{" "}
              <strong>{form.getValues("email")}</strong>
            </p>
            <p className="text-sm text-muted-foreground">
              Click the link in the email to complete your registration. The
              link expires in 15 minutes.
            </p>
          </div>

          <div className="space-y-2 text-sm">
            <p className="text-muted-foreground">
              Didn't receive the email?{" "}
              <button
                onClick={() => setSubmitted(false)}
                className="text-primary underline underline-offset-4"
              >
                Try again
              </button>
            </p>
          </div>

          <div className="text-center text-sm">
            Already have an account?{" "}
            <RouterLink to="/login" className="underline underline-offset-4">
              Log in
            </RouterLink>
          </div>
        </div>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout>
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="flex flex-col gap-6"
        >
          <div className="flex flex-col items-center gap-2 text-center">
            <h1 className="text-title font-semibold">Create an account</h1>
            <p className="text-muted-foreground">
              Enter your email to receive a magic link
            </p>
          </div>

          <div className="grid gap-4">
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input
                      data-testid="email-input"
                      placeholder="user@example.com"
                      type="email"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage className="text-xs" />
                </FormItem>
              )}
            />

            <LoadingButton
              type="submit"
              className="w-full"
              loading={registerMutation.isPending}
            >
              Send Magic Link
            </LoadingButton>

            <OAuthButtons disabled={registerMutation.isPending} />
          </div>

          <div className="text-center text-sm">
            Already have an account?{" "}
            <RouterLink to="/login" className="underline underline-offset-4">
              Log in
            </RouterLink>
          </div>
        </form>
      </Form>
    </AuthLayout>
  )
}

export default Register

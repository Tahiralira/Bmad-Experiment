import {
  MutationCache,
  QueryCache,
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query"
import { createRouter, RouterProvider } from "@tanstack/react-router"
import { StrictMode } from "react"
import ReactDOM from "react-dom/client"
import { toast } from "sonner"
import { ApiError, OpenAPI } from "./client"
import { ThemeProvider } from "./components/theme-provider"
import { Toaster } from "./components/ui/sonner"
import "./index.css"
import { routeTree } from "./routeTree.gen"

OpenAPI.BASE = import.meta.env.VITE_API_URL
OpenAPI.TOKEN = async () => {
  return localStorage.getItem("access_token") || ""
}

const router = createRouter({ routeTree })

// S4-H1: only 401 (invalid/expired session) ends the session. 403 is a
// BUSINESS authorization denial ("only the creator can edit") — surfacing it
// as a toast instead of destroying the session, and navigating via the
// router instead of a hard redirect that throws away SPA state.
const handleUnauthorized = (error: Error) => {
  if (error instanceof ApiError && error.status === 401) {
    localStorage.removeItem("access_token")
    router.navigate({ to: "/login" })
  }
}

// Queries render error states but have no local toasts, so the denial would
// otherwise be silent. Mutations already show their own error toasts —
// toasting 403s here too would double-toast them.
const handleQueryError = (error: Error) => {
  handleUnauthorized(error)
  if (error instanceof ApiError && error.status === 403) {
    const detail = (error.body as { detail?: unknown } | null)?.detail
    toast.error(
      typeof detail === "string"
        ? detail
        : "You don't have permission to view that.",
    )
  }
}

const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: handleQueryError,
  }),
  mutationCache: new MutationCache({
    onError: handleUnauthorized,
  }),
})
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router
  }
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
        <Toaster richColors closeButton />
      </QueryClientProvider>
    </ThemeProvider>
  </StrictMode>,
)

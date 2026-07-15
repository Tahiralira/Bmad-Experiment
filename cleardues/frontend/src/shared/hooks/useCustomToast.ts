import { toast } from "sonner"

export const useCustomToast = () => {
  const showSuccessToast = (description: string) => {
    toast.success("Success!", {
      description,
    })
  }

  const showErrorToast = (description: string) => {
    // Mediator voice (UX-H4): calm, no exclamation, no blame
    toast.error("That didn't go through", {
      description,
    })
  }

  return { showSuccessToast, showErrorToast }
}

export default useCustomToast

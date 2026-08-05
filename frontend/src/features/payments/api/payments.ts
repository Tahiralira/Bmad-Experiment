import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import { request as __request } from "@/client/core/request"
import { EVENTS, track } from "@/lib/analytics"
import { OpenAPI } from "@/shared/api"
import { getApiErrorMessage } from "@/utils"
import type {
  PaymentMethod,
  PaymentMethodCreate,
  PaymentMethodUpdate,
  PaymentMethodsResponse,
} from "../types"

// === My payment methods (self-service registry) ===

const MY_KEY = ["payment-methods", "me"]

async function listMyPaymentMethods(): Promise<PaymentMethodsResponse> {
  return __request(OpenAPI, {
    method: "GET",
    url: "/api/v1/users/me/payment-methods",
    errors: { 401: "Unauthorized" },
  })
}

export function useMyPaymentMethods() {
  return useQuery<PaymentMethodsResponse, Error>({
    queryKey: MY_KEY,
    queryFn: listMyPaymentMethods,
  })
}

async function createPaymentMethod(
  data: PaymentMethodCreate,
): Promise<PaymentMethod> {
  return __request(OpenAPI, {
    method: "POST",
    url: "/api/v1/users/me/payment-methods",
    body: data,
    errors: {
      401: "Unauthorized",
      409: "That payment method is already saved",
      422: "Check the handle and try again",
    },
  })
}

export function useCreatePaymentMethod() {
  const queryClient = useQueryClient()
  return useMutation<PaymentMethod, Error, PaymentMethodCreate>({
    mutationFn: createPaymentMethod,
    onSuccess: (method) => {
      // Provider code only — never the handle itself (it's a payment address)
      track(EVENTS.PAYMENT_METHOD_ADDED, { provider: method.provider })
      queryClient.invalidateQueries({ queryKey: MY_KEY })
      toast.success("Payment method saved")
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  })
}

async function updatePaymentMethod(
  id: string,
  data: PaymentMethodUpdate,
): Promise<PaymentMethod> {
  return __request(OpenAPI, {
    method: "PUT",
    url: `/api/v1/users/me/payment-methods/${id}`,
    body: data,
    errors: {
      401: "Unauthorized",
      404: "Payment method not found",
      409: "That payment method is already saved",
    },
  })
}

export function useUpdatePaymentMethod() {
  const queryClient = useQueryClient()
  return useMutation<
    PaymentMethod,
    Error,
    { id: string; data: PaymentMethodUpdate }
  >({
    mutationFn: ({ id, data }) => updatePaymentMethod(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MY_KEY })
      toast.success("Payment method updated")
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  })
}

async function deletePaymentMethod(id: string): Promise<{ message: string }> {
  return __request(OpenAPI, {
    method: "DELETE",
    url: `/api/v1/users/me/payment-methods/${id}`,
    errors: { 401: "Unauthorized", 404: "Payment method not found" },
  })
}

export function useDeletePaymentMethod() {
  const queryClient = useQueryClient()
  return useMutation<{ message: string }, Error, string>({
    mutationFn: deletePaymentMethod,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MY_KEY })
      toast.success("Payment method removed")
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  })
}

// === Counterparty payment methods (surfaced at settle time) ===

async function getMemberPaymentMethods(
  groupId: string,
  userId: string,
): Promise<PaymentMethodsResponse> {
  return __request(OpenAPI, {
    method: "GET",
    url: `/api/v1/expense-groups/${groupId}/members/${userId}/payment-methods`,
    errors: {
      401: "Unauthorized",
      403: "You are not a member of this group",
      404: "That person isn't a member of this group",
    },
  })
}

/**
 * A group member's payment handles, for when you owe them money. Fetched
 * lazily — pass enabled=true only when the settle UI actually shows them.
 */
export function useCounterpartyPaymentMethods(
  groupId: string,
  userId: string,
  enabled: boolean,
) {
  return useQuery<PaymentMethodsResponse, Error>({
    queryKey: ["payment-methods", "counterparty", groupId, userId],
    queryFn: () => getMemberPaymentMethods(groupId, userId),
    enabled: enabled && !!groupId && !!userId,
  })
}

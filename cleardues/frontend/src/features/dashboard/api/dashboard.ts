import { useQuery } from "@tanstack/react-query"

import { request as __request } from "@/client/core/request"
import { OpenAPI } from "@/shared/api"
import type { DashboardResponse } from "../types"

async function getDashboard(): Promise<DashboardResponse> {
  return __request(OpenAPI, {
    method: "GET",
    url: "/api/v1/users/me/dashboard",
    errors: {
      401: "Unauthorized",
    },
  })
}

export function useDashboard() {
  return useQuery<DashboardResponse, Error>({
    queryKey: ["dashboard"],
    queryFn: getDashboard,
  })
}

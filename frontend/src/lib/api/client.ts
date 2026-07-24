import { environment } from "@/lib/config/environment";

import type { ApiErrorResponse } from "./types";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly requestId?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiGet<T>(
  path: string,
  signal?: AbortSignal,
): Promise<T> {
  const timeout = AbortSignal.timeout(5_000);
  const combinedSignal = signal ? AbortSignal.any([signal, timeout]) : timeout;
  let response: Response;
  try {
    response = await fetch(`${environment.NEXT_PUBLIC_API_BASE_URL}${path}`, {
      headers: { Accept: "application/json" },
      signal: combinedSignal,
    });
  } catch {
    throw new ApiError("Cannot connect to the backend.", "CONNECTION_ERROR");
  }
  if (!response.ok) {
    const body = (await response
      .json()
      .catch(() => null)) as ApiErrorResponse | null;
    throw new ApiError(
      body?.error.message ?? "The backend request failed.",
      body?.error.code ?? "REQUEST_FAILED",
      body?.error.request_id,
    );
  }
  return (await response.json()) as T;
}

import { z } from "zod";
import { env } from "@/lib/env";

/** Error carrying the HTTP status so callers/UI can branch on 404/409/413/... */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }

  /** True for the codes the backend uses for user-correctable problems. */
  get isClientError() {
    return this.status >= 400 && this.status < 500;
  }
}

/** Pull a useful message out of FastAPI's `{ detail }` error shape. */
async function extractErrorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
    if (Array.isArray(body?.detail) && body.detail[0]?.msg) {
      return body.detail[0].msg;
    }
  } catch {
    /* not JSON — fall through */
  }
  return res.statusText || `Request failed (${res.status})`;
}

type RequestOptions = {
  method?: string;
  /** JSON body — mutually exclusive with `formData`. */
  body?: unknown;
  /** Raw FormData for multipart uploads (file uploads). */
  formData?: FormData;
  signal?: AbortSignal;
  /**
   * Single place to inject an Authorization header later. The backend has no
   * auth yet (see FRONTEND_PROMPT §6); this keeps that change to one location.
   */
  authToken?: string;
};

/**
 * Thin fetch wrapper: builds the URL, sets headers, parses + validates the
 * response against a Zod schema. The only way the app talks to the backend.
 */
async function request<T>(
  path: string,
  schema: z.ZodType<T>,
  options: RequestOptions = {},
): Promise<T> {
  const { method = "GET", body, formData, signal, authToken } = options;

  const headers: Record<string, string> = {};
  if (authToken) headers["Authorization"] = `Bearer ${authToken}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";

  let res: Response;
  try {
    res = await fetch(`${env.apiBaseUrl}${path}`, {
      method,
      headers,
      body: formData ?? (body !== undefined ? JSON.stringify(body) : undefined),
      signal,
    });
  } catch {
    // Network failure / CORS block / server down.
    throw new ApiError(
      0,
      "Could not reach the server. Check that the API is running and CORS allows this origin.",
    );
  }

  if (!res.ok) {
    throw new ApiError(res.status, await extractErrorMessage(res));
  }

  // 204 No Content (deletes) — nothing to parse.
  if (res.status === 204 || res.headers.get("content-length") === "0") {
    return schema.parse(undefined);
  }

  const json = await res.json();
  return schema.parse(json);
}

export const apiClient = {
  get: <T>(path: string, schema: z.ZodType<T>, signal?: AbortSignal) =>
    request(path, schema, { method: "GET", signal }),

  post: <T>(path: string, schema: z.ZodType<T>, body?: unknown) =>
    request(path, schema, { method: "POST", body }),

  patch: <T>(path: string, schema: z.ZodType<T>, body?: unknown) =>
    request(path, schema, { method: "PATCH", body }),

  postForm: <T>(path: string, schema: z.ZodType<T>, formData: FormData) =>
    request(path, schema, { method: "POST", formData }),

  delete: (path: string) =>
    request(path, z.void(), { method: "DELETE" }),
};

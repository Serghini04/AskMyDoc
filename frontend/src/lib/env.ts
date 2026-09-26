/**
 * Centralized, validated access to public env config.
 * Keeping this in one place means there's exactly one spot to change the host
 * and one spot to add auth/base-path concerns later.
 */
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export const env = {
  apiBaseUrl: API_BASE_URL.replace(/\/$/, ""),
} as const;

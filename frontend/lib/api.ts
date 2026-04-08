export const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? 'http://localhost:8000';

/**
 * Constructs the health-check URL for a backend base URL.
 *
 * @param baseUrl - The backend base URL to use; defaults to the exported `backendUrl`. Any trailing slash on `baseUrl` is ignored.
 * @returns The full health endpoint URL (base URL with `/health` appended).
 */
export function healthEndpoint(baseUrl = backendUrl): string {
  return `${baseUrl.replace(/\/$/, '')}/health`;
}

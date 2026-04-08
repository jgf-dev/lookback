export const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? 'http://localhost:8000';

export function healthEndpoint(baseUrl = backendUrl): string {
  return `${baseUrl.replace(/\/$/, '')}/health`;
}

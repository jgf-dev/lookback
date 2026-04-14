export const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? 'http://localhost:8000';

const base = () => backendUrl.replace(/\/$/, '');

export function healthEndpoint(baseUrl = backendUrl): string {
  return `${baseUrl.replace(/\/$/, '')}/health`;
}

export function itemsEndpoint(baseUrl = backendUrl): string {
  return `${baseUrl.replace(/\/$/, '')}/api/items`;
}

export function timelineWsEndpoint(baseUrl = backendUrl): string {
  const http = baseUrl.replace(/\/$/, '');
  const ws = http.replace(/^https?/, (p) => (p === 'https' ? 'wss' : 'ws'));
  return `${ws}/api/ws/timeline`;
}

export function reviewTodayEndpoint(baseUrl = backendUrl): string {
  return `${baseUrl.replace(/\/$/, '')}/api/review/today`;
}

// ─── Types ───────────────────────────────────────────────────────────────────

export interface Relationship {
  target_item_id: number;
  relationship_type: string;
  confidence: number | null;
  provenance: Record<string, unknown>;
}

export interface CapturedItem {
  id: number;
  timestamp: string;
  source_type: string;
  raw_content: string;
  enriched_content: string | null;
  tags: string[];
  inferred_project_task: string | null;
  relationships: Relationship[];
  confidence: number | null;
  user_edits: Record<string, unknown> | null;
  provenance: Record<string, unknown>;
}

export interface ReviewResponse {
  voice_review_script: string;
  next_actions: string[];
}

export interface ItemUpdatePayload {
  raw_content?: string;
  enriched_content?: string;
  tags?: string[];
  confidence?: number;
  user_edits?: Record<string, unknown>;
  provenance?: Record<string, unknown>;
}

// ─── API calls ────────────────────────────────────────────────────────────────

export async function fetchItems(opts?: {
  source_type?: string;
  tag?: string;
}): Promise<CapturedItem[]> {
  const url = new URL(itemsEndpoint());
  if (opts?.source_type) url.searchParams.set('source_type', opts.source_type);
  if (opts?.tag) url.searchParams.set('tag', opts.tag);
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`fetchItems failed: ${res.status}`);
  return res.json() as Promise<CapturedItem[]>;
}

export async function createNote(rawContent: string): Promise<CapturedItem> {
  const now = new Date().toISOString();
  const res = await fetch(itemsEndpoint(), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      timestamp: now,
      source_type: 'manual_note',
      raw_content: rawContent,
    }),
  });
  if (!res.ok) throw new Error(`createNote failed: ${res.status}`);
  return res.json() as Promise<CapturedItem>;
}

export async function updateItem(
  id: number,
  payload: ItemUpdatePayload,
): Promise<CapturedItem> {
  const res = await fetch(`${itemsEndpoint()}/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`updateItem failed: ${res.status}`);
  return res.json() as Promise<CapturedItem>;
}

export async function transcribeAudio(file: File): Promise<CapturedItem> {
  const form = new FormData();
  form.append('audio', file);
  const res = await fetch(`${base()}/api/items/transcribe`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) throw new Error(`transcribeAudio failed: ${res.status}`);
  return res.json() as Promise<CapturedItem>;
}

export async function uploadScreenshot(file: File): Promise<CapturedItem> {
  const form = new FormData();
  form.append('image', file);
  const res = await fetch(`${base()}/api/items/screenshot`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) throw new Error(`uploadScreenshot failed: ${res.status}`);
  return res.json() as Promise<CapturedItem>;
}

export async function fetchTodayReview(): Promise<ReviewResponse> {
  const res = await fetch(reviewTodayEndpoint());
  if (!res.ok) throw new Error(`fetchTodayReview failed: ${res.status}`);
  return res.json() as Promise<ReviewResponse>;
}

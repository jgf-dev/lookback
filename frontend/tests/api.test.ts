import { describe, expect, it } from 'vitest';
import {
  healthEndpoint,
  itemsEndpoint,
  reviewTodayEndpoint,
  timelineWsEndpoint,
} from '../lib/api';

// ─── Endpoint URL helpers ─────────────────────────────────────────────────────

describe('healthEndpoint', () => {
  it('appends /health to the base URL', () => {
    expect(healthEndpoint('http://localhost:8000')).toBe('http://localhost:8000/health');
  });

  it('strips trailing slash before appending', () => {
    expect(healthEndpoint('http://localhost:8000/')).toBe('http://localhost:8000/health');
  });
});

describe('itemsEndpoint', () => {
  it('returns /api/items path', () => {
    expect(itemsEndpoint('http://localhost:8000')).toBe('http://localhost:8000/api/items');
  });

  it('strips trailing slash', () => {
    expect(itemsEndpoint('http://backend/')).toBe('http://backend/api/items');
  });
});

describe('timelineWsEndpoint', () => {
  it('converts http to ws', () => {
    expect(timelineWsEndpoint('http://localhost:8000')).toBe(
      'ws://localhost:8000/api/ws/timeline',
    );
  });

  it('converts https to wss', () => {
    expect(timelineWsEndpoint('https://app.example.com')).toBe(
      'wss://app.example.com/api/ws/timeline',
    );
  });

  it('strips trailing slash before converting', () => {
    expect(timelineWsEndpoint('http://localhost:8000/')).toBe(
      'ws://localhost:8000/api/ws/timeline',
    );
  });
});

describe('reviewTodayEndpoint', () => {
  it('returns /api/review/today path', () => {
    expect(reviewTodayEndpoint('http://localhost:8000')).toBe(
      'http://localhost:8000/api/review/today',
    );
  });

  it('strips trailing slash', () => {
    expect(reviewTodayEndpoint('http://backend/')).toBe('http://backend/api/review/today');
  });
});

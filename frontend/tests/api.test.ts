import { describe, expect, it } from 'vitest';

import { healthEndpoint } from '../lib/api';

describe('healthEndpoint', () => {
  it('builds /health URL without duplicate slashes', () => {
    expect(healthEndpoint('http://localhost:8000/')).toBe('http://localhost:8000/health');
  });
});

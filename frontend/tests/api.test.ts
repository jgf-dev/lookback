import { describe, expect, it } from 'vitest';

import { healthEndpoint } from '../lib/api';

describe('healthEndpoint', () => {
  it('builds /health URL without duplicate slashes', () => {
    expect(healthEndpoint('http://localhost:8000/')).toBe('http://localhost:8000/health');
  });

  it('appends /health to URL without trailing slash', () => {
    expect(healthEndpoint('http://localhost:8000')).toBe('http://localhost:8000/health');
  });

  it('works with https scheme', () => {
    expect(healthEndpoint('https://api.example.com')).toBe('https://api.example.com/health');
  });

  it('works with https and trailing slash', () => {
    expect(healthEndpoint('https://api.example.com/')).toBe('https://api.example.com/health');
  });

  it('preserves port in URL', () => {
    expect(healthEndpoint('http://localhost:3001')).toBe('http://localhost:3001/health');
  });

  it('preserves port with trailing slash', () => {
    expect(healthEndpoint('http://localhost:3001/')).toBe('http://localhost:3001/health');
  });

  it('works with IP address', () => {
    expect(healthEndpoint('http://192.168.1.1:8000')).toBe('http://192.168.1.1:8000/health');
  });

  it('works with subdomain URL', () => {
    expect(healthEndpoint('https://backend.staging.example.com')).toBe(
      'https://backend.staging.example.com/health'
    );
  });

  it('uses default backendUrl when no argument given', () => {
    // healthEndpoint() with no arg uses module-level backendUrl default
    const result = healthEndpoint();
    expect(result).toMatch(/\/health$/);
  });

  it('always ends with /health', () => {
    const urls = [
      'http://localhost:8000',
      'http://localhost:8000/',
      'https://example.com',
      'https://example.com/',
    ];
    for (const url of urls) {
      expect(healthEndpoint(url)).toMatch(/\/health$/);
    }
  });

  it('does not double-append /health', () => {
    const result = healthEndpoint('http://localhost:8000');
    expect(result).toBe('http://localhost:8000/health');
    expect(result.split('/health').length - 1).toBe(1);
  });
});
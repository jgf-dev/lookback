import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import RootLayout from '../app/layout';

describe('RootLayout', () => {
  it('renders required html and body wrappers', () => {
    const markup = renderToStaticMarkup(
      <RootLayout>
        <div>content</div>
      </RootLayout>
    );

    expect(markup).toContain('<html lang="en">');
    expect(markup).toContain('<body>');
    expect(markup).toContain('content');
  });
});

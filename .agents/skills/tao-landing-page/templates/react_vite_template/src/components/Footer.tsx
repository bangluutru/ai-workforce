import React from 'react';
import type { SiteContent } from '../types/content';
import { Text } from './Text';

export const Footer: React.FC<{ content: SiteContent }> = ({ content }) => {
  const f = content.footer;
  return (
    <footer className="py-10 border-t border-brand-border bg-brand-background text-sm text-brand-muted">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 grid gap-2">
        <p className="font-semibold text-brand-text"><Text value={f.company} /></p>
        {f.address && <p><Text value={f.address} /></p>}
        {f.phone && <p><Text value={f.phone} /></p>}
        {f.email && <p><Text value={f.email} /></p>}
        {f.lines?.map((l, i) => (
          <p key={i}><Text value={l} /></p>
        ))}
      </div>
    </footer>
  );
};

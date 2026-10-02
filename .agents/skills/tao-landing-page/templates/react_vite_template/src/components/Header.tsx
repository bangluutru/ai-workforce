import React from 'react';
import type { SiteContent } from '../types/content';
import { CtaLink } from './CtaLink';
import { Text } from './Text';

export const Header: React.FC<{ content: SiteContent }> = ({ content }) => {
  const { brand, header, form } = content;
  return (
    <header className="sticky top-0 z-40 bg-brand-background border-b border-brand-border backdrop-blur">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
        <a href="#top" className="font-heading text-lg sm:text-xl font-bold text-brand-text truncate">
          <Text value={brand.name} />
        </a>
        <nav className="flex items-center gap-4">
          {header.nav?.map((n) => (
            <a key={n.target} href={n.target} className="hidden md:inline text-sm text-brand-muted hover:text-brand-text">
              <Text value={n.label} />
            </a>
          ))}
          {header.phone && (
            <a href={`tel:${header.phone.replace(/\s/g, '')}`} className="hidden md:inline text-sm font-semibold text-brand-text">
              <Text value={header.phone} />
            </a>
          )}
          {header.ctaLabel && (
            <CtaLink cta={{ label: header.ctaLabel, target: `#${form?.id ?? 'form'}` }} id="btn_header_cta" section="header" className="!min-h-[44px] !px-4 text-sm" />
          )}
        </nav>
      </div>
    </header>
  );
};

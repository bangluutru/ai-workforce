import React from 'react';
import { LPHub } from '../lib/lphub';
import type { Cta } from '../types/content';
import { Text } from './Text';

const styles = {
  primary:
    'inline-flex items-center justify-center min-h-[48px] px-6 rounded-brand font-semibold bg-brand-primary text-brand-on-primary hover:opacity-90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-primary transition',
  secondary:
    'inline-flex items-center justify-center min-h-[48px] px-6 rounded-brand font-semibold border border-brand-border text-brand-text hover:bg-brand-surface focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-primary transition',
};

export const CtaLink: React.FC<{ cta: Cta; id: string; section: string; variant?: 'primary' | 'secondary'; className?: string }> = ({
  cta,
  id,
  section,
  variant = 'primary',
  className = '',
}) => (
  <a
    href={cta.target}
    className={`${styles[variant]} ${className}`}
    onClick={() => LPHub.track('cta_click', { buttonId: id, section, label: cta.label })}
  >
    <Text value={cta.label} />
  </a>
);

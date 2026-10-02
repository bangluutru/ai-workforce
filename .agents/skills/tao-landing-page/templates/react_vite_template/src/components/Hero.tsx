import React from 'react';
import type { SiteContent } from '../types/content';
import { CtaLink } from './CtaLink';
import { Text } from './Text';

export const Hero: React.FC<{ content: SiteContent }> = ({ content }) => {
  const { hero } = content;
  const hasImage = Boolean(hero.image?.src);
  return (
    <section id="top" className="bg-brand-surface">
      <div className={`max-w-6xl mx-auto px-4 sm:px-6 py-14 sm:py-20 grid gap-10 items-center ${hasImage ? 'lg:grid-cols-2' : ''}`}>
        <div className={hasImage ? '' : 'max-w-3xl'}>
          {hero.eyebrow && (
            <p className="text-sm font-semibold uppercase tracking-[0.14em] text-brand-accent mb-4">
              <Text value={hero.eyebrow} />
            </p>
          )}
          <h1 className="font-heading text-4xl sm:text-5xl lg:text-6xl font-bold leading-[1.08] text-brand-text">
            <Text value={hero.headline} />
          </h1>
          {hero.subheadline && (
            <p className="mt-5 text-lg leading-relaxed text-brand-muted max-w-xl">
              <Text value={hero.subheadline} />
            </p>
          )}
          <div className="mt-8 flex flex-col sm:flex-row gap-3">
            <CtaLink cta={hero.primaryCta} id="btn_hero_primary" section="hero" />
            {hero.secondaryCta && <CtaLink cta={hero.secondaryCta} id="btn_hero_secondary" section="hero" variant="secondary" />}
          </div>
          {hero.stats && hero.stats.length > 0 && (
            <dl className="mt-10 grid grid-cols-3 gap-4 max-w-lg">
              {hero.stats.map((s) => (
                <div key={s.label} className="border-t border-brand-border pt-3 flex flex-col-reverse">
                  <dt className="text-xs sm:text-sm text-brand-muted mt-1"><Text value={s.label} /></dt>
                  <dd className="font-heading text-2xl sm:text-3xl font-bold text-brand-primary"><Text value={s.value} /></dd>
                </div>
              ))}
            </dl>
          )}
        </div>
        {hasImage && (
          <img
            src={hero.image!.src}
            alt={hero.image!.alt}
            width={960}
            height={720}
            loading="eager"
            {...{ fetchpriority: 'high' }} /* ảnh LCP: tải ngay, ưu tiên cao */
            decoding="async"
            className="w-full aspect-[4/3] object-cover rounded-brand"
          />
        )}
      </div>
    </section>
  );
};

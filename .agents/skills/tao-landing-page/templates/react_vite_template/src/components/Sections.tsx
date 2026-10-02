import React from 'react';
import type { Section } from '../types/content';
import { Text } from './Text';

const SectionHead: React.FC<{ eyebrow?: string; title: string; intro?: string }> = ({ eyebrow, title, intro }) => (
  <div className="max-w-2xl mb-10">
    {eyebrow && (
      <p className="text-sm font-semibold uppercase tracking-[0.14em] text-brand-accent mb-3">
        <Text value={eyebrow} />
      </p>
    )}
    <h2 className="font-heading text-3xl sm:text-4xl font-bold text-brand-text leading-tight">
      <Text value={title} />
    </h2>
    {intro && (
      <p className="mt-4 text-brand-muted text-lg leading-relaxed">
        <Text value={intro} />
      </p>
    )}
  </div>
);

const SectionBody: React.FC<{ s: Section }> = ({ s }) => {
  switch (s.type) {
    case 'cards':
      return (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {s.items.map((it, i) => (
            <article key={i} className="rounded-brand border border-brand-border bg-brand-surface p-6">
              <h3 className="font-heading text-xl font-semibold text-brand-text"><Text value={it.title} /></h3>
              {it.description && <p className="mt-2 text-brand-muted leading-relaxed"><Text value={it.description} /></p>}
            </article>
          ))}
        </div>
      );
    case 'pricelist':
      return (
        <>
          <div className="grid gap-10 md:grid-cols-2 lg:grid-cols-3">
            {s.groups.map((g, gi) => (
              <div key={gi}>
                {g.title && <h3 className="font-heading text-xl font-semibold text-brand-primary mb-3"><Text value={g.title} /></h3>}
                <ul>
                  {g.items.map((it, ii) => (
                    <li key={ii} className="flex items-baseline justify-between gap-4 border-b border-brand-border py-3">
                      <span>
                        <span className="font-medium text-brand-text"><Text value={it.name} /></span>
                        {it.note && <span className="block text-sm text-brand-muted"><Text value={it.note} /></span>}
                      </span>
                      {it.price && <span className="font-semibold text-brand-primary whitespace-nowrap"><Text value={it.price} /></span>}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
          {s.note && <p className="mt-6 text-sm text-brand-muted"><Text value={s.note} /></p>}
        </>
      );
    case 'faq':
      return (
        <div className="divide-y divide-brand-border border-y border-brand-border max-w-3xl">
          {s.items.map((f, i) => (
            <details key={i} className="py-4 group">
              <summary className="cursor-pointer font-semibold text-brand-text list-none flex justify-between gap-4 min-h-[44px] items-center">
                <Text value={f.question} />
                <span aria-hidden className="text-brand-primary group-open:rotate-45 transition">+</span>
              </summary>
              <p className="mt-2 text-brand-muted leading-relaxed"><Text value={f.answer} /></p>
            </details>
          ))}
        </div>
      );
    case 'text':
      return (
        <div className="max-w-3xl space-y-4 text-lg leading-relaxed text-brand-muted">
          {s.paragraphs.map((p, i) => (
            <p key={i}><Text value={p} /></p>
          ))}
        </div>
      );
  }
};

export const Sections: React.FC<{ sections: Section[] }> = ({ sections }) => (
  <>
    {sections.map((s, i) => (
      <section key={s.id} id={s.id} className={`below-fold py-16 sm:py-20 ${i % 2 ? 'bg-brand-surface' : 'bg-brand-background'}`}>
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <SectionHead eyebrow={s.eyebrow} title={s.title} intro={'intro' in s ? s.intro : undefined} />
          <SectionBody s={s} />
        </div>
      </section>
    ))}
  </>
);

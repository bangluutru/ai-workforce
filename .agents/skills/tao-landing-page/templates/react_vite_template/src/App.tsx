import React, { useEffect } from 'react';
import contentJson from './content.json';
import type { SiteContent } from './types/content';
import { LPHub } from './lib/lphub';
import { Header } from './components/Header';
import { Hero } from './components/Hero';
import { Sections } from './components/Sections';
import { LandingForm } from './components/LandingForm';
import { Footer } from './components/Footer';

const content = contentJson as unknown as SiteContent;

export default function App() {
  useEffect(() => {
    LPHub.init({
      projectId: content.hub.projectId,
      landingPageId: content.hub.landingPageId,
      apiUrl: import.meta.env.VITE_LPHUB_URL ?? '',
      autoPageView: true,
    });
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-brand-background text-brand-text font-body">
      <Header content={content} />
      <main className="flex-grow">
        <Hero content={content} />
        <Sections sections={content.sections} />
        {content.form && <LandingForm form={content.form} hub={content.hub} />}
      </main>
      <Footer content={content} />
    </div>
  );
}

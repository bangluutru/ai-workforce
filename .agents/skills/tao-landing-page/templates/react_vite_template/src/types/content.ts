// Kiểu dữ liệu của src/content.json (sinh bởi landing_builder.py từ landing_spec.json).
// Mọi chữ hiển thị trên trang nằm trong content.json - component KHÔNG chứa câu chữ marketing cố định.

export interface Cta {
  label: string;
  target: string; // '#form' | '#section-id' | 'tel:...' | 'https://...'
}

export interface HeroImage {
  src: string;
  alt: string;
}

export interface Stat {
  value: string;
  label: string;
}

export interface CardItem {
  title: string;
  description?: string;
}

export interface PriceItem {
  name: string;
  price?: string;
  note?: string;
}

export interface PriceGroup {
  title?: string;
  items: PriceItem[];
}

export interface FaqItem {
  question: string;
  answer: string;
}

export type Section =
  | { type: 'cards'; id: string; eyebrow?: string; title: string; intro?: string; items: CardItem[] }
  | { type: 'pricelist'; id: string; eyebrow?: string; title: string; intro?: string; groups: PriceGroup[]; note?: string }
  | { type: 'faq'; id: string; eyebrow?: string; title: string; items: FaqItem[] }
  | { type: 'text'; id: string; eyebrow?: string; title: string; paragraphs: string[] };

export type FieldType = 'text' | 'tel' | 'email' | 'number' | 'date' | 'time' | 'textarea' | 'select';

export interface FormField {
  key: string; // name | phone | email | address | note | <khóa tùy chỉnh>
  label: string;
  type: FieldType;
  required?: boolean;
  placeholder?: string;
  options?: string[];
  min?: number;
  max?: number;
}

export interface OrderProduct {
  id: string;
  name: string;
  unitPrice: number; // VND, bắt buộc có nguồn từ người dùng
  currency: string;
}

export interface FormContent {
  id: string; // anchor id, mặc định 'form'
  type: 'lead' | 'order' | 'custom';
  eyebrow?: string;
  title: string;
  intro?: string;
  submitLabel: string;
  successTitle: string;
  successMessage: string;
  errorMessage: string;
  consentText?: string;
  fields: FormField[];
  product?: OrderProduct;
}

export interface SiteContent {
  meta: { title: string; description: string; lang: string };
  brand: { name: string; tagline?: string };
  header: { ctaLabel?: string; phone?: string; nav?: { label: string; target: string }[] };
  hero: {
    eyebrow?: string;
    headline: string;
    subheadline?: string;
    primaryCta: Cta;
    secondaryCta?: Cta;
    image?: HeroImage;
    stats?: Stat[];
  };
  sections: Section[];
  form?: FormContent;
  footer: { company: string; address?: string; phone?: string; email?: string; lines?: string[] };
  hub: { projectId: string; landingPageId: string; formId: string };
}

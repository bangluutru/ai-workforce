/** @type {import('tailwindcss').Config} */
// Mọi màu/font giao diện đi qua token brand-* (CSS variables sinh từ landing_spec.json -> src/theme.css).
// KHÔNG dùng màu Tailwind cố định (teal-*, slate-*, purple-*...) trong component.
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: 'var(--color-primary)',
          'on-primary': 'var(--color-on-primary)',
          secondary: 'var(--color-secondary)',
          accent: 'var(--color-accent)',
          background: 'var(--color-background)',
          surface: 'var(--color-surface)',
          text: 'var(--color-text)',
          muted: 'var(--color-muted)',
          border: 'var(--color-border)',
        },
      },
      fontFamily: {
        heading: 'var(--font-heading)',
        body: 'var(--font-body)',
      },
      borderRadius: {
        brand: 'var(--radius-brand)',
      },
    },
  },
  plugins: [],
};

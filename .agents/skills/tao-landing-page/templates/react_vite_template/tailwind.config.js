/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: 'var(--color-primary, #006964)',
          secondary: 'var(--color-secondary, #51BF9D)',
          accent: 'var(--color-accent, #E11D48)',
          background: 'var(--color-background, #0F172A)',
          surface: 'var(--color-surface, #1E293B)',
          text: 'var(--color-text, #F8FAFC)',
          muted: 'var(--color-muted, #94A3B8)',
        }
      },
      borderRadius: {
        'brand': 'var(--radius-brand, 1rem)',
      }
    },
  },
  plugins: [],
}

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          950: '#070a12',
          900: '#0b0f19',
          850: '#0f172a',
          800: '#111827',
          750: '#162032',
          700: '#1e293b',
          600: '#334155',
        },
        trade: {
          up: '#10b981',
          'up-bg': 'rgba(16, 185, 129, 0.12)',
          down: '#f43f5e',
          'down-bg': 'rgba(244, 63, 94, 0.12)',
          accent: '#38bdf8',
          subtle: '#94a3b8',
        }
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      }
    },
  },
  plugins: [],
}

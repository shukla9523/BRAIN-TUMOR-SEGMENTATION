/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        medical: {
          50: '#F0F9FF',
          100: '#E0F2FE',
          200: '#BAE6FD',
          300: '#7DD3FC',
          400: '#38BDF8',
          500: '#0EA5E9',
          600: '#0284C7',
          700: '#0369A1',
          800: '#075985',
          900: '#0C4A6E',
          navy: '#0F1E36',
          dark: '#0B132B',
          card: '#1C2541'
        },
        tumor: {
          wt: '#2563EB',    // Whole Tumor: Blue
          tc: '#DC2626',    // Tumor Core: Red
          et: '#F59E0B',    // Enhancing Tumor: Amber
          ed: '#10B981',    // Edema: Emerald
          ncr: '#8B5CF6'    // Necrotic / Non-enhancing: Violet
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
}

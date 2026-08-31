/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Ground: warm charcoal family (#1A1815) — not pure black, not cool grey
        ground: {
          950: '#12110F',
          900: '#1A1815', // Base ground
          850: '#22201C',
          800: '#2A2722',
        },
        // Surfaces: slightly lighter warm tone with crisp 1px borders
        surface: {
          base: '#22201C',
          card: '#2A2722',
          hover: '#33302A',
          active: '#3E3A33',
          elevated: '#484239',
        },
        // Borders: crisp hard edges (the comic panel language)
        border: {
          charcoal: '#332F28',
          crisp: '#484239',
          prominent: '#5E564A',
          panel: '#1A1815',
        },
        // The comic page: rendered on paper-cream floating on dark ground
        paper: {
          page: '#F6F3EB',
          cream: '#FAF7F0',
          warm: '#EFE9DC',
          border: '#D5CEBE',
          ink: '#1A1815',
          muted: '#686052',
        },
        // ONE accent only: Vermilion #EA5A2C (Editorial warm orange-red)
        vermilion: {
          500: '#EA5A2C',
          600: '#D44A1E',
          700: '#B83B13',
          muted: 'rgba(234, 90, 44, 0.12)',
          border: 'rgba(234, 90, 44, 0.45)',
        },
      },
      fontFamily: {
        display: ['Newsreader', 'Georgia', 'serif'],
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
        comic: ['Bangers', 'cursive', 'sans-serif'],
      },
      boxShadow: {
        page: '0 24px 48px -12px rgba(0, 0, 0, 0.75), 0 0 1px 1px rgba(0, 0, 0, 0.5)',
        crisp: '0 0 0 1px #332F28',
        'crisp-elevated': '0 0 0 1px #484239',
        'vermilion-glow': '0 0 20px -3px rgba(234, 90, 44, 0.35)',
      },
      transitionTimingFunction: {
        editorial: 'cubic-bezier(0.2, 0, 0, 1)',
      },
      transitionDuration: {
        fast: '200ms',
        panel: '400ms',
        crossfade: '600ms',
      },
    },
  },
  plugins: [],
}

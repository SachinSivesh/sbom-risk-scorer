/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        sg: {
          red: '#FF1338',
          black: '#000000',
          navy: '#0B1220',
          slate: '#1E293B',
          gray: '#CBD5E1',
          bg: '#F8FAFC',
          success: '#22C55E',
          warning: '#F59E0B',
          danger: '#EF4444',
        }
      },
      fontFamily: {
        sans: ['"Inter"', '"IBM Plex Sans"', 'system-ui', '-apple-system', 'sans-serif'],
      }
    },
  },
  plugins: [],
}

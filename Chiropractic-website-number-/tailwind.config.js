/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          green: '#22C55E',
          blue: '#3B82F6',
        },
        background: {
          light: '#F0F9FF',
          white: '#FFFFFF',
        },
        text: {
          dark: '#1F2937',
          gray: '#6B7280',
          light: '#9CA3AF',
        },
      },
      animation: {
        'float': 'float 3s ease-in-out infinite',
        'float-delayed': 'float 3s ease-in-out 0.5s infinite',
        'float-delayed-2': 'float 3s ease-in-out 1s infinite',
        'float-delayed-3': 'float 3s ease-in-out 1.5s infinite',
        'fade-in-up': 'fadeInUp 0.6s ease-out forwards',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-15px)' },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(30px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
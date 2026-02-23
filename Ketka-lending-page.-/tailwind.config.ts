import type { Config } from 'tailwindcss';

const config: Config = {
    content: [
        "./index.html",
        "./**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                paper: '#E8E4DD',
                signal: '#E63B2E',
                offwhite: '#F5F3EE',
                dark: '#111111',
                success: '#34C759', // Keep success for the LED indicator
            },
            fontFamily: {
                heading: ['Space Grotesk', 'sans-serif'],
                drama: ['DM Serif Display', 'serif'],
                mono: ['Space Mono', 'monospace'],
                sans: ['Inter', 'sans-serif'], // Keep Inter as fallback sans
            },
            animation: {
                'fade-in-up': 'fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards',
                'fade-in': 'fadeIn 1s ease-out forwards',
                'shimmer': 'shimmer 2.5s infinite',
                'float': 'float 6s ease-in-out infinite',
                'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'scale-in': 'scaleIn 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards',
            },
            keyframes: {
                fadeInUp: {
                    '0%': { opacity: '0', transform: 'translateY(20px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                scaleIn: {
                    '0%': { transform: 'scale(0.95)', opacity: '0' },
                    '100%': { transform: 'scale(1)', opacity: '1' },
                },
                shimmer: {
                    '0%': { transform: 'translateX(-100%)', opacity: '0' },
                    '50%': { opacity: '0.5' },
                    '100%': { transform: 'translateX(100%)', opacity: '0' },
                },
                float: {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-10px)' },
                }
            },
            backgroundImage: {
                'grid-pattern': "linear-gradient(to right, rgba(0,0,0,0.03) 1px, transparent 1px), linear-gradient(to bottom, rgba(0,0,0,0.03) 1px, transparent 1px)",
            }
        },
    },
    plugins: [],
};

export default config;

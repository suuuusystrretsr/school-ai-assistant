import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f2f8ff',
          100: '#daeefe',
          200: '#bcdfff',
          300: '#8ec6ff',
          400: '#5aa7ff',
          500: '#2e86ff',
          600: '#1369e4',
          700: '#0f53b4',
          800: '#124792',
          900: '#153d79'
        },
        ink: '#0c1524',
        surface: '#f7f9fc'
      },
      boxShadow: {
        float: '0 12px 32px rgba(18, 41, 84, 0.18)'
      },
      keyframes: {
        rise: {
          '0%': { opacity: '0', transform: 'translateY(14px)' },
          '100%': { opacity: '1', transform: 'translateY(0px)' }
        }
      },
      animation: {
        rise: 'rise 520ms ease-out both'
      }
    }
  },
  plugins: []
};

export default config;

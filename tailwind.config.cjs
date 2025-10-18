module.exports = {
  content: [
    './index.html',
    './src/**/*.{ts,tsx,js,jsx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui'],
      },
      colors: {
        alphaBlue: {
          500: '#3b82f6',
          600: '#2563eb'
        }
      }
    },
  },
  plugins: [],
}

/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    "./templates/**/*.html",
    "./static/js/**/*.js",
  ],
  presets: [
    require("franken-ui/shadcn-ui/preset-quick")
  ],
  theme: {
    extend: {
      colors: {
        'dark-bg': '#0a0a0a',
        'dark-sidebar': '#111111',
        'dark-card': '#1a1a1a',
        'dark-border': '#2a2a2a',
        'dark-hover': '#2a2a2a',
        'dark-text': '#e5e5e5',
        'dark-text-secondary': '#a0a0a0',
      }
    },
  },
  plugins: [],
}
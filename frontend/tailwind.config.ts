
/** @type {import('tailwindcss').Config} */
export default {
  // CRITICAL: Forces Tailwind to compile dark: variants when .dark class is on the ancestor wrapper div
  darkMode: 'class',
  
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'], 
      },
    },
  },
  plugins: [],
}

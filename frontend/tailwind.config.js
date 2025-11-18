/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        success: {
          light: '#d4edda',
          DEFAULT: '#28a745',
          dark: '#155724'
        },
        error: {
          light: '#f8d7da',
          DEFAULT: '#dc3545',
          dark: '#721c24'
        },
        info: {
          light: '#d1ecf1',
          DEFAULT: '#17a2b8',
          dark: '#0c5460'
        }
      }
    },
  },
  plugins: [],
}

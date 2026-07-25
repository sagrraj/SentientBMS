/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        darkbg: "#0B0F19",
        cardbg: "#151D30",
        borderbg: "#1F2E4D",
      }
    },
  },
  plugins: [],
}

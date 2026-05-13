/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0b0d17",
        electric: "#11cfe4",
        magenta: "#7a4cff",
      },
      fontFamily: {
        display: ["Sora", "system-ui", "sans-serif"],
        body: ["Space Grotesk", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
}

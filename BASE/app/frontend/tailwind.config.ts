import type { Config } from "tailwindcss";

const config: Config = {
  darkmode: ["class"],
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: "#16120E",
        accent: "#AC6E37",
        "accent-light": "#C98A4B",
        paper: "#F3F1EE",
      },
    },
  },
  plugins: [],
};
export default config;

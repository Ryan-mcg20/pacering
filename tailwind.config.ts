import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      colors: {
        background: "#000000",
        foreground: "#ffffff",
        card: {
          DEFAULT: "rgba(255, 255, 255, 0.15)",
          foreground: "#ffffff",
        },
        primary: {
          DEFAULT: "#ff1744",
          foreground: "#ffffff",
        },
        muted: {
          DEFAULT: "rgba(255, 255, 255, 0.1)",
          foreground: "rgba(255, 255, 255, 0.6)",
        },
        border: "rgba(255, 255, 255, 0.08)",
        ring: "#ff1744",
        accent: {
          ruby: "#9b111e",
          crimson: "#dc143c",
          neon: "#ff1744",
        },
      },
      borderRadius: {
        glass: "24px",
      },
      backdropBlur: {
        glass: "24px",
      },
    },
  },
  plugins: [],
};

export default config;

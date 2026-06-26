import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        rail: {
          track: "hsl(var(--rail-track))",
          btn: "hsl(var(--rail-btn))",
          "btn-hover": "hsl(var(--rail-btn-hover))",
          "btn-active": "hsl(var(--rail-btn-active))",
          "btn-active-hover": "hsl(var(--rail-btn-active-hover))",
          list: "hsl(var(--rail-list))",
          "list-hover": "hsl(var(--rail-list-hover))",
          "list-active": "hsl(var(--rail-list-active))",
          border: "hsl(var(--rail-border))",
          "border-active": "hsl(var(--rail-border-active))",
          "fg-muted": "hsl(var(--rail-fg-muted))",
          fg: "hsl(var(--rail-fg))",
          check: "hsl(var(--rail-check))",
          pick: "hsl(var(--rail-pick))",
          "pick-hover": "hsl(var(--rail-pick-hover))",
          "pick-active": "hsl(var(--rail-pick-active))",
          "pick-border": "hsl(var(--rail-pick-border))",
          "pick-border-active": "hsl(var(--rail-pick-border-active))",
          "pick-check": "hsl(var(--rail-pick-check))",
          history: "hsl(var(--rail-history))",
          "history-hover": "hsl(var(--rail-history-hover))",
          "history-active": "hsl(var(--rail-history-active))",
          "history-border": "hsl(var(--rail-history-border))",
          "history-border-active": "hsl(var(--rail-history-border-active))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;

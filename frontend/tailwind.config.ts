import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./src/**/*.{ts,tsx}"],
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
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // «Тетрадь исследователя»: палитра из котика-логотипа УИИ.
        paper: "#F6F7FB",
        grid: { DEFAULT: "#E2E7F1", soft: "#EDF0F7" },
        line: "#D3DAE8",
        field: "#C9D2E3",
        ink: "#22262E",
        fur: "#5F6673",
        scheme: { DEFAULT: "#1E5FD8", hover: "#174BAD", soft: "#F3F7FE", line: "#8FB0EC" },
        glow: "#3FDCFF",
        marker: { DEFAULT: "#FFC2C8", dot: "#F37C8A", line: "#F39AA4" },
        ok: "#1B7A46",
        danger: "#B42318",
      },
      fontFamily: {
        display: ['"Geologica Variable"', "Geologica", "system-ui", "sans-serif"],
        sans: ['"Golos Text"', "system-ui", "sans-serif"],
      },
      backgroundImage: {
        "grid-paper":
          "linear-gradient(#EDF0F7 1px, transparent 1px), linear-gradient(90deg, #EDF0F7 1px, transparent 1px)",
      },
      backgroundSize: {
        cell: "24px 24px",
        "cell-sm": "12px 12px",
      },
      keyframes: {
        "glow-pulse": {
          "0%, 100%": { opacity: "0.18", transform: "scale(0.92)" },
          "50%": { opacity: "0.36", transform: "scale(1.04)" },
        },
      },
      animation: {
        "glow-pulse": "glow-pulse 1.6s ease-in-out infinite",
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [],
};

export default config;

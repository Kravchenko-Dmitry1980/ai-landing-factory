import type { Metadata } from "next";
import "@fontsource-variable/geologica";
import "@fontsource/golos-text/400.css";
import "@fontsource/golos-text/500.css";
import "@fontsource/golos-text/600.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ленд — страницы проектов УИИ",
  description: "Собирает страницу проекта из презентации, текста или отчёта",
  icons: { icon: "/brand/cat-mark.webp" },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ru">
      <body className="min-h-screen bg-paper font-sans text-ink">{children}</body>
    </html>
  );
}

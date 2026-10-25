import Link from "next/link";
import type { ReactNode } from "react";
import { hasRole, type SessionUser } from "@/lib/platform";
import { SignOutButton } from "./SignOutButton";

export type AppSection = "library" | "studio" | "admin";
/** paper: the studio's light sheet; night: the library, in the colours of the night landing. */
export type HeaderTone = "paper" | "night";

const TONES: Record<HeaderTone, { bar: string; link: string; name: string }> = {
  paper: {
    bar: "border-grid bg-white",
    link: "text-ink hover:bg-paper aria-[current=page]:bg-scheme-soft aria-[current=page]:text-scheme",
    name: "text-fur",
  },
  night: {
    bar: "border-night-line bg-night-bg text-night-ink",
    link: "text-night-soft hover:bg-night-panel aria-[current=page]:bg-[#3FDCFF]/10 aria-[current=page]:text-night-ink",
    name: "text-night-muted",
  },
};

const SECTIONS: { key: AppSection; href: string; label: string; role: "viewer" | "editor" | "admin" }[] = [
  { key: "library", href: "/", label: "Библиотека", role: "viewer" },
  { key: "studio", href: "/studio", label: "Студия", role: "editor" },
  { key: "admin", href: "/admin", label: "Сотрудники", role: "admin" },
];

/**
 * Шапка интерфейса: котик-логотип УИИ, разделы, доступные учётной записи, и выход.
 * Без user — только логотип (страницы входа и ошибок).
 */
export function AppHeader({
  user,
  current,
  tone = "paper",
  children,
}: {
  user?: SessionUser | null;
  current?: AppSection;
  tone?: HeaderTone;
  children?: ReactNode;
}) {
  const sections = user ? SECTIONS.filter((s) => hasRole(user, s.role)) : [];
  const colors = TONES[tone];
  return (
    <header className={`border-b ${colors.bar}`}>
      {/* The library is wider than the studio sheet; the header lines up with each. */}
      <div
        className={`mx-auto flex flex-wrap items-center gap-x-6 gap-y-3 px-6 py-3 ${tone === "night" ? "max-w-[1240px]" : "max-w-[1200px]"}`}
      >
        <CatLogoLink night={tone === "night"} />
        {sections.length > 1 && (
          <nav aria-label="Разделы" className="flex flex-wrap gap-1">
            {sections.map((s) => (
              <Link
                key={s.key}
                href={s.href}
                aria-current={s.key === current ? "page" : undefined}
                className={`rounded-lg px-3 py-1.5 text-[15px] no-underline aria-[current=page]:font-semibold ${colors.link}`}
              >
                {s.label}
              </Link>
            ))}
          </nav>
        )}
        <div className="ml-auto flex flex-wrap items-center gap-4">
          {children}
          {user && (
            <div className="flex items-center gap-3 text-[15px]">
              <span className={`max-w-[220px] truncate ${colors.name}`} title={user.login}>
                {user.name}
              </span>
              <SignOutButton night={tone === "night"} />
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

export function CatLogoLink({
  compact = false,
  night = false,
  onClick,
}: {
  compact?: boolean;
  night?: boolean;
  onClick?: (e: React.MouseEvent<HTMLAnchorElement>) => void;
}) {
  const size = compact ? 36 : 44;
  return (
    <Link href="/" onClick={onClick} className={`flex items-center gap-2.5 no-underline ${night ? "text-night-ink" : "text-ink"}`}>
      {/* eslint-disable-next-line @next/next/no-img-element -- статичный логотип, оптимизирован заранее */}
      <img src="/brand/cat-mark.webp" alt="" width={size} height={size} />
      <span className={`font-display font-semibold ${compact ? "text-[19px]" : "text-[22px]"}`}>
        Ленд
      </span>
    </Link>
  );
}

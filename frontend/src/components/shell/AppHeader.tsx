import Link from "next/link";
import type { ReactNode } from "react";
import { hasRole, type SessionUser } from "@/lib/platform";
import { SignOutButton } from "./SignOutButton";

export type AppSection = "library" | "studio" | "admin";

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
  children,
}: {
  user?: SessionUser | null;
  current?: AppSection;
  children?: ReactNode;
}) {
  const sections = user ? SECTIONS.filter((s) => hasRole(user, s.role)) : [];
  return (
    <header className="border-b border-grid bg-white">
      <div className="mx-auto flex max-w-[1200px] flex-wrap items-center gap-x-6 gap-y-3 px-6 py-3">
        <CatLogoLink />
        {sections.length > 1 && (
          <nav aria-label="Разделы" className="flex flex-wrap gap-1">
            {sections.map((s) => (
              <Link
                key={s.key}
                href={s.href}
                aria-current={s.key === current ? "page" : undefined}
                className="rounded-lg px-3 py-1.5 text-[15px] text-ink no-underline hover:bg-paper aria-[current=page]:bg-scheme-soft aria-[current=page]:font-semibold aria-[current=page]:text-scheme"
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
              <span className="max-w-[220px] truncate text-fur" title={user.login}>
                {user.name}
              </span>
              <SignOutButton />
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

export function CatLogoLink({
  compact = false,
  onClick,
}: {
  compact?: boolean;
  onClick?: (e: React.MouseEvent<HTMLAnchorElement>) => void;
}) {
  const size = compact ? 36 : 44;
  return (
    <Link href="/" onClick={onClick} className="flex items-center gap-2.5 text-ink no-underline">
      {/* eslint-disable-next-line @next/next/no-img-element -- статичный логотип, оптимизирован заранее */}
      <img src="/brand/cat-mark.webp" alt="" width={size} height={size} />
      <span className={`font-display font-semibold ${compact ? "text-[19px]" : "text-[22px]"}`}>
        Ленд
      </span>
    </Link>
  );
}

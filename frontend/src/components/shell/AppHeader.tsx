import Link from "next/link";
import type { ReactNode } from "react";

/** Шапка интерфейса сотрудника: котик-логотип УИИ и название, справа — действия экрана. */
export function AppHeader({ children }: { children?: ReactNode }) {
  return (
    <header className="border-b border-grid bg-white">
      <div className="mx-auto flex max-w-[1200px] flex-wrap items-center justify-between gap-4 px-6 py-3">
        <CatLogoLink />
        {children}
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

import type { ReactNode } from "react";
import { CatLogoLink } from "@/components/shell/AppHeader";

/** Страницы без учётной записи (вход, приглашение): лист в клетку с котиком. */
export function AccountShell({ title, lead, children }: { title: string; lead?: ReactNode; children: ReactNode }) {
  return (
    <div className="min-h-screen bg-paper bg-grid-paper bg-cell">
      <main className="mx-auto flex min-h-screen max-w-[460px] flex-col justify-center gap-8 px-6 py-12">
        <CatLogoLink />
        <div className="flex flex-col gap-6 rounded-[18px] border border-line bg-white p-7 shadow-[0_1px_0_#E2E7F1]">
          <div className="flex flex-col gap-2">
            <h1 className="font-display text-[28px] font-semibold leading-tight">{title}</h1>
            {lead && <p className="text-[15px] leading-relaxed text-fur">{lead}</p>}
          </div>
          {children}
        </div>
      </main>
    </div>
  );
}

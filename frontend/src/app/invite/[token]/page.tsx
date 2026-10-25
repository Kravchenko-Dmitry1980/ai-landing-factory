import type { Metadata } from "next";
import Link from "next/link";
import { AcceptInviteForm } from "@/components/account/AcceptInviteForm";
import { AccountShell } from "@/components/account/AccountShell";
import { ROLE_HINTS, ROLE_LABELS, type InviteInfo } from "@/lib/platform";
import { backendFetch } from "@/lib/session.server";

export const metadata: Metadata = { title: "Приглашение — Ленд" };

async function loadInvite(token: string): Promise<{ invite: InviteInfo } | { message: string }> {
  let res: Response;
  try {
    res = await backendFetch(`/auth/invites/${encodeURIComponent(token)}`, { signal: AbortSignal.timeout(10_000) });
  } catch (err) {
    console.error("Invite page: backend unreachable", err);
    return { message: "Сервер сейчас не отвечает. Откройте ссылку ещё раз через несколько минут." };
  }
  if (res.ok) return { invite: (await res.json()) as InviteInfo };
  if (res.status === 404) {
    const body = (await res.json().catch(() => null)) as { detail?: string } | null;
    return { message: body?.detail ?? "Ссылка не работает. Попросите у администратора новую." };
  }
  console.error("Invite page: backend answered", res.status);
  return { message: "Не удалось проверить ссылку. Попробуйте ещё раз через несколько минут." };
}

export default async function InvitePage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  const loaded = await loadInvite(token);

  if ("message" in loaded) {
    return (
      <AccountShell title="Ссылка не работает" lead={loaded.message}>
        <Link href="/login" className="text-[15px] text-scheme">
          Перейти ко входу
        </Link>
      </AccountShell>
    );
  }

  const { invite } = loaded;
  if (invite.kind === "reset") {
    return (
      <AccountShell title="Новый пароль" lead={`Для учётной записи ${invite.user_name ?? ""}. Старый пароль перестанет работать, а вход на других устройствах закончится.`}>
        <AcceptInviteForm token={token} invite={invite} />
      </AccountShell>
    );
  }
  const from = invite.created_by_name ? `${invite.created_by_name} приглашает вас в Ленд` : "Вас приглашают в Ленд";
  return (
    <AccountShell
      title="Учётная запись в Ленде"
      lead={`${from}. Роль: ${ROLE_LABELS[invite.role].toLowerCase()} — ${ROLE_HINTS[invite.role]}.`}
    >
      <AcceptInviteForm token={token} invite={invite} />
    </AccountShell>
  );
}

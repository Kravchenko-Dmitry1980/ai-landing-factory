import type { Metadata } from "next";
import { AdminView } from "@/components/admin/AdminView";
import { AppHeader } from "@/components/shell/AppHeader";
import type { InviteInfo, SessionUser } from "@/lib/platform";
import { backendFetch, requireUser } from "@/lib/session.server";

export const metadata: Metadata = { title: "Сотрудники — Ленд" };

async function loadJson<T>(path: string): Promise<T> {
  const res = await backendFetch(path, { signal: AbortSignal.timeout(10_000) });
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return (await res.json()) as T;
}

export default async function AdminPage() {
  const me = await requireUser("/admin", "admin");
  let users: SessionUser[] | null = null;
  let invites: InviteInfo[] | null = null;
  try {
    [users, invites] = await Promise.all([loadJson<SessionUser[]>("/admin/users"), loadJson<InviteInfo[]>("/admin/invites")]);
  } catch (err) {
    console.error("Admin page: backend request failed", err);
  }
  return (
    <>
      <AppHeader user={me} current="admin" />
      <AdminView me={me} initialUsers={users} initialInvites={invites} />
    </>
  );
}

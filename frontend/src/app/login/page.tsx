import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { LoginForm } from "@/components/account/LoginForm";
import { AccountShell } from "@/components/account/AccountShell";
import { safeNextPath } from "@/lib/platform";
import { getSessionUser } from "@/lib/session.server";

export const metadata: Metadata = { title: "Вход — Ленд" };

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const next = safeNextPath((await searchParams).next);
  let signedIn = false;
  try {
    signedIn = (await getSessionUser()) !== null;
  } catch (err) {
    // The form still works once the server is back; the sign-in request will say what is wrong.
    console.error("Login page: session check failed", err);
  }
  if (signedIn) redirect(next);

  return (
    <AccountShell title="Вход в Ленд" lead="Библиотека лендингов УИИ открыта только сотрудникам. Учётную запись выдаёт администратор по ссылке-приглашению.">
      <LoginForm next={next} />
    </AccountShell>
  );
}

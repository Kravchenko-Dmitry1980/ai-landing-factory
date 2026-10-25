"use client";

import { useId, useRef, useState } from "react";
import { PRIMARY_BUTTON } from "@/components/account/fields";
import {
  createInvite,
  createResetLink,
  formatDate,
  listInvites,
  listUsers,
  platformErrorMessage,
  revokeInvite,
  ROLE_HINTS,
  ROLE_LABELS,
  updateUser,
  type InviteCreated,
  type InviteInfo,
  type Role,
  type SessionUser,
} from "@/lib/platform";

const ROLES: Role[] = ["editor", "viewer", "admin"];
const SECONDARY_BUTTON = "rounded-lg border border-field bg-white px-3 py-1.5 text-[15px] hover:bg-paper disabled:opacity-60";

function fullLink(path: string): string {
  return `${window.location.origin}${path}`;
}

/** Ссылка, показанная один раз: поле только для чтения и кнопка «Скопировать». */
function LinkBox({ created, children }: { created: InviteCreated; children: React.ReactNode }) {
  const input = useRef<HTMLInputElement>(null);
  const [copied, setCopied] = useState<"yes" | "no" | null>(null);
  const link = fullLink(created.path);

  async function copy() {
    try {
      await navigator.clipboard.writeText(link);
      setCopied("yes");
    } catch {
      // Over plain http the clipboard API is off: select the text so Ctrl+C works.
      input.current?.select();
      setCopied("no");
    }
  }

  return (
    <div className="flex flex-col gap-2 rounded-xl border border-scheme-line bg-scheme-soft p-4">
      <p className="text-[15px]">{children}</p>
      <div className="flex flex-wrap gap-2">
        <input
          ref={input}
          readOnly
          value={link}
          aria-label="Ссылка"
          onFocus={(e) => e.currentTarget.select()}
          className="h-10 min-w-0 flex-[1_1_320px] rounded-[10px] border border-field bg-white px-3 font-mono text-sm"
        />
        <button type="button" onClick={() => void copy()} className={SECONDARY_BUTTON}>
          Скопировать
        </button>
      </div>
      {copied === "yes" && <p className="text-sm text-ok">Ссылка скопирована.</p>}
      {copied === "no" && <p className="text-sm text-fur">Ссылка выделена: нажмите Ctrl+C, чтобы скопировать.</p>}
      <p className="text-sm text-fur">
        Действует до {formatDate(created.invite.expires_at)} и срабатывает один раз. Ссылку видно только сейчас: сохраните
        или отправьте её сразу.
      </p>
    </div>
  );
}

function InvitePanel({ onCreated }: { onCreated: () => void }) {
  const noteId = useId();
  const [role, setRole] = useState<Role>("editor");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState<InviteCreated | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      setCreated(await createInvite(role, note.trim()));
      setNote("");
      onCreated();
    } catch (err) {
      console.error("Invite creation failed", err);
      setError(platformErrorMessage(err, "Не удалось создать приглашение"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section aria-labelledby="invite-title" className="flex flex-col gap-5">
      <div className="flex flex-col gap-1.5">
        <h2 id="invite-title" className="font-display text-[26px] font-semibold">
          Пригласить сотрудника
        </h2>
        <p className="max-w-[640px] text-[15px] text-fur">
          Ленд выдаст ссылку. Сотрудник откроет её, сам придумает логин и пароль и сразу войдёт.
        </p>
      </div>
      <form onSubmit={(e) => void submit(e)} className="flex max-w-[760px] flex-col gap-4">
        <fieldset className="flex flex-col gap-2">
          <legend className="mb-1 text-[15px] font-semibold">Что сотрудник сможет делать</legend>
          <div className="grid gap-2 sm:grid-cols-3">
            {ROLES.map((r) => (
              <label
                key={r}
                className="flex cursor-pointer flex-col gap-1 rounded-xl border border-line bg-white p-3 has-[:checked]:border-scheme has-[:checked]:bg-scheme-soft"
              >
                <span className="flex items-center gap-2 text-[15px] font-semibold">
                  <input type="radio" name="role" value={r} checked={role === r} onChange={() => setRole(r)} />
                  {ROLE_LABELS[r]}
                </span>
                <span className="text-sm text-fur">{ROLE_HINTS[r]}</span>
              </label>
            ))}
          </div>
        </fieldset>
        <div className="flex flex-col gap-1.5">
          <label htmlFor={noteId} className="text-[15px] font-semibold">
            Для кого ссылка
          </label>
          <input
            id={noteId}
            value={note}
            maxLength={200}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Например: Мария, отдел кадров"
            className="h-11 rounded-[10px] border border-field bg-white px-3 text-base"
          />
          <p className="text-sm text-fur">Видно только администраторам, чтобы не перепутать ссылки</p>
        </div>
        {error && (
          <p role="alert" className="rounded-[10px] bg-marker px-4 py-3 text-[15px]">
            {error}
          </p>
        )}
        <div>
          <button type="submit" disabled={busy} className={PRIMARY_BUTTON}>
            {busy ? "Создаю…" : "Создать ссылку-приглашение"}
          </button>
        </div>
      </form>
      {created && (
        <LinkBox created={created}>
          Приглашение для роли «{ROLE_LABELS[created.invite.role]}»{created.invite.note ? ` (${created.invite.note})` : ""}.
        </LinkBox>
      )}
    </section>
  );
}

function OpenInvites({ invites, onChange }: { invites: InviteInfo[]; onChange: () => void }) {
  const [error, setError] = useState<string | null>(null);
  if (invites.length === 0) return null;

  async function revoke(invite: InviteInfo) {
    setError(null);
    try {
      await revokeInvite(invite.id);
    } catch (err) {
      console.error("Invite revoke failed", err);
      setError(platformErrorMessage(err, "Не удалось отозвать ссылку"));
    }
    onChange();
  }

  return (
    <section aria-labelledby="open-invites-title" className="flex flex-col gap-3">
      <h2 id="open-invites-title" className="font-display text-[22px] font-semibold">
        Ссылки ждут ответа
      </h2>
      {error && (
        <p role="alert" className="text-[15px] text-danger">
          {error}
        </p>
      )}
      <ul className="flex flex-col divide-y divide-grid rounded-xl border border-line bg-white">
        {invites.map((invite) => (
          <li key={invite.id} className="flex flex-wrap items-center gap-x-5 gap-y-1 px-4 py-3 text-[15px]">
            <span className="min-w-0 flex-[1_1_220px] font-semibold">
              {invite.kind === "reset"
                ? `Новый пароль: ${invite.user_name ?? "сотрудник"}`
                : invite.note || `Новый сотрудник, ${ROLE_LABELS[invite.role].toLowerCase()}`}
            </span>
            <span className="text-fur">
              {invite.kind === "account" && invite.note ? `${ROLE_LABELS[invite.role]}, ` : ""}до {formatDate(invite.expires_at)}
            </span>
            <button type="button" onClick={() => void revoke(invite)} className={SECONDARY_BUTTON}>
              Отозвать
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}

function UserRow({
  user,
  isMe,
  onSaved,
  onLinks,
}: {
  user: SessionUser;
  isMe: boolean;
  onSaved: (user: SessionUser) => void;
  onLinks: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reset, setReset] = useState<InviteCreated | null>(null);

  async function change(patch: { role?: Role; is_active?: boolean }) {
    setBusy(true);
    setError(null);
    try {
      onSaved(await updateUser(user.id, patch));
    } catch (err) {
      console.error("User update failed", user.id, err);
      setError(platformErrorMessage(err, "Не удалось изменить учётную запись"));
    } finally {
      setBusy(false);
    }
  }

  async function makeResetLink() {
    setBusy(true);
    setError(null);
    try {
      setReset(await createResetLink(user.id));
      onLinks();
    } catch (err) {
      console.error("Reset link failed", user.id, err);
      setError(platformErrorMessage(err, "Не удалось создать ссылку"));
    } finally {
      setBusy(false);
    }
  }

  function toggleActive() {
    if (user.is_active && !window.confirm(`Отключить учётную запись «${user.name}»? Вход перестанет работать сразу.`)) return;
    void change({ is_active: !user.is_active });
  }

  return (
    <li className={`flex flex-col gap-3 px-4 py-4 ${user.is_active ? "" : "bg-paper"}`}>
      <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
        <div className="flex min-w-0 flex-[1_1_220px] flex-col">
          <span className={`truncate text-[16px] font-semibold ${user.is_active ? "" : "text-fur line-through"}`}>
            {user.name}
            {isMe && <span className="ml-2 text-sm font-normal text-fur">это вы</span>}
          </span>
          <span className="truncate text-sm text-fur">
            {user.login}
            {", "}
            {user.last_login_at ? `последний вход ${formatDate(user.last_login_at)}` : "входа ещё не было"}
          </span>
        </div>
        <label className="flex items-center gap-2 text-[15px]">
          <span className="sr-only">Роль: {user.name}</span>
          <select
            value={user.role}
            disabled={isMe || busy || !user.is_active}
            onChange={(e) => void change({ role: e.target.value as Role })}
            className="h-10 rounded-[10px] border border-field bg-white px-2 text-[15px] disabled:opacity-60"
          >
            {ROLES.map((r) => (
              <option key={r} value={r}>
                {ROLE_LABELS[r]}
              </option>
            ))}
          </select>
        </label>
        {!isMe && (
          <div className="flex flex-wrap gap-2">
            {user.is_active && (
              <button type="button" disabled={busy} onClick={() => void makeResetLink()} className={SECONDARY_BUTTON}>
                Ссылка для нового пароля
              </button>
            )}
            <button type="button" disabled={busy} onClick={toggleActive} className={SECONDARY_BUTTON}>
              {user.is_active ? "Отключить" : "Включить"}
            </button>
          </div>
        )}
      </div>
      {error && (
        <p role="alert" className="text-[15px] text-danger">
          {error}
        </p>
      )}
      {reset && <LinkBox created={reset}>Ссылка для нового пароля «{user.name}». Старый пароль перестанет работать, когда сотрудник задаст новый.</LinkBox>}
    </li>
  );
}

export function AdminView({
  me,
  initialUsers,
  initialInvites,
}: {
  me: SessionUser;
  initialUsers: SessionUser[] | null;
  initialInvites: InviteInfo[] | null;
}) {
  const [users, setUsers] = useState(initialUsers);
  const [invites, setInvites] = useState(initialInvites ?? []);
  const [error, setError] = useState<string | null>(
    initialUsers === null ? "Не удалось загрузить список сотрудников. Обновите страницу через минуту." : null,
  );

  async function reload() {
    try {
      const [u, i] = await Promise.all([listUsers(), listInvites()]);
      setUsers(u);
      setInvites(i);
      setError(null);
    } catch (err) {
      console.error("Admin lists failed to load", err);
      setError(platformErrorMessage(err, "Не удалось обновить списки"));
    }
  }

  return (
    <main className="mx-auto flex max-w-[1200px] flex-col gap-12 px-6 pb-20 pt-10">
      <h1 className="font-display text-[40px] font-semibold leading-tight">Сотрудники</h1>
      <InvitePanel onCreated={() => void reload()} />
      <OpenInvites invites={invites} onChange={() => void reload()} />
      <section aria-labelledby="users-title" className="flex flex-col gap-3">
        <h2 id="users-title" className="font-display text-[26px] font-semibold">
          Учётные записи
        </h2>
        {error && (
          <div role="alert" className="flex flex-wrap items-center gap-3 rounded-xl border border-line bg-white px-5 py-4 text-[15px]">
            <span>{error}</span>
            <button type="button" onClick={() => void reload()} className={SECONDARY_BUTTON}>
              Повторить
            </button>
          </div>
        )}
        {users && (
          <ul className="flex flex-col divide-y divide-grid rounded-xl border border-line bg-white">
            {users.map((user) => (
              <UserRow
                key={user.id}
                user={user}
                isMe={user.id === me.id}
                onSaved={(saved) => setUsers((prev) => prev?.map((u) => (u.id === saved.id ? saved : u)) ?? prev)}
                onLinks={() => void reload()}
              />
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}

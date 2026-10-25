"use client";

import { useState, type FormEvent } from "react";
import { acceptInvite, platformErrorMessage, type InviteInfo } from "@/lib/platform";
import { slugifyRu } from "@/lib/staff";
import { Field, FormError, PRIMARY_BUTTON } from "./fields";

const PASSWORD_MIN = 8;

/** "Мария Соколова" → "mariya.sokolova": a login suggestion until the person types their own. */
export function suggestLogin(name: string): string {
  const slug = slugifyRu(name, 64).replace(/-/g, ".");
  return slug === "landing" ? "" : slug;
}

export function AcceptInviteForm({ token, invite }: { token: string; invite: InviteInfo }) {
  const isReset = invite.kind === "reset";
  const [name, setName] = useState("");
  const [login, setLogin] = useState("");
  const [loginTouched, setLoginTouched] = useState(false);
  const [password, setPassword] = useState("");
  const [repeat, setRepeat] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const shownLogin = loginTouched ? login : suggestLogin(name);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (busy) return;
    if (password.length < PASSWORD_MIN) return setError(`Пароль должен быть не короче ${PASSWORD_MIN} символов.`);
    if (password !== repeat) return setError("Пароли не совпадают. Введите один и тот же пароль дважды.");
    setBusy(true);
    setError(null);
    try {
      const user = await acceptInvite(token, isReset ? { password } : { name, login: shownLogin, password });
      window.location.assign(user.role === "viewer" ? "/" : "/studio");
    } catch (err) {
      console.error("Invite acceptance failed", err);
      setError(platformErrorMessage(err, isReset ? "Не удалось сменить пароль" : "Не удалось создать учётную запись"));
      setBusy(false);
    }
  }

  return (
    <form onSubmit={(e) => void submit(e)} className="flex flex-col gap-5" noValidate>
      {!isReset && (
        <>
          <Field
            label="Имя и фамилия"
            hint="Так вас увидят коллеги в библиотеке"
            autoComplete="name"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <Field
            label="Логин"
            hint="Латинские буквы, цифры и точка. По нему вы будете входить"
            autoComplete="username"
            autoCapitalize="none"
            spellCheck={false}
            required
            value={shownLogin}
            onChange={(e) => {
              setLoginTouched(true);
              setLogin(e.target.value);
            }}
          />
        </>
      )}
      <Field
        label={isReset ? "Новый пароль" : "Пароль"}
        hint={`Не короче ${PASSWORD_MIN} символов`}
        type="password"
        autoComplete="new-password"
        required
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <Field
        label="Пароль ещё раз"
        type="password"
        autoComplete="new-password"
        required
        value={repeat}
        onChange={(e) => setRepeat(e.target.value)}
      />
      <FormError message={error} />
      <button type="submit" disabled={busy} className={PRIMARY_BUTTON}>
        {busy ? "Сохраняю…" : isReset ? "Сохранить пароль и войти" : "Создать учётную запись"}
      </button>
    </form>
  );
}

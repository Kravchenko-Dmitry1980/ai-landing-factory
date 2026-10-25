"use client";

import { useState, type FormEvent } from "react";
import { platformErrorMessage, signIn } from "@/lib/platform";
import { Field, FormError, PRIMARY_BUTTON } from "./fields";

export function LoginForm({ next }: { next: string }) {
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      await signIn(login, password);
    } catch (err) {
      console.error("Sign-in failed", err);
      setError(platformErrorMessage(err, "Не удалось войти"));
      setBusy(false);
      return;
    }
    // A full load, so every server-rendered page sees the new session cookie.
    window.location.assign(next);
  }

  return (
    <form onSubmit={(e) => void submit(e)} className="flex flex-col gap-5" noValidate>
      <Field
        label="Логин"
        name="username"
        autoComplete="username"
        autoCapitalize="none"
        spellCheck={false}
        required
        value={login}
        onChange={(e) => setLogin(e.target.value)}
      />
      <Field
        label="Пароль"
        name="password"
        type="password"
        autoComplete="current-password"
        required
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <FormError message={error} />
      <button type="submit" disabled={busy || !login.trim() || !password} className={PRIMARY_BUTTON}>
        {busy ? "Вхожу…" : "Войти"}
      </button>
      <p className="text-sm leading-relaxed text-fur">Забыли пароль? Администратор пришлёт ссылку, по которой можно задать новый.</p>
    </form>
  );
}

"use client";

import { useState } from "react";
import { platformErrorMessage, signOut } from "@/lib/platform";

export function SignOutButton() {
  const [busy, setBusy] = useState(false);

  async function leave() {
    setBusy(true);
    try {
      await signOut();
    } catch (err) {
      console.error("Sign-out failed", err);
      setBusy(false);
      window.alert(platformErrorMessage(err, "Не удалось выйти"));
      return;
    }
    // A full load: every server-rendered page must forget the account.
    window.location.assign("/login");
  }

  return (
    <button
      type="button"
      onClick={() => void leave()}
      disabled={busy}
      className="rounded-lg border border-field px-3 py-1.5 text-[15px] hover:bg-paper disabled:opacity-60"
    >
      {busy ? "Выхожу…" : "Выйти"}
    </button>
  );
}

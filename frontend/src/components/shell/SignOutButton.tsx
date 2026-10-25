"use client";

import { useState } from "react";
import { platformErrorMessage, signOut } from "@/lib/platform";

export function SignOutButton({ night = false }: { night?: boolean }) {
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
      className={`rounded-lg border px-3 py-1.5 text-[15px] disabled:opacity-60 ${
        night ? "border-night-rim text-night-ink hover:border-[#3FDCFF]" : "border-field hover:bg-paper"
      }`}
    >
      {busy ? "Выхожу…" : "Выйти"}
    </button>
  );
}

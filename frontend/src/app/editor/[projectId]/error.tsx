"use client";

import Link from "next/link";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";

export default function EditorRouteError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Editor route failed", error);
  }, [error]);

  return (
    <section className="mx-auto max-w-2xl space-y-4 rounded-lg border p-6">
      <h1 className="text-2xl font-bold">Не удалось открыть проект</h1>
      <p className="text-sm text-muted-foreground">
        Ошибка на маршруте редактора. Проверьте backend и попробуйте повторить.
      </p>
      {error.digest && (
        <p className="text-xs text-muted-foreground">
          diagnostic digest: <code>{error.digest}</code>
        </p>
      )}
      <div className="flex flex-wrap gap-2">
        <Button type="button" onClick={() => reset()}>
          Повторить
        </Button>
        <Link href="/">
          <Button variant="outline" type="button">
            Вернуться к списку
          </Button>
        </Link>
      </div>
    </section>
  );
}

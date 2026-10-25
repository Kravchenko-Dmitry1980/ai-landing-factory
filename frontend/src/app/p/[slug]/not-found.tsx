import Link from "next/link";
import { AppHeader } from "@/components/shell/AppHeader";

export default function PublishedPageNotFound() {
  return (
    <>
      <AppHeader />
      <main className="mx-auto flex max-w-[720px] flex-col gap-4 px-6 py-16">
        <h1 className="font-display text-3xl font-semibold">Такого лендинга в библиотеке нет</h1>
        <p className="text-[17px] text-fur">Его сняли с публикации, или в ссылке ошибка. Найдите проект в библиотеке по названию.</p>
        <div>
          <Link
            href="/"
            className="inline-flex h-11 items-center rounded-[10px] border border-field bg-white px-5 text-[15px] text-ink no-underline hover:bg-paper"
          >
            Открыть библиотеку
          </Link>
        </div>
      </main>
    </>
  );
}

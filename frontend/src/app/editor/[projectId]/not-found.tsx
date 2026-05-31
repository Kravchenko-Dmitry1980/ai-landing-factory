import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function EditorProjectNotFound() {
  return (
    <section className="mx-auto max-w-2xl space-y-4 rounded-lg border p-6">
      <h1 className="text-2xl font-bold">Проект не найден</h1>
      <p className="text-sm text-muted-foreground">
        Указанный project_id отсутствует или был удален.
      </p>
      <Link href="/">
        <Button variant="outline" type="button">
          Вернуться к списку
        </Button>
      </Link>
    </section>
  );
}

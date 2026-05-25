"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { createProject, formatApiError, uploadMaterials } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export function UploadForm() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [files, setFiles] = useState<FileList | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!name.trim()) {
      setError("Укажите название проекта");
      return;
    }
    if (!files?.length) {
      setError("Выберите хотя бы один файл");
      return;
    }

    setLoading(true);
    try {
      const project = await createProject(name.trim(), description.trim() || undefined);
      await uploadMaterials(project.id, Array.from(files), description.trim() || undefined);
      router.push(`/editor/${project.id}`);
    } catch (err) {
      setError(formatApiError(err, "Ошибка загрузки"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Материалы проекта</CardTitle>
        <p className="text-sm text-muted-foreground">
          PDF, DOCX, PPTX, изображения, скриншоты или текст. После загрузки создаётся
          черновой LandingContract.
        </p>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="name">Название проекта</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Например: Платформа аналитики"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="description">Текстовое описание (опционально)</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Краткий бриф или вводные..."
              rows={4}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="files">Файлы</Label>
            <Input
              id="files"
              type="file"
              multiple
              accept=".pdf,.docx,.pptx,.png,.jpg,.jpeg,.webp,.txt,.md"
              onChange={(e) => setFiles(e.target.files)}
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <Button type="submit" disabled={loading}>
            {loading ? "Обработка…" : "Загрузить и создать ленд"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

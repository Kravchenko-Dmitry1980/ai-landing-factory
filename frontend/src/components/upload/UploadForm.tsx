"use client";

import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { createProject, formatApiError, uploadMaterials } from "@/lib/api";
import { rememberLastProject } from "@/lib/lastProject";
import {
  mergeFileSelection,
  removeFileAt,
  validateUploadSubmit,
} from "@/lib/uploadFormUtils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export function UploadForm() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleFilesChange(e: React.ChangeEvent<HTMLInputElement>) {
    setFiles((prev) => mergeFileSelection(prev, e.target.files));
    e.target.value = "";
  }

  function handleRemoveFile(index: number) {
    setFiles((prev) => removeFileAt(prev, index));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const validationError = validateUploadSubmit(name, files);
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    try {
      const project = await createProject(name.trim(), description.trim() || undefined);
      await uploadMaterials(project.id, files, description.trim() || undefined);
      rememberLastProject(project.id);
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
          Загрузите все материалы одного проекта: презентацию, лендинг DOCX, команду TXT и
          отчёт PDF. После загрузки создаётся черновой LandingContract из всех источников.
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
              ref={fileInputRef}
              id="files"
              type="file"
              multiple
              accept=".pdf,.docx,.pptx,.png,.jpg,.jpeg,.webp,.txt,.md"
              onChange={handleFilesChange}
            />
            <p className="text-xs text-muted-foreground">
              Можно выбрать несколько файлов за раз или добавить партиями. Для полной команды
              загрузите DOCX/TXT с разделом «Команда проекта», а не только презентацию.
            </p>
            {files.length > 0 && (
              <div className="rounded-md border border-border bg-muted/30 p-3 text-sm">
                <p className="font-medium">Выбрано файлов: {files.length}</p>
                <ul className="mt-2 space-y-1">
                  {files.map((file, index) => (
                    <li
                      key={`${file.name}-${file.size}-${file.lastModified}`}
                      className="flex items-center justify-between gap-2"
                    >
                      <span className="truncate">{file.name}</span>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="h-7 shrink-0 px-2 text-xs"
                        onClick={() => handleRemoveFile(index)}
                        disabled={loading}
                      >
                        Удалить
                      </Button>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <Button type="submit" disabled={loading || files.length === 0}>
            {loading ? "Обработка…" : "Загрузить и создать ленд"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

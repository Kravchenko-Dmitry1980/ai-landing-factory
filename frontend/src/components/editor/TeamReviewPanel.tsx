"use client";

import { useCallback, useEffect, useState } from "react";
import {
  getTeamReview,
  teamReviewBulkAction,
  teamReviewManualText,
} from "@/lib/api";
import type { TeamReviewData } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";

interface Props {
  projectId: string;
  onUpdated?: () => void;
  advancedDiagnostics?: boolean;
}

const SIMPLE_TEAM_WARNING =
  "Команда не найдена или требует проверки. Добавьте её вручную в редакторе.";
const SIMPLE_REVIEW_WARNING =
  "Список команды требует проверки. Отредактируйте участников вручную при необходимости.";

interface ViewProps {
  data: TeamReviewData;
  editing: boolean;
  editText: string;
  acting: boolean;
  error: string | null;
  advancedDiagnostics: boolean;
  onEditTextChange: (text: string) => void;
  onStartEdit: () => void;
  onCancelEdit: () => void;
  onSaveManual: () => void;
  onAction: (action: "accept_all" | "keep_verified_only" | "reset_to_auto") => void;
}

function resolveTeamWarning(
  data: TeamReviewData,
  advancedDiagnostics: boolean,
): string | null {
  if (data.summary.warning) {
    if (advancedDiagnostics) {
      return data.summary.warning;
    }
    const low = data.summary.warning.toLowerCase();
    if (low.includes("ocr") || low.includes("paddle") || low.includes("tesseract")) {
      return SIMPLE_REVIEW_WARNING;
    }
    return data.summary.warning;
  }
  if (data.summary.needs_review_count > 0 || data.summary.probable_count > 0) {
    return advancedDiagnostics
      ? "Команда извлечена из изображения через OCR. Возможны ошибки в ФИО."
      : SIMPLE_REVIEW_WARNING;
  }
  if (data.summary.total_candidates === 0) {
    return SIMPLE_TEAM_WARNING;
  }
  return null;
}

export function TeamReviewPanelView({
  data,
  editing,
  editText,
  acting,
  error,
  advancedDiagnostics,
  onEditTextChange,
  onStartEdit,
  onCancelEdit,
  onSaveManual,
  onAction,
}: ViewProps) {
  const { summary } = data;
  const teamWarning = resolveTeamWarning(data, advancedDiagnostics);
  const showReviewActions =
    advancedDiagnostics &&
    (summary.needs_review_count > 0 || summary.probable_count > 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Команда проекта</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <p>
          Найдено участников: {summary.total_candidates}
          {summary.verified_count > 0 && (
            <> · Уверенно: {summary.verified_count}</>
          )}
          {summary.needs_review_count > 0 && (
            <> · Требуют проверки: {summary.needs_review_count}</>
          )}
        </p>

        {teamWarning && (
          <p className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-amber-900">
            {teamWarning}
          </p>
        )}

        {editing ? (
          <div className="space-y-2">
            <Textarea
              value={editText}
              onChange={(e) => onEditTextChange(e.target.value)}
              rows={12}
              className="font-mono text-xs"
            />
            <div className="flex flex-wrap gap-2">
              <Button type="button" size="sm" disabled={acting} onClick={onSaveManual}>
                Сохранить команду
              </Button>
              <Button
                type="button"
                size="sm"
                variant="outline"
                disabled={acting}
                onClick={onCancelEdit}
              >
                Отмена
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex flex-wrap gap-2">
            {showReviewActions && (
              <>
                <Button
                  type="button"
                  size="sm"
                  disabled={acting}
                  onClick={() => onAction("accept_all")}
                >
                  Принять всё
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  disabled={acting}
                  onClick={() => onAction("keep_verified_only")}
                >
                  Оставить только уверенных
                </Button>
              </>
            )}
            <Button
              type="button"
              size="sm"
              variant="outline"
              disabled={acting}
              onClick={onStartEdit}
            >
              Редактировать текстом
            </Button>
          </div>
        )}

        {error && <p className="text-red-600">{error}</p>}
      </CardContent>
    </Card>
  );
}

export function TeamReviewPanel({
  projectId,
  onUpdated,
  advancedDiagnostics = false,
}: Props) {
  const [data, setData] = useState<TeamReviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState("");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const review = await getTeamReview(projectId);
      setData(review);
      setEditText(review.editable_text);
    } catch (e) {
      setData(null);
      setError(e instanceof Error ? e.message : "Ошибка загрузки команды");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function runAction(
    action: "accept_all" | "keep_verified_only" | "reset_to_auto",
  ) {
    setActing(true);
    setError(null);
    try {
      await teamReviewBulkAction(projectId, action);
      await load();
      onUpdated?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка действия");
    } finally {
      setActing(false);
    }
  }

  async function saveManual() {
    setActing(true);
    setError(null);
    try {
      await teamReviewManualText(projectId, editText);
      setEditing(false);
      await load();
      onUpdated?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка сохранения");
    } finally {
      setActing(false);
    }
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Команда проекта</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Загрузка…
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return null;
  }

  if (data.summary.total_candidates === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Команда проекта</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-amber-900">
            {SIMPLE_TEAM_WARNING}
          </p>
          <Button type="button" size="sm" variant="outline" onClick={() => setEditing(true)}>
            Редактировать текстом
          </Button>
          {editing && (
            <div className="space-y-2">
              <Textarea
                value={editText}
                onChange={(e) => setEditText(e.target.value)}
                rows={8}
                className="font-mono text-xs"
                placeholder="ФИО — роль"
              />
              <Button type="button" size="sm" disabled={acting} onClick={() => void saveManual()}>
                Сохранить команду
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  return (
    <TeamReviewPanelView
      data={data}
      editing={editing}
      editText={editText}
      acting={acting}
      error={error}
      advancedDiagnostics={advancedDiagnostics}
      onEditTextChange={setEditText}
      onStartEdit={() => setEditing(true)}
      onCancelEdit={() => {
        setEditing(false);
        setEditText(data.editable_text);
      }}
      onSaveManual={() => void saveManual()}
      onAction={(action) => void runAction(action)}
    />
  );
}

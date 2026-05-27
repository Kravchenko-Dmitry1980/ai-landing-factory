import React from "react";
import { describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { TeamReviewPanelView } from "./TeamReviewPanel";
import type { TeamReviewData } from "@/lib/types";

const sampleReview: TeamReviewData = {
  project_id: "p1",
  summary: {
    total_candidates: 7,
    verified_count: 1,
    probable_count: 0,
    needs_review_count: 6,
    rejected_count: 0,
    publication_mode: "draft_auto",
    can_publish_team: true,
    warning:
      "Команда извлечена из изображения через OCR. Возможны ошибки в ФИО.",
  },
  candidates: [],
  editable_text: "Кравченко Дмитрий — тимлид\n",
  publication_mode: "draft_auto",
};

const noop = () => {};

describe("TeamReviewPanelView", () => {
  it("renders summary", () => {
    const html = renderToStaticMarkup(
      <TeamReviewPanelView
        data={sampleReview}
        editing={false}
        editText=""
        acting={false}
        error={null}
        advancedDiagnostics={false}
        onEditTextChange={noop}
        onStartEdit={noop}
        onCancelEdit={noop}
        onSaveManual={noop}
        onAction={noop}
      />,
    );
    expect(html).toContain("Найдено участников: 7");
    expect(html).toContain("Уверенно: 1");
    expect(html).toContain("Требуют проверки: 6");
  });

  it("shows bulk action buttons in advanced mode", () => {
    const html = renderToStaticMarkup(
      <TeamReviewPanelView
        data={sampleReview}
        editing={false}
        editText=""
        acting={false}
        error={null}
        advancedDiagnostics={true}
        onEditTextChange={noop}
        onStartEdit={noop}
        onCancelEdit={noop}
        onSaveManual={noop}
        onAction={noop}
      />,
    );
    expect(html).toContain("Принять всё");
    expect(html).toContain("Оставить только уверенных");
    expect(html).toContain("Редактировать текстом");
  });

  it("shows edit textarea when editing", () => {
    const html = renderToStaticMarkup(
      <TeamReviewPanelView
        data={sampleReview}
        editing
        editText="Игорь Колесов — тимлид"
        acting={false}
        error={null}
        onEditTextChange={noop}
        onStartEdit={noop}
        onCancelEdit={noop}
        onSaveManual={noop}
        onAction={noop}
      />,
    );
    expect(html).toContain("Сохранить команду");
    expect(html).toContain("Игорь Колесов");
  });

  it("shows simple review warning without OCR text", () => {
    const html = renderToStaticMarkup(
      <TeamReviewPanelView
        data={sampleReview}
        editing={false}
        editText=""
        acting={false}
        error={null}
        advancedDiagnostics={false}
        onEditTextChange={noop}
        onStartEdit={noop}
        onCancelEdit={noop}
        onSaveManual={noop}
        onAction={noop}
      />,
    );
    expect(html).not.toContain("OCR");
    expect(html).toContain("требует проверки");
  });

  it("shows OCR warning in advanced diagnostics mode", () => {
    const html = renderToStaticMarkup(
      <TeamReviewPanelView
        data={sampleReview}
        editing={false}
        editText=""
        acting={false}
        error={null}
        advancedDiagnostics={true}
        onEditTextChange={noop}
        onStartEdit={noop}
        onCancelEdit={noop}
        onSaveManual={noop}
        onAction={noop}
      />,
    );
    expect(html).toContain("OCR");
  });

  it("save button visible in edit mode", () => {
    const save = vi.fn();
    const html = renderToStaticMarkup(
      <TeamReviewPanelView
        data={sampleReview}
        editing
        editText="test"
        acting={false}
        error={null}
        onEditTextChange={noop}
        onStartEdit={noop}
        onCancelEdit={noop}
        onSaveManual={save}
        onAction={noop}
      />,
    );
    expect(html).toContain("Сохранить команду");
  });
});

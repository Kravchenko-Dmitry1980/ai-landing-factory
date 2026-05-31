/**
 * Demo-ready showcase starter templates (Stage P.6.3).
 */

import type { ShowcaseCreateRequest } from "./showcase";

export type ShowcaseTemplateId = "uii_ai_projects";

const UII_AI_PROJECTS: ShowcaseCreateRequest = {
  title: "Витрина AI-проектов УИИ",
  subtitle:
    "Интерактивная VR/AR-витрина учебных и исследовательских AI-проектов",
  organization: "Университет искусственного интеллекта",
  layout: "gallery_arc",
  mode: "vr_ready",
  theme: "tech",
};

const TEMPLATES: Record<ShowcaseTemplateId, ShowcaseCreateRequest> = {
  uii_ai_projects: UII_AI_PROJECTS,
};

/** Build a showcase create request from a known demo template. */
export function createDefaultShowcaseTemplate(
  templateId: ShowcaseTemplateId = "uii_ai_projects",
): ShowcaseCreateRequest {
  return { ...TEMPLATES[templateId] };
}

/** Minimal payload for an empty custom showcase. */
export function createEmptyShowcaseRequest(): ShowcaseCreateRequest {
  return { title: "Новая витрина" };
}

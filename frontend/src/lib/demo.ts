import { apiRequest } from "./api";
import type { PublicationState } from "./platform";

/** What the studio knows about the demo. The intern sees it only after publication. */
export interface DemoInfo {
  has_draft: boolean;
  has_poster: boolean;
  on_link: boolean;
  pending: boolean;
  updated_at: string | null;
}

export type DemoLoad =
  | { status: "loading" }
  | { status: "ok"; info: DemoInfo }
  | { status: "error"; message: string };

export const MAX_DEMO_BYTES = 50 * 1024 * 1024;
export const MAX_POSTER_BYTES = 2 * 1024 * 1024;

export function demoNote(demo: DemoInfo, state: PublicationState): string {
  if (state === "withdrawn" && demo.has_draft) {
    return "Демо сохранено. После повторной публикации оно появится по новой ссылке.";
  }
  if (demo.pending && demo.on_link && demo.has_draft) {
    return "По ссылке ещё прежнее демо. Обновите публикацию, чтобы показать новое.";
  }
  if (demo.pending && demo.on_link && !demo.has_draft) {
    return "По ссылке ещё есть демо. Обновите публикацию, чтобы убрать его.";
  }
  if (demo.pending && demo.has_draft) {
    return "Демо ещё не по ссылке. Обновите публикацию, чтобы стажёр его увидел.";
  }
  if (demo.on_link) {
    return "По ссылке для стажёра это демо стоит над страницей.";
  }
  if (demo.has_draft) {
    return "Демо готово. Стажёр увидит его над страницей после публикации.";
  }
  return "Когда ролик будет готов, добавьте его здесь. Страница без демо работает как раньше.";
}

/** A second publish button only when the page text is already current and the demo is not. */
export function demoFollowUp(demo: DemoInfo, state: PublicationState): "show" | "remove" | null {
  if (state !== "published" || !demo.pending) return null;
  return demo.has_draft ? "show" : "remove";
}

export function getDemo(projectId: string): Promise<DemoInfo> {
  return apiRequest<DemoInfo>(`/projects/${encodeURIComponent(projectId)}/demo`);
}

export function uploadDemo(projectId: string, video: File, poster: File | null): Promise<DemoInfo> {
  const form = new FormData();
  form.append("video", video);
  if (poster) form.append("poster", poster);
  return apiRequest<DemoInfo>(`/projects/${encodeURIComponent(projectId)}/demo`, { method: "PUT", body: form });
}

export function uploadPoster(projectId: string, poster: File): Promise<DemoInfo> {
  const form = new FormData();
  form.append("poster", poster);
  return apiRequest<DemoInfo>(`/projects/${encodeURIComponent(projectId)}/demo/poster`, { method: "PUT", body: form });
}

export function removeDemo(projectId: string): Promise<DemoInfo> {
  return apiRequest<DemoInfo>(`/projects/${encodeURIComponent(projectId)}/demo`, { method: "DELETE" });
}

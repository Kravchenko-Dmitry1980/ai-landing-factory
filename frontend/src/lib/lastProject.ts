const LAST_PROJECT_ID_KEY = "aiLandingFactory.lastProjectId";
const LAST_EDITOR_URL_KEY = "aiLandingFactory.lastEditorUrl";

export function rememberLastProject(projectId: string, editorUrl?: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(LAST_PROJECT_ID_KEY, projectId);
  const url =
    editorUrl ??
    `${window.location.origin}/editor/${projectId}`;
  localStorage.setItem(LAST_EDITOR_URL_KEY, url);
}

export function getLastProjectId(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(LAST_PROJECT_ID_KEY);
}

export function getLastEditorUrl(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(LAST_EDITOR_URL_KEY);
}

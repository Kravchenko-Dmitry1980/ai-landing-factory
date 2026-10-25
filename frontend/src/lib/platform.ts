import { apiRequest } from "./api";
import { ApiRequestError } from "./api-errors";

/** Accounts, invites, publications and the library: the shared part of the platform. */

export type Role = "viewer" | "editor" | "admin";

const ROLE_RANK: Record<Role, number> = { viewer: 0, editor: 1, admin: 2 };

export const ROLE_LABELS: Record<Role, string> = {
  viewer: "Читатель",
  editor: "Редактор",
  admin: "Администратор",
};

export const ROLE_HINTS: Record<Role, string> = {
  viewer: "смотрит и ищет лендинги в библиотеке",
  editor: "создаёт, правит и публикует лендинги",
  admin: "то же, что редактор, и управляет учётными записями",
};

export interface SessionUser {
  id: string;
  login: string;
  name: string;
  role: Role;
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface InviteInfo {
  id: string;
  /** account: a new account; reset: a new password for an existing one. */
  kind: "account" | "reset";
  role: Role;
  note: string;
  user_name: string | null;
  created_by_name: string | null;
  created_at: string;
  expires_at: string;
}

export interface InviteCreated {
  invite: InviteInfo;
  /** /invite/<token>: shown once, the server keeps only a digest. */
  path: string;
}

export interface PublicationInfo {
  slug: string;
  path: string;
  status: "published" | "withdrawn";
  version: number;
  contract_version: number;
  theme: string;
  title: string;
  first_published_at: string;
  published_at: string;
  published_by_name: string | null;
  withdrawn_at: string | null;
}

export interface TopicTag {
  key: string;
  label: string;
}

export interface LibraryCard {
  project_id: string;
  slug: string;
  path: string;
  title: string;
  summary: string;
  customer: string;
  lead: string;
  people: string[];
  /** Strongest first; empty when the text matches no topic of the library. */
  topics: TopicTag[];
  theme: string;
  version: number;
  first_published_at: string;
  published_at: string;
  published_by_name: string | null;
}

export function hasRole(user: Pick<SessionUser, "role">, minimum: Role): boolean {
  return ROLE_RANK[user.role] >= ROLE_RANK[minimum];
}

const SAME_SITE_BASE = "http://lend.invalid";

/**
 * Where to go after signing in: only paths of this site, never another address.
 * Browsers drop tabs and line breaks from URLs ("/\t/evil.example" turns into "//evil.example"),
 * so the value is resolved the way the browser will resolve it and must stay on the same origin.
 */
export function safeNextPath(raw: string | string[] | null | undefined, fallback = "/"): string {
  const value = Array.isArray(raw) ? raw[0] : raw;
  // eslint-disable-next-line no-control-regex -- control characters are exactly what is refused here
  if (!value || !value.startsWith("/") || /[\u0000-\u001f\u007f\\]/.test(value)) return fallback;
  let resolved: URL;
  try {
    resolved = new URL(value, SAME_SITE_BASE);
  } catch {
    return fallback;
  }
  if (resolved.origin !== SAME_SITE_BASE) return fallback;
  const path = `${resolved.pathname}${resolved.search}${resolved.hash}`;
  if (path.startsWith("/login") || path.startsWith("/invite/")) return fallback;
  return path;
}

/** The backend's own message (written for staff, in Russian), or null when there is none. */
export function apiDetail(err: unknown): string | null {
  if (!(err instanceof ApiRequestError)) return null;
  try {
    const parsed = JSON.parse(err.message) as { detail?: unknown };
    return typeof parsed.detail === "string" && parsed.detail !== "Not Found" ? parsed.detail : null;
  } catch {
    return null;
  }
}

/** A message for a failed action: the server's explanation when it gave one, else a plain fallback. */
export function platformErrorMessage(err: unknown, action: string): string {
  const detail = apiDetail(err);
  if (detail) return detail;
  const status = err instanceof ApiRequestError ? err.status : undefined;
  if (status === null) return `${action}: нет связи с сервером. Проверьте подключение и попробуйте ещё раз.`;
  if (status === 401) return `${action}: вы не вошли в учётную запись. Обновите страницу и войдите.`;
  if (status === 403) return `${action}: у вашей учётной записи нет прав на это действие.`;
  if (typeof status === "number" && status >= 500) return `${action}: сервер не справился. Попробуйте ещё раз через минуту.`;
  return `${action}. Попробуйте ещё раз.`;
}

function sendJson(method: string, body: unknown): RequestInit {
  return { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
}

export function signIn(login: string, password: string): Promise<SessionUser> {
  return apiRequest<SessionUser>("/auth/login", sendJson("POST", { login, password }));
}

export function signOut(): Promise<void> {
  return apiRequest<void>("/auth/logout", { method: "POST" });
}

export function acceptInvite(
  token: string,
  body: { login?: string; name?: string; password: string },
): Promise<SessionUser> {
  return apiRequest<SessionUser>(`/auth/invites/${encodeURIComponent(token)}/accept`, sendJson("POST", body));
}

export function listUsers(): Promise<SessionUser[]> {
  return apiRequest<SessionUser[]>("/admin/users");
}

export function updateUser(id: string, patch: { role?: Role; is_active?: boolean }): Promise<SessionUser> {
  return apiRequest<SessionUser>(`/admin/users/${encodeURIComponent(id)}`, sendJson("PATCH", patch));
}

export function createResetLink(id: string): Promise<InviteCreated> {
  return apiRequest<InviteCreated>(`/admin/users/${encodeURIComponent(id)}/reset-link`, { method: "POST" });
}

export function listInvites(): Promise<InviteInfo[]> {
  return apiRequest<InviteInfo[]>("/admin/invites");
}

export function createInvite(role: Role, note: string): Promise<InviteCreated> {
  return apiRequest<InviteCreated>("/admin/invites", sendJson("POST", { role, note }));
}

export function revokeInvite(id: string): Promise<void> {
  return apiRequest<void>(`/admin/invites/${encodeURIComponent(id)}`, { method: "DELETE" });
}

export function getPublication(projectId: string): Promise<PublicationInfo | null> {
  return apiRequest<PublicationInfo | null>(`/projects/${encodeURIComponent(projectId)}/publication`);
}

export function withdrawPublication(projectId: string): Promise<PublicationInfo> {
  return apiRequest<PublicationInfo>(`/projects/${encodeURIComponent(projectId)}/publication`, { method: "DELETE" });
}

export interface LibraryHit {
  card: LibraryCard;
  /** Where the query was found: "в названии", "участник: …", "похожая тема: …". */
  reasons: string[];
  /** Found through a related topic, not through its own words. */
  similar_topic: boolean;
}

export interface LibrarySearch {
  /** Everything published, whatever the query. */
  total: number;
  query: string;
  /** Counted before the list is cut to the limit. */
  direct_total: number;
  related_total: number;
  /** Words of the query that count; 0 with a non-empty query means nothing searchable was typed. */
  terms: number;
  hits: LibraryHit[];
}

export interface LibraryShelf {
  key: string;
  label: string;
  note: string;
  cards: LibraryCard[];
}

export interface TopicCount {
  key: string;
  label: string;
  count: number;
}

export interface LibraryShelves {
  total: number;
  fresh: LibraryCard[];
  shelves: LibraryShelf[];
  topics: TopicCount[];
}

export interface SimilarCard {
  card: LibraryCard;
  /** What the two landings share: "общая тема: …", "общий заказчик: …", "общие слова: …". */
  reason: string;
}

export function searchLibrary(query: string): Promise<LibrarySearch> {
  const q = query.trim();
  return apiRequest<LibrarySearch>(`/library${q ? `?q=${encodeURIComponent(q)}` : ""}`);
}

/**
 * Renders the saved landing on the frontend server and publishes it (POST /publish/{id}).
 * Errors come back in the backend's format, so platformErrorMessage reads them the same way.
 */
export async function publishLanding(projectId: string, expectedVersion: number | null): Promise<PublicationInfo> {
  let res: Response;
  try {
    res = await fetch(`/publish/${encodeURIComponent(projectId)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      // The version on screen: the server refuses to publish a newer text that nobody here has seen.
      body: JSON.stringify({ expected_version: expectedVersion }),
    });
  } catch {
    throw new ApiRequestError("Failed to fetch", null);
  }
  const text = await res.text();
  if (!res.ok) throw new ApiRequestError(text || `HTTP ${res.status}`, res.status);
  try {
    return JSON.parse(text) as PublicationInfo;
  } catch {
    throw new ApiRequestError(JSON.stringify({ detail: "Сервер ответил непонятно. Обновите страницу и проверьте, опубликован ли лендинг." }), 502);
  }
}

export type PublicationState = "none" | "published" | "outdated" | "withdrawn";

/** outdated: published, but the landing was edited after that and the library shows the older text. */
export function publicationState(
  status: "published" | "withdrawn" | null | undefined,
  publishedContractVersion: number | null | undefined,
  currentContractVersion: number,
): PublicationState {
  if (!status) return "none";
  if (status === "withdrawn") return "withdrawn";
  return publishedContractVersion != null && currentContractVersion > publishedContractVersion ? "outdated" : "published";
}

export const PUBLICATION_STATE_LABELS: Record<Exclude<PublicationState, "none">, string> = {
  published: "В библиотеке",
  outdated: "В библиотеке старая версия",
  withdrawn: "Снят с публикации",
};

const DATE_FORMAT = new Intl.DateTimeFormat("ru-RU", {
  day: "numeric",
  month: "long",
  year: "numeric",
  // Fixed zone: the server and the browser must print the same date (no hydration mismatch).
  timeZone: "Europe/Moscow",
});

const YEAR_FORMAT = new Intl.DateTimeFormat("ru-RU", { year: "numeric", timeZone: "Europe/Moscow" });

/** The year in Moscow time, the same on the server and in the browser. */
export function formatYear(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? "" : YEAR_FORMAT.format(d).replace(/\D/g, "");
}

/** "24 октября 2026 г." → "24 октября 2026". */
export function formatDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return DATE_FORMAT.format(d).replace(/\s*г\.$/, "");
}

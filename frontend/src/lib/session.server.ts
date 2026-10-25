import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { getApiBaseUrl } from "./api";
import { hasRole, type Role, type SessionUser } from "./platform";

/** The backend's session cookie: set SESSION_COOKIE_NAME for both, or neither ("lend_session"). */
export const SESSION_COOKIE = (process.env.SESSION_COOKIE_NAME ?? "").trim() || "lend_session";

const SESSION_CHECK_TIMEOUT_MS = 10_000;

/** A Cookie header with only the session, for server-side calls to the backend on the visitor's behalf. */
export async function sessionCookieHeader(): Promise<string | null> {
  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  return token ? `${SESSION_COOKIE}=${token}` : null;
}

/** fetch() to the backend API from the frontend server, signed in as the current visitor. */
export async function backendFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  const cookie = await sessionCookieHeader();
  if (cookie) headers.set("cookie", cookie);
  return fetch(`${getApiBaseUrl()}${path}`, { cache: "no-store", ...init, headers });
}

/**
 * The signed-in visitor, or null without a valid session.
 * Throws when the backend cannot answer: that is an outage, not a reason to show the login form.
 */
export async function getSessionUser(): Promise<SessionUser | null> {
  if (!(await sessionCookieHeader())) return null;
  const res = await backendFetch("/auth/me", { signal: AbortSignal.timeout(SESSION_CHECK_TIMEOUT_MS) });
  if (res.status === 401) return null;
  if (!res.ok) throw new Error(`Session check failed: HTTP ${res.status}`);
  return (await res.json()) as SessionUser;
}

/**
 * For pages: a visitor without a session goes to /login and comes back to `returnTo` afterwards;
 * an account without the role goes to the library, which every account can open.
 */
export async function requireUser(returnTo: string, minimum: Role = "viewer"): Promise<SessionUser> {
  const user = await getSessionUser();
  if (!user) redirect(`/login?next=${encodeURIComponent(returnTo)}`);
  if (!hasRole(user, minimum)) redirect("/");
  return user;
}

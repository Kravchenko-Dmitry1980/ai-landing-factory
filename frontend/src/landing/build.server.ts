import { slugifyRu } from "@/lib/staff";
import type { LandingContract, TeamMember } from "@/lib/types";
import { backendFetch } from "@/lib/session.server";
import { loadLandingAssets } from "./assets.server";
import { buildLandingModel, themeFromContract, type LandingModel, type LandingTheme } from "./model";
import { renderLandingHtml } from "./render";

const BACKEND_TIMEOUT_MS = 15_000;

/** A failure with a message for staff and the HTTP status to answer with. */
export class LandingBuildError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

export interface BuiltLanding {
  html: string;
  fileName: string;
  contract: LandingContract;
  model: LandingModel;
  theme: LandingTheme;
}

async function backendJson<T>(path: string, what: string): Promise<T> {
  let res: Response;
  try {
    res = await backendFetch(path, { signal: AbortSignal.timeout(BACKEND_TIMEOUT_MS) });
  } catch (err) {
    const timedOut = err instanceof Error && err.name === "TimeoutError";
    console.error(`Landing: ${what} request failed`, path, err);
    throw new LandingBuildError(
      timedOut ? "Сервер данных не ответил вовремя. Попробуйте ещё раз." : "Нет связи с сервером данных. Попробуйте ещё раз.",
      timedOut ? 504 : 502,
    );
  }
  if (res.status === 401) throw new LandingBuildError("Войдите в учётную запись, чтобы открыть лендинг.", 401);
  if (res.status === 403) throw new LandingBuildError("У вашей учётной записи нет доступа к студии.", 403);
  if (res.status === 404 || res.status === 422) {
    throw new LandingBuildError("Лендинг не найден или материалы ещё не загружены.", 404);
  }
  if (!res.ok) {
    console.error(`Landing: ${what} returned ${res.status}`, path, (await res.text()).slice(0, 300));
    throw new LandingBuildError("Сервер данных вернул ошибку. Попробуйте ещё раз через минуту.", 502);
  }
  try {
    return (await res.json()) as T;
  } catch (err) {
    console.error(`Landing: ${what} is not JSON`, path, err);
    throw new LandingBuildError("Сервер данных ответил не тем форматом. Сообщите разработчику.", 502);
  }
}

function assertContract(value: unknown): asserts value is LandingContract {
  const c = value as LandingContract | null;
  if (!c || typeof c !== "object" || !Array.isArray(c.blocks)) {
    console.error("Landing: contract has an unexpected shape", value);
    throw new LandingBuildError("Данные лендинга повреждены. Сообщите разработчику.", 502);
  }
}

/**
 * The saved landing of a project, rendered by the single v2 engine, on behalf of the signed-in visitor.
 * The preview, the downloaded file and the published page all come from here.
 *
 * @param requireTeam publishing: fail when the team cannot be loaded instead of leaving it out,
 *   so the library never keeps a page without its team (search would still find those names).
 */
export async function buildProjectLanding(
  projectId: string,
  { theme: themeOverride, requireTeam = false }: { theme?: LandingTheme; requireTeam?: boolean } = {},
): Promise<BuiltLanding> {
  const id = encodeURIComponent(projectId);
  const teamRequest = backendJson<TeamMember[]>(`/projects/${id}/public-team`, "public team");
  const [contract, publicTeam] = await Promise.all([
    backendJson<unknown>(`/projects/${id}/contract`, "contract"),
    // The team goes through the backend publication policy; without it the preview shows no team.
    requireTeam
      ? teamRequest.catch((err: unknown) => {
          console.error("Landing: publishable team unavailable, publication stopped", projectId, err);
          throw new LandingBuildError("Не удалось загрузить команду проекта, поэтому публикация отменена. Попробуйте ещё раз.", 502);
        })
      : teamRequest.catch((err: unknown) => {
          console.error("Landing: publishable team unavailable, rendering without a team", projectId, err);
          return null;
        }),
  ]);
  assertContract(contract);
  const theme = themeOverride ?? themeFromContract(contract);

  let assets;
  try {
    assets = await loadLandingAssets();
  } catch (err) {
    console.error("Landing: fonts or cat image could not be read from disk", err);
    throw new LandingBuildError("Не удалось собрать страницу: на сервере нет файлов оформления. Сообщите разработчику.", 500);
  }

  try {
    const model = buildLandingModel(contract, Array.isArray(publicTeam) ? publicTeam : null);
    const html = renderLandingHtml(model, { theme, assets });
    return { html, fileName: `${slugifyRu(contract.title || "landing")}.html`, contract, model, theme };
  } catch (err) {
    console.error("Landing: render failed", projectId, err);
    throw new LandingBuildError("Не удалось собрать страницу. Сообщите разработчику.", 500);
  }
}

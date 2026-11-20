import { describe, expect, it } from "vitest";
import { suggestLogin } from "@/components/account/AcceptInviteForm";
import { publishButtonLabel } from "@/components/editor/PublishPanel";
import { resultsHeading } from "@/components/library/LibraryView";
import { cardExtra } from "@/components/library/LibraryCardView";
import { ApiRequestError } from "./api-errors";
import { apiDetail, formatDate, formatYear, hasRole, platformErrorMessage, publicationState, safeNextPath } from "./platform";

describe("safeNextPath", () => {
  it("keeps paths of this site", () => {
    expect(safeNextPath("/studio")).toBe("/studio");
    expect(safeNextPath("/p/kontrol-kassy?x=1")).toBe("/p/kontrol-kassy?x=1");
    expect(safeNextPath(["/admin", "/studio"])).toBe("/admin");
  });

  it("never sends the visitor to another site or back to the sign-in forms", () => {
    for (const bad of ["https://evil.example", "//evil.example", "/\\evil.example", "evil", "", undefined, null]) {
      expect(safeNextPath(bad)).toBe("/");
    }
    expect(safeNextPath("/login?next=/x")).toBe("/");
    expect(safeNextPath("/invite/abc")).toBe("/");
  });

  it("refuses paths that the browser would turn into another site", () => {
    // Browsers drop tabs and line breaks: "/\t/evil.example" would open //evil.example.
    for (const bad of ["/\t/evil.example", "/\n/evil.example", "/\r/evil.example"]) {
      expect(safeNextPath(bad)).toBe("/");
    }
    // An encoded tab stays text inside the path and keeps the visitor on this site.
    expect(safeNextPath("/%09/x")).toBe("/%09/x");
    expect(safeNextPath("/./login")).toBe("/");
  });
});

describe("error messages", () => {
  it("prefers the backend's own explanation", () => {
    const err = new ApiRequestError(JSON.stringify({ detail: "Такой логин уже занят." }), 409);
    expect(apiDetail(err)).toBe("Такой логин уже занят.");
    expect(platformErrorMessage(err, "Не удалось")).toBe("Такой логин уже занят.");
  });

  it("falls back to a plain sentence by status", () => {
    expect(apiDetail(new ApiRequestError("<html>", 502))).toBeNull();
    expect(apiDetail(new ApiRequestError(JSON.stringify({ detail: [{ msg: "x" }] }), 422))).toBeNull();
    expect(platformErrorMessage(new ApiRequestError("Failed to fetch", null), "Не удалось войти")).toContain("нет связи");
    expect(platformErrorMessage(new ApiRequestError("", 403), "Не удалось")).toContain("нет прав");
    expect(platformErrorMessage(new ApiRequestError("", 503), "Не удалось")).toContain("сервер не справился");
    expect(platformErrorMessage(new Error("boom"), "Не удалось войти")).toBe("Не удалось войти. Попробуйте ещё раз.");
  });
});

describe("roles", () => {
  it("ranks admin over editor over viewer", () => {
    expect(hasRole({ role: "admin" }, "editor")).toBe(true);
    expect(hasRole({ role: "editor" }, "editor")).toBe(true);
    expect(hasRole({ role: "viewer" }, "editor")).toBe(false);
    expect(hasRole({ role: "viewer" }, "viewer")).toBe(true);
  });
});

describe("publication state", () => {
  it("tells whether the library shows what is on screen", () => {
    expect(publicationState(null, null, 3)).toBe("none");
    expect(publicationState("published", 3, 3)).toBe("published");
    expect(publicationState("published", 3, 5)).toBe("outdated");
    expect(publicationState("withdrawn", 3, 5)).toBe("withdrawn");
  });

  it("offers to publish only when there is something new", () => {
    expect(publishButtonLabel("none")).toBe("Опубликовать");
    expect(publishButtonLabel("withdrawn")).toBe("Опубликовать");
    expect(publishButtonLabel("outdated")).toBe("Обновить в библиотеке");
    expect(publishButtonLabel("published")).toBeNull();
  });

  it("requires an explicit publication action to share an older private page", () => {
    expect(publishButtonLabel("published", true)).toBe("Создать ссылку для стажёра");
    expect(publishButtonLabel("published", false)).toBeNull();
    expect(publishButtonLabel("outdated", true)).toBe("Обновить в библиотеке");
  });
});

describe("texts", () => {
  it("prints dates in Moscow time without the year abbreviation", () => {
    expect(formatDate("2026-10-24T22:30:00+00:00")).toBe("25 октября 2026");
    expect(formatDate("not a date")).toBe("");
  });

  it("takes the year in Moscow time as well", () => {
    expect(formatYear("2025-12-31T22:30:00+00:00")).toBe("2026");
    expect(formatYear("nope")).toBe("");
  });

  it("names the team size under a card, or the customer when the page has no team", () => {
    const base = { people: [] as string[], customer: "ООО «Пример»" };
    expect(cardExtra({ ...base, people: ["А", "Б", "В"] } as never)).toBe("3 участника");
    expect(cardExtra({ ...base, people: Array(11).fill("А") } as never)).toBe("11 участников");
    expect(cardExtra(base as never)).toBe("ООО «Пример»");
  });

  it("suggests a Latin login from the name", () => {
    expect(suggestLogin("Мария Соколова")).toBe("mariya.sokolova");
    expect(suggestLogin("  ")).toBe("");
  });

  it("words search results by number", () => {
    const found = (query: string, direct: number, related: number, shown = direct + related, terms = 1) =>
      resultsHeading({ query, direct_total: direct, related_total: related, terms, hits: Array(shown).fill(null) });
    expect(found("касса", 1, 0)).toBe("По запросу «касса» нашёлся 1 проект.");
    expect(found("касса", 3, 2)).toBe("По запросу «касса» нашлось 3 проекта, ещё 2 на похожую тему.");
    expect(found("видеонаблюдение", 0, 2)).toBe("Точных совпадений с «видеонаблюдение» нет. Проекты на похожую тему: 2.");
    expect(found("касса", 0, 0)).toContain("ничего не нашлось");
    expect(found("склад", 150, 0, 100)).toBe("По запросу «склад» нашлось 150 проектов. Показаны первые 100.");
    expect(found("?!", 0, 0, 0, 0)).toContain("нет слов для поиска");
  });
});

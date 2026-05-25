/** Map raw fetch/API errors to user-friendly messages (no PII). */

export function formatApiError(err: unknown, fallback = "Ошибка запроса к API"): string {
  const raw = err instanceof Error ? err.message : String(err);

  if (raw.includes("Failed to fetch") || raw.includes("NetworkError") || raw.includes("fetch")) {
    return "Backend недоступен. Проверьте, что uvicorn запущен и NEXT_PUBLIC_API_URL верный.";
  }

  if (raw.includes("Not Found") || raw.includes('"detail":"Not Found"') || raw.includes("404")) {
    return "API endpoint not found. Проверьте backend URL и route.";
  }

  try {
    const parsed = JSON.parse(raw) as { detail?: string | unknown[] };
    if (typeof parsed.detail === "string") {
      if (parsed.detail === "Not Found") {
        return "API endpoint not found. Проверьте backend URL и route.";
      }
      return parsed.detail;
    }
  } catch {
    // not JSON — keep raw if short and safe
  }

  if (raw.length > 200) {
    return fallback;
  }

  return raw || fallback;
}

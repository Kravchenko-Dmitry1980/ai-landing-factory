import { describe, expect, it } from "vitest";
import { ApiRequestError, formatApiError, getApiErrorStatus } from "./api-errors";

describe("api-errors", () => {
  it("returns status for ApiRequestError", () => {
    const err = new ApiRequestError("missing", 404);
    expect(getApiErrorStatus(err)).toBe(404);
  });

  it("formats backend endpoint 404 message", () => {
    const message = formatApiError(new ApiRequestError('{"detail":"Not Found"}', 404));
    expect(message).toContain("API endpoint not found");
  });

  it("formats backend unavailability", () => {
    const message = formatApiError(new ApiRequestError("Failed to fetch", null));
    expect(message).toContain("Backend недоступен");
  });
});

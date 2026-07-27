import { describe, expect, it, afterEach, vi } from "vitest";
import { getApiBaseUrl, resolveApiBaseUrl } from "./api";

describe("getApiBaseUrl", () => {
  const originalEnv = { ...process.env };

  afterEach(() => {
    process.env = { ...originalEnv };
    vi.unstubAllGlobals();
  });

  it("uses INTERNAL_API_URL on server when set", () => {
    vi.stubGlobal("window", undefined);
    process.env.INTERNAL_API_URL = "http://backend:8001/api/v1/";
    process.env.NEXT_PUBLIC_API_URL = "/api/v1";
    expect(getApiBaseUrl()).toBe("http://backend:8001/api/v1");
  });

  it("server uses absolute NEXT_PUBLIC when INTERNAL unset (local Windows)", () => {
    vi.stubGlobal("window", undefined);
    delete process.env.INTERNAL_API_URL;
    process.env.NEXT_PUBLIC_API_URL = "http://127.0.0.1:8001/api/v1";
    expect(getApiBaseUrl()).toBe("http://127.0.0.1:8001/api/v1");
  });

  it("uses NEXT_PUBLIC_API_URL in browser", () => {
    vi.stubGlobal("window", {});
    process.env.NEXT_PUBLIC_API_URL = "/api/v1/";
    process.env.INTERNAL_API_URL = "http://backend:8001/api/v1";
    expect(getApiBaseUrl()).toBe("/api/v1");
  });

  it("browser default is /api/v1 when NEXT_PUBLIC unset", () => {
    vi.stubGlobal("window", {});
    delete process.env.NEXT_PUBLIC_API_URL;
    expect(getApiBaseUrl()).toBe("/api/v1");
  });

  it("resolveApiBaseUrl aliases getApiBaseUrl", () => {
    vi.stubGlobal("window", {});
    process.env.NEXT_PUBLIC_API_URL = "/api/v1";
    expect(resolveApiBaseUrl()).toBe(getApiBaseUrl());
  });
});

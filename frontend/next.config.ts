import type { NextConfig } from "next";

/**
 * Local development: the browser calls /api/v1 on the frontend's own address and Next.js
 * forwards it to the backend (API_PROXY_TARGET, written by scripts/start_dev.ps1). On the
 * server nginx does the same, so the HttpOnly session cookie behaves identically in both.
 */
const apiProxyTarget = (process.env.API_PROXY_TARGET ?? "").trim().replace(/\/$/, "");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  experimental: {
    // Building a landing from large files can take minutes; the default proxy timeout is 30 s.
    proxyTimeout: 300_000,
  },
  async rewrites() {
    if (!apiProxyTarget) return [];
    return [{ source: "/api/v1/:path*", destination: `${apiProxyTarget}/api/v1/:path*` }];
  },
};

export default nextConfig;

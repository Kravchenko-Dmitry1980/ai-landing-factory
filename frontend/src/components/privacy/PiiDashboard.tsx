"use client";

import { useCallback, useEffect, useState } from "react";
import {
  formatApiError,
  getPiiReport,
  getPrivacyConfig,
  getSafeCloudPayload,
  runPiiPrescan,
} from "@/lib/api";
import type {
  PIIReportPublic,
  PrivacyStatusResponse,
  SafeCloudPayloadPreview,
} from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PiiEntityGroups } from "./PiiEntityGroups";
import { PiiReportExpiry } from "./PiiReportExpiry";
import { PiiRiskBadge } from "./PiiRiskBadge";
import { PrivacyModeStatus } from "./PrivacyModeStatus";
import { SafeCloudPayloadPreviewPanel } from "./SafeCloudPayloadPreview";

interface Props {
  projectId: string;
  defaultOpen?: boolean;
}

export function PiiDashboard({ projectId, defaultOpen = false }: Props) {
  const [open, setOpen] = useState(defaultOpen);
  const [report, setReport] = useState<PIIReportPublic | null>(null);
  const [privacy, setPrivacy] = useState<PrivacyStatusResponse | null>(null);
  const [payload, setPayload] = useState<SafeCloudPayloadPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setApiError(null);
    try {
      const [r, p, s] = await Promise.all([
        getPiiReport(projectId),
        getPrivacyConfig(),
        getSafeCloudPayload(projectId),
      ]);
      setReport(r);
      setPrivacy(p);
      setPayload(s);
    } catch (err) {
      setReport(null);
      setPayload(null);
      setApiError(formatApiError(err, "Не удалось загрузить privacy data"));
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    if (open) load();
  }, [open, load]);

  async function handleRefresh() {
    setRefreshing(true);
    try {
      const r = await runPiiPrescan(projectId);
      setReport(r);
      const s = await getSafeCloudPayload(projectId);
      setPayload(s);
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <Card className="border-slate-200">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex flex-wrap items-center gap-2">
          <CardTitle className="text-base">Privacy & PII</CardTitle>
          {report && (
            <PiiRiskBadge riskLevel={report.risk_level} hasPii={report.has_pii} />
          )}
        </div>
        <Button variant="ghost" size="sm" type="button" onClick={() => setOpen((v) => !v)}>
          {open ? "Свернуть" : "Развернуть"}
        </Button>
      </CardHeader>
      {open && (
        <CardContent className="space-y-4">
          <PrivacyModeStatus status={privacy} />
          {apiError && (
            <p className="text-sm text-red-600">{apiError}</p>
          )}
          {loading ? (
            <p className="text-sm text-muted-foreground">Загрузка…</p>
          ) : (
            <>
              {report && (
                <div className="space-y-2">
                  <p className="text-xs text-muted-foreground">
                    Detectors: {report.detectors_used.join(", ") || "—"} · redactions:{" "}
                    {report.redaction_count}
                  </p>
                  {report.source_files.length > 0 && (
                    <p className="text-xs text-muted-foreground">
                      Files: {report.source_files.join(", ")}
                    </p>
                  )}
                  <PiiReportExpiry expiresAt={report.expires_at} />
                  {report.warnings.length > 0 && (
                    <p className="text-xs text-amber-700">{report.warnings.join("; ")}</p>
                  )}
                  <PiiEntityGroups entities={report.entities} />
                </div>
              )}
              <div>
                <p className="mb-2 text-sm font-medium">Что будет отправлено в облачную модель</p>
                <SafeCloudPayloadPreviewPanel preview={payload} />
              </div>
              <Button
                variant="outline"
                size="sm"
                type="button"
                onClick={handleRefresh}
                disabled={refreshing}
              >
                {refreshing ? "Сканирование…" : "Обновить pre-scan"}
              </Button>
            </>
          )}
        </CardContent>
      )}
    </Card>
  );
}

"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  exportHtml,
  formatApiError,
  getContract,
  getLanding,
  getPrivacyStatus,
  getSemanticLanding,
} from "@/lib/api";
import type { GeneratedSemanticLanding, PrivacyStatusResponse } from "@/lib/types";
import { DomainDebugPanel } from "@/components/domain/DomainDebugPanel";
import { ArchitectureDebugPanel } from "@/components/architecture/ArchitectureDebugPanel";
import { SemanticDebugPanel } from "@/components/semantic/SemanticDebugPanel";
import { PrivacyBanner } from "@/components/privacy/PrivacyBanner";
import type { GeneratedLanding, LandingContract } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { InteractiveRenderer } from "@/rendering/renderer";
import {
  resolveExportStyleConfig,
  resolveExportTheme,
  resolveRenderConfig,
  saveRenderConfig,
} from "@/rendering/contract_adapter";
import type { RenderConfig } from "@/rendering/types";

interface Props {
  projectId: string;
}

export function LandingPreview({ projectId }: Props) {
  const searchParams = useSearchParams();
  const urlStyle = searchParams.get("style");
  const [landing, setLanding] = useState<GeneratedLanding | null>(null);
  const [contract, setContract] = useState<LandingContract | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [privacyStatus, setPrivacyStatus] = useState<PrivacyStatusResponse | null>(null);
  const [renderConfig, setRenderConfig] = useState<RenderConfig | null>(null);
  const [semantic, setSemantic] = useState<GeneratedSemanticLanding | null>(null);

  const showDevPanel = useMemo(() => {
    if (typeof window === "undefined") return false;
    return (
      new URLSearchParams(window.location.search).has("dev") ||
      renderConfig?.showDevPanel === true
    );
  }, [renderConfig?.showDevPanel]);

  const showArchitectureDebug = useMemo(() => {
    if (typeof window === "undefined") return false;
    return new URLSearchParams(window.location.search).has("architecture_debug");
  }, []);

  const showDomainDebug = useMemo(() => {
    if (typeof window === "undefined") return false;
    return new URLSearchParams(window.location.search).has("domain_debug");
  }, []);

  const showSemanticDebug = useMemo(() => {
    if (typeof window === "undefined") return false;
    return new URLSearchParams(window.location.search).has("semantic_debug");
  }, []);

  const showFidelityDebug = useMemo(() => {
    if (typeof window === "undefined") return false;
    return new URLSearchParams(window.location.search).has("fidelity_debug");
  }, []);

  const urlStyleDisplay = urlStyle;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [landingData, contractData, privacy, semanticData] = await Promise.all([
        getLanding(projectId),
        getContract(projectId).catch(() => null),
        getPrivacyStatus(),
        getSemanticLanding(projectId).catch(() => null),
      ]);
      setLanding(landingData);
      setContract(contractData);
      setPrivacyStatus(privacy);
      setSemantic(semanticData);
    } catch (err) {
      setError(formatApiError(err, "Preview недоступен"));
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!landing) return;
    setRenderConfig(resolveRenderConfig(projectId, landing, contract, urlStyle));
  }, [projectId, landing, contract, urlStyle]);

  function handleConfigChange(config: RenderConfig) {
    setRenderConfig(config);
    saveRenderConfig(projectId, config);
  }

  async function handleExport() {
    const theme = resolveExportTheme(renderConfig, contract, urlStyle, landing);
    const styleConfig = resolveExportStyleConfig(renderConfig, contract);
    const html = await exportHtml(projectId, { theme, styleConfig });
    const blob = new Blob([html], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `landing-${projectId}.html`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (loading) return <p className="text-muted-foreground">Загрузка preview…</p>;
  if (error) return <p className="text-red-600">{error}</p>;
  if (!landing || !renderConfig) return null;

  return (
    <div className="space-y-6">
      <PrivacyBanner status={privacyStatus} />
      <div className="flex flex-wrap items-center gap-2">
        <Link href={`/editor/${projectId}`}>
          <Button variant="outline" type="button">
            Редактор
          </Button>
        </Link>
        <Button variant="outline" onClick={handleExport}>
          Экспорт HTML{renderConfig?.profileId === "university_platform" ? " (university)" : ""}
        </Button>
        <span className="text-xs text-muted-foreground">
          Stage D renderer · {renderConfig.profileId} / {renderConfig.layoutId}
          {urlStyleDisplay && (
            <> · style query: <code className="text-xs">{urlStyleDisplay}</code></>
          )}
          {!showDevPanel && (
            <> · add <code className="text-xs">?dev=1</code> for dev panel</>
          )}
          {!showSemanticDebug && (
            <> · <code className="text-xs">?semantic_debug=1</code> for semantic debug</>
          )}
          {!showArchitectureDebug && (
            <> · <code className="text-xs">?architecture_debug=1</code> for topology</>
          )}
          {!showDomainDebug && (
            <> · <code className="text-xs">?domain_debug=1</code> for domain intelligence</>
          )}
          {!showFidelityDebug && (
            <> · <code className="text-xs">?fidelity_debug=1</code> for fidelity sources</>
          )}
        </span>
      </div>

      {showDomainDebug && (
        <DomainDebugPanel
          projectId={projectId}
          semanticDomain={
            semantic?.intelligence_domain_profile?.primary_domain ?? semantic?.domain
          }
          compact
        />
      )}

      {showSemanticDebug && semantic && (
        <SemanticDebugPanel semantic={semantic} />
      )}

      {showArchitectureDebug && (
        <ArchitectureDebugPanel topology={semantic?.architecture} />
      )}

      <InteractiveRenderer
        landing={landing}
        contract={contract}
        projectId={projectId}
        semantic={semantic}
        config={renderConfig}
        onConfigChange={handleConfigChange}
        showDevPanel={showDevPanel}
        showFidelityDebug={showFidelityDebug}
      />
    </div>
  );
}

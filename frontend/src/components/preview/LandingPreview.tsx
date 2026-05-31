"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  exportHtml,
  exportWowBundleZip,
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
import { WowExportPanel } from "@/components/preview/WowExportPanel";
import { WowHeroCanvas } from "@/components/wow/WowHeroCanvas";
import { parseWowHeroMode, isWowMode } from "@/lib/wowHeroMode";
import { normalizeThemeTokens } from "@/design/themeTokens";
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
  const heroMode = parseWowHeroMode(searchParams.get("mode"));
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

  const heroAccent = useMemo(() => {
    const styleConfig = contract?.style_config ?? { profile: "tech" as const };
    try {
      return normalizeThemeTokens(styleConfig).accent;
    } catch {
      return "#7c8bff";
    }
  }, [contract]);

  const modeHref = useCallback(
    (mode: "standard" | "wow" | "wow3d") => {
      const params = new URLSearchParams(searchParams.toString());
      if (mode === "standard") {
        params.delete("mode");
      } else {
        params.set("mode", mode);
      }
      const qs = params.toString();
      return qs ? `?${qs}` : "?";
    },
    [searchParams],
  );

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

  function downloadHtml(html: string, suffix: string) {
    const blob = new Blob([html], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `landing-${projectId}${suffix}.html`;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function handleExport() {
    const theme = resolveExportTheme(renderConfig, contract, urlStyle, landing);
    const styleConfig = resolveExportStyleConfig(renderConfig, contract);
    const html = await exportHtml(projectId, { theme, styleConfig });
    downloadHtml(html, "");
  }

  async function handleWowExport(withRuntime: boolean) {
    const theme = resolveExportTheme(renderConfig, contract, urlStyle, landing);
    const styleConfig = resolveExportStyleConfig(renderConfig, contract);
    const html = await exportHtml(projectId, {
      theme,
      styleConfig,
      mode: "wow",
      wow3dRuntime: withRuntime ? "aframe" : "none",
    });
    downloadHtml(html, withRuntime ? "-wow-3d" : "-wow");
  }

  async function handleWowBundleExport() {
    try {
      const { blob, filename } = await exportWowBundleZip(projectId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(formatApiError(err, "Не удалось собрать интерактивный WOW ZIP"));
    }
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

      <WowExportPanel
        onStandard={handleExport}
        onWow={() => handleWowExport(false)}
        onWow3d={() => handleWowExport(true)}
        onWowBundle={handleWowBundleExport}
      />

      <section
        className="rounded-lg border border-border bg-muted/40 p-4"
        aria-label="Режим preview"
      >
        <h2 className="text-sm font-semibold">Режим preview</h2>
        <p className="mt-1 text-xs text-muted-foreground">
          WOW-hero — интерактивная 3D-сцена (React Three Fiber) поверх обычного
          лендинга. Standard остаётся без изменений.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <Link href={modeHref("standard")} scroll={false}>
            <Button variant={heroMode === "standard" ? "default" : "outline"} type="button">
              Standard
            </Button>
          </Link>
          <Link href={modeHref("wow")} scroll={false}>
            <Button variant={heroMode === "wow" ? "default" : "outline"} type="button">
              WOW
            </Button>
          </Link>
          <Link href={modeHref("wow3d")} scroll={false}>
            <Button variant={heroMode === "wow3d" ? "default" : "outline"} type="button">
              WOW 3D
            </Button>
          </Link>
        </div>
      </section>

      {isWowMode(heroMode) && (
        <WowHeroCanvas
          landing={landing}
          contract={contract}
          semantic={semantic}
          mode={heroMode}
          accent={heroAccent}
        />
      )}

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

      <div id="wow-landing-content">
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
    </div>
  );
}

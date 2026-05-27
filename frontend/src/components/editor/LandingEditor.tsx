"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { buildPreviewHref } from "@/rendering/contract_adapter";
import { useCallback, useEffect, useState } from "react";
import {
  enrichContract,
  formatApiError,
  generateLanding,
  getContract,
  getContractCompleteness,
  getEvidenceReport,
  getLanding,
  getSourceStructure,
  reparseStructuredLanding,
  regenerateLanding,
  updateContract,
} from "@/lib/api";
import type {
  ContractCompletenessReport,
  EnrichmentMetadata,
  GeneratedLanding,
  GeneratedSemanticLanding,
  LandingBlock,
  LandingContract,
  LandingStylePreset,
  EvidenceVisibility,
  SourceStructureReport,
} from "@/lib/types";
import { ContractQualityPanel } from "@/components/editor/ContractQualityPanel";
import { ProjectSourceStatusPanel } from "@/components/editor/ProjectSourceStatusPanel";
import { SourceStructurePanel } from "@/components/editor/SourceStructurePanel";
import { TeamCardsPanel } from "@/components/editor/TeamCardsPanel";
import { TeamReviewPanel } from "@/components/editor/TeamReviewPanel";
import { DomainDebugPanel } from "@/components/domain/DomainDebugPanel";
import { SemanticDebugPanel } from "@/components/semantic/SemanticDebugPanel";
import { ArchitectureDebugPanel } from "@/components/architecture/ArchitectureDebugPanel";
import { PiiBadge } from "@/components/privacy/PiiBadge";
import { PiiDashboard } from "@/components/privacy/PiiDashboard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

const STYLES: { value: LandingStylePreset; label: string }[] = [
  { value: "minimal", label: "Minimal" },
  { value: "corporate", label: "Corporate" },
  { value: "tech", label: "Tech" },
  { value: "bold", label: "Bold" },
];

const PRESENTATION_PROFILES: { value: string; label: string }[] = [
  { value: "", label: "Auto (по стилю ленда)" },
  { value: "university_platform", label: "University / Платформа УИИ" },
];

interface Props {
  projectId: string;
}

export function LandingEditor({ projectId }: Props) {
  const router = useRouter();
  const [contract, setContract] = useState<LandingContract | null>(null);
  const [blocks, setBlocks] = useState<LandingBlock[]>([]);
  const [style, setStyle] = useState<LandingStylePreset>("minimal");
  const [presentationStyle, setPresentationStyle] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [enriching, setEnriching] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [semanticInfo, setSemanticInfo] = useState<GeneratedSemanticLanding | null>(null);
  const [semanticMessage, setSemanticMessage] = useState<string | null>(null);
  const [enrichmentInfo, setEnrichmentInfo] = useState<EnrichmentMetadata | null>(null);
  const [enrichMessage, setEnrichMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [completeness, setCompleteness] = useState<ContractCompletenessReport | null>(null);
  const [sourceStructure, setSourceStructure] = useState<SourceStructureReport | null>(null);
  const [evidenceVisibility, setEvidenceVisibility] = useState<EvidenceVisibility | null>(null);
  const [landingPreview, setLandingPreview] = useState<GeneratedLanding | null>(null);
  const [structureLoading, setStructureLoading] = useState(false);
  const [evidenceLoading, setEvidenceLoading] = useState(false);
  const [reparsing, setReparsing] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getContract(projectId);
      setContract(data);
      setBlocks(data.blocks);
      setStyle(data.style);
      setPresentationStyle(
        data.presentation_style && !data.presentation_style.startsWith("layout:")
          ? data.presentation_style
          : "",
      );
      setEnrichmentInfo(data.enrichment ?? null);
      setEvidenceLoading(true);
      try {
        setCompleteness(await getContractCompleteness(projectId));
      } catch {
        setCompleteness(data.fidelity?.completeness ?? null);
      }
      try {
        setSourceStructure(await getSourceStructure(projectId));
      } catch {
        setSourceStructure(null);
      }
      try {
        setEvidenceVisibility(await getEvidenceReport(projectId));
      } catch {
        setEvidenceVisibility(null);
      }
      try {
        setLandingPreview(await getLanding(projectId));
      } catch {
        setLandingPreview(null);
      }
      setEvidenceLoading(false);
    } catch (err) {
      setError(formatApiError(err, "Не удалось загрузить контракт"));
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    load();
  }, [load]);

  function updateBlock(index: number, content: string) {
    setBlocks((prev) =>
      prev.map((b, i) => (i === index ? { ...b, content } : b)),
    );
  }

  async function handleGenerateLanding() {
    setGenerating(true);
    setError(null);
    setSemanticMessage(null);
    try {
      const result = await generateLanding(projectId);
      setSemanticInfo(result.semantic);
      setSemanticMessage(result.message);
      setContract(await getContract(projectId));
      router.push(buildPreviewHref(projectId, presentationStyle || undefined));
    } catch (err) {
      setError(formatApiError(err, "Не удалось сформировать ленд"));
    } finally {
      setGenerating(false);
    }
  }

  async function handleEnrich() {
    setEnriching(true);
    setError(null);
    setEnrichMessage(null);
    try {
      const result = await enrichContract(projectId);
      setContract(result.contract);
      setBlocks(result.contract.blocks);
      setEnrichmentInfo(result.enrichment);
      setEnrichMessage(result.message);
      await regenerateLanding(projectId);
    } catch (err) {
      setError(formatApiError(err, "Ошибка LLM enrichment"));
    } finally {
      setEnriching(false);
    }
  }

  async function handleReparse() {
    setReparsing(true);
    setError(null);
    try {
      const updated = await reparseStructuredLanding(projectId);
      setContract(updated);
      setBlocks(updated.blocks);
      setCompleteness(updated.fidelity?.completeness ?? null);
      setStructureLoading(true);
      setEvidenceLoading(true);
      try {
        const [struct, evidence] = await Promise.all([
          getSourceStructure(projectId),
          getEvidenceReport(projectId),
        ]);
        setSourceStructure(struct);
        setEvidenceVisibility(evidence);
      } finally {
        setStructureLoading(false);
        setEvidenceLoading(false);
      }
      await regenerateLanding(projectId);
      try {
        setLandingPreview(await getLanding(projectId));
      } catch {
        setLandingPreview(null);
      }
    } catch (err) {
      setError(formatApiError(err, "Не удалось перепарсить ленд"));
    } finally {
      setReparsing(false);
    }
  }

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      const updated = await updateContract(projectId, {
        blocks,
        style,
        presentation_style: presentationStyle || null,
      });
      setContract(updated);
      await regenerateLanding(projectId);
    } catch (err) {
      setError(formatApiError(err, "Ошибка сохранения"));
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <p className="text-muted-foreground">Загрузка контракта…</p>;
  if (!contract && error) return <p className="text-red-600">{error}</p>;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Редактор ленда</h1>
          <p className="text-sm text-muted-foreground flex flex-wrap items-center gap-2">
            <span>
              Проект {projectId.slice(0, 8)}… · v{contract?.version ?? 1}
            </span>
            <PiiBadge
              hasPii={enrichmentInfo?.pii_detected ?? false}
              count={enrichmentInfo?.pii_redaction_count}
            />
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button onClick={handleGenerateLanding} disabled={generating}>
            {generating ? "Формирование…" : "Сформировать ленд"}
          </Button>
          <Link href={buildPreviewHref(projectId, presentationStyle || undefined)}>
            <Button variant="outline" type="button">
              Preview
            </Button>
          </Link>
          <Button variant="ghost" onClick={() => setShowAdvanced((v) => !v)} type="button">
            {showAdvanced ? "Скрыть advanced" : "Advanced"}
          </Button>
          {showAdvanced && (
            <>
              <Button variant="outline" onClick={handleEnrich} disabled={enriching}>
                {enriching ? "LLM…" : "Улучшить через LLM"}
              </Button>
              <Button variant="outline" onClick={handleSave} disabled={saving}>
                {saving ? "Сохранение…" : "Сохранить"}
              </Button>
            </>
          )}
        </div>
      </div>

      <PiiDashboard projectId={projectId} />

      <ContractQualityPanel
        fidelity={contract?.fidelity}
        completeness={completeness}
        onReparse={handleReparse}
        reparsing={reparsing}
      />

      <ProjectSourceStatusPanel
        contract={contract}
        evidence={evidenceVisibility}
        landing={landingPreview}
      />

      <SourceStructurePanel
        report={sourceStructure}
        evidence={evidenceVisibility}
        loading={structureLoading}
        evidenceLoading={evidenceLoading}
        parserMode={contract?.fidelity?.parser_mode}
      />

      <TeamReviewPanel
        projectId={projectId}
        onUpdated={load}
        advancedDiagnostics={evidenceVisibility?.advanced_diagnostics_enabled ?? false}
      />

      {contract?.fidelity?.team_structured &&
        contract.fidelity.team_structured.length > 0 && (
          <TeamCardsPanel members={contract.fidelity.team_structured} />
        )}

      {showAdvanced && (
        <DomainDebugPanel
          projectId={projectId}
          semanticDomain={semanticInfo?.intelligence_domain_profile?.primary_domain ?? semanticInfo?.domain}
        />
      )}

      {showAdvanced && semanticInfo && (
        <>
          <SemanticDebugPanel semantic={semanticInfo} message={semanticMessage} />
          <ArchitectureDebugPanel topology={semanticInfo.architecture} />
        </>
      )}

      {(enrichMessage || enrichmentInfo) && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">LLM enrichment</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-muted-foreground">
            {enrichMessage && <p>{enrichMessage}</p>}
            {enrichmentInfo?.cloud_unsafe_warning && (
              <p className="text-red-700 font-medium">
                CLOUD_UNSAFE_DEV: в облако мог уйти немаскированный текст.
              </p>
            )}
            {enrichmentInfo?.pii_detected && enrichmentInfo.cloud_payload_safe && (
              <p className="text-emerald-800">
                Cloud payload: обезличен (redaction + rehydration).
              </p>
            )}
            {enrichmentInfo?.fallback_used && (
              <p className="text-amber-700">
                LLM disabled or fallback — используется эвристический контракт.
              </p>
            )}
            {enrichmentInfo && (
              <>
                <p>
                  Provider: {enrichmentInfo.provider} · LLM enabled:{" "}
                  {enrichmentInfo.llm_enabled ? "yes" : "no"}
                </p>
                <p>
                  Confidence: title {enrichmentInfo.confidence.title.toFixed(2)}, client{" "}
                  {enrichmentInfo.confidence.client.toFixed(2)}, team{" "}
                  {enrichmentInfo.confidence.team.toFixed(2)}
                </p>
                {enrichmentInfo.missing_fields.length > 0 && (
                  <p>Missing: {enrichmentInfo.missing_fields.join(", ")}</p>
                )}
                {enrichmentInfo.assumptions.length > 0 && (
                  <p>Assumptions: {enrichmentInfo.assumptions.join("; ")}</p>
                )}
                {enrichmentInfo.source_trace.length > 0 && (
                  <ul className="list-disc pl-5">
                    {enrichmentInfo.source_trace.slice(0, 5).map((t) => (
                      <li key={`${t.field}-${t.filename}`}>
                        {t.field} ← {t.filename ?? "?"}: {t.evidence.slice(0, 80)}
                      </li>
                    ))}
                  </ul>
                )}
              </>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Стиль</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {STYLES.map((s) => (
              <button
                key={s.value}
                type="button"
                onClick={() => setStyle(s.value)}
                className={`rounded-md border px-3 py-1.5 text-sm ${
                  style === s.value
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-input hover:bg-muted"
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>
          <div>
            <p className="mb-2 text-sm text-muted-foreground">Preview / export profile</p>
            <div className="flex flex-wrap gap-2">
              {PRESENTATION_PROFILES.map((s) => (
                <button
                  key={s.value || "auto"}
                  type="button"
                  onClick={() => setPresentationStyle(s.value)}
                  className={`rounded-md border px-3 py-1.5 text-sm ${
                    presentationStyle === s.value
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-input hover:bg-muted"
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="grid gap-4">
        {blocks.map((block, index) => (
          <Card key={block.key}>
            <CardHeader>
              <CardTitle className="text-lg">{block.title}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Label htmlFor={`block-${block.key}`}>Содержание</Label>
              <Textarea
                id={`block-${block.key}`}
                value={block.content}
                onChange={(e) => updateBlock(index, e.target.value)}
                rows={4}
              />
              {block.bullets.length > 0 && (
                <ul className="list-disc pl-5 text-sm text-muted-foreground">
                  {block.bullets.map((b) => (
                    <li key={b}>{b}</li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

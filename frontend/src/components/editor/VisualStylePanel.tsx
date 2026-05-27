"use client";

import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  DEFAULT_STYLE_CONFIG,
  buildStyleConfigFromEditor,
} from "@/lib/styleConfig";
import { parseStyleIntent } from "@/lib/styleIntent";
import type { LandingStyleConfig, LandingStyleProfile } from "@/lib/types";

const PROFILES: { value: LandingStyleProfile; label: string }[] = [
  { value: "university_platform", label: "University / Платформа УИИ" },
  { value: "minimal", label: "Minimal" },
  { value: "corporate", label: "Corporate" },
  { value: "tech", label: "Tech" },
  { value: "bold", label: "Bold" },
  { value: "custom", label: "Custom" },
];

const AUTO_PROFILE = { value: "auto" as const, label: "Auto (по контракту)" };

interface Props {
  value: LandingStyleConfig;
  onChange: (config: LandingStyleConfig) => void;
  onApply: (config: LandingStyleConfig) => void;
}

function tokenSummary(tokens: ReturnType<typeof parseStyleIntent>): string[] {
  const lines: string[] = [];
  if (tokens.color_scheme) lines.push(`theme: ${tokens.color_scheme}`);
  if (tokens.accent) lines.push(`accent: ${tokens.accent}`);
  if (tokens.motion) lines.push(`motion: ${tokens.motion}`);
  if (tokens.hero_mode) lines.push(`hero: ${tokens.hero_mode}`);
  return lines;
}

export function VisualStylePanel({ value, onChange, onApply }: Props) {
  const [customPrompt, setCustomPrompt] = useState(
    value.custom_style_prompt ?? "",
  );
  const [useAuto, setUseAuto] = useState(false);

  const previewTokens = useMemo(() => {
    if (value.profile === "custom") {
      return parseStyleIntent(customPrompt);
    }
    return value.theme_tokens ?? DEFAULT_STYLE_CONFIG.theme_tokens!;
  }, [value.profile, value.theme_tokens, customPrompt]);

  const summary = tokenSummary(previewTokens);

  function selectProfile(profile: LandingStyleProfile | "auto") {
    if (profile === "auto") {
      setUseAuto(true);
      onChange({ ...DEFAULT_STYLE_CONFIG });
      return;
    }
    setUseAuto(false);
    const next = buildStyleConfigFromEditor(profile, customPrompt);
    onChange(next);
  }

  function handleApply() {
    const next =
      value.profile === "custom"
        ? buildStyleConfigFromEditor("custom", customPrompt, previewTokens)
        : value;
    onApply(next);
  }

  function handleReset() {
    setUseAuto(false);
    setCustomPrompt("");
    const reset = { ...DEFAULT_STYLE_CONFIG };
    onChange(reset);
    onApply(reset);
  }

  const activeProfile = useAuto ? "auto" : value.profile;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Визуальный стиль</CardTitle>
        <p className="text-sm text-muted-foreground">
          По умолчанию — University / Платформа УИИ. Custom описание преобразуется
          только в безопасные параметры темы.
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <p className="mb-2 text-sm font-medium">Основной стиль</p>
          <div className="flex flex-wrap gap-2">
            {[...PROFILES, AUTO_PROFILE].map((s) => (
              <button
                key={s.value}
                type="button"
                onClick={() =>
                  selectProfile(s.value as LandingStyleProfile | "auto")
                }
                className={`rounded-md border px-3 py-1.5 text-sm ${
                  activeProfile === s.value
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-input hover:bg-muted"
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>

        {value.profile === "custom" && !useAuto && (
          <div className="space-y-2">
            <Label htmlFor="custom-style-prompt">Опишите стиль лендинга</Label>
            <Textarea
              id="custom-style-prompt"
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              rows={3}
              placeholder="Например: тёмный технологичный стиль с синим акцентом, 3D-карточками и плавной анимацией"
            />
          </div>
        )}

        {summary.length > 0 && (
          <div className="rounded-md border border-dashed border-input bg-muted/40 px-3 py-2 text-xs text-muted-foreground">
            <p className="mb-1 font-medium text-foreground">Preview tokens</p>
            <ul className="list-disc pl-4">
              {summary.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="flex flex-wrap gap-2">
          <Button type="button" size="sm" onClick={handleApply}>
            Применить стиль
          </Button>
          <Button type="button" size="sm" variant="outline" onClick={handleReset}>
            Сбросить к University
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

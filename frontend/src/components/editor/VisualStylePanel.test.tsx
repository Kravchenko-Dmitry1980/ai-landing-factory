import React from "react";
import { describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { VisualStylePanel } from "./VisualStylePanel";
import { DEFAULT_STYLE_CONFIG } from "@/lib/styleConfig";

describe("VisualStylePanel", () => {
  it("shows University selected by default", () => {
    const html = renderToStaticMarkup(
      <VisualStylePanel
        value={DEFAULT_STYLE_CONFIG}
        onChange={vi.fn()}
        onApply={vi.fn()}
      />,
    );
    expect(html).toContain("University / Платформа УИИ");
    expect(html).toContain("Сбросить к University");
  });

  it("shows custom textarea only for custom profile", () => {
    const custom = renderToStaticMarkup(
      <VisualStylePanel
        value={{ profile: "custom", custom_style_prompt: "" }}
        onChange={vi.fn()}
        onApply={vi.fn()}
      />,
    );
    expect(custom).toContain("Опишите стиль лендинга");

    const minimal = renderToStaticMarkup(
      <VisualStylePanel
        value={{ profile: "minimal" }}
        onChange={vi.fn()}
        onApply={vi.fn()}
      />,
    );
    expect(minimal).not.toContain('id="custom-style-prompt"');
  });
});

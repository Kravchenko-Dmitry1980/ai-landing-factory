# Stage D — Interactive Rendering & Style Engine

## Architecture

```
LandingContract + GeneratedLanding
        ↓
  contract_adapter (typed sections)
        ↓
  StyleProfile + LayoutPreset
        ↓
  Section Registry → Section Components
        ↓
  InteractiveRenderer (+ MotionLayer)
        ↓
  Enterprise Landing Preview
```

**LLM never generates HTML/JSX.** It only fills `LandingContract` blocks. The renderer is deterministic and typed.

## Directories

| Path | Role |
|------|------|
| `src/design/` | Tokens, typography, motion, themes, style profiles, layout presets, hallmark rules |
| `src/rendering/` | Adapter, registry, factory, renderer |
| `src/sections/` | One React component per section type |
| `src/components/diagrams|cards|grids|typography/` | Shared UI primitives |
| `src/components/dev/DevRenderPanel.tsx` | Dev overlay |

## Style profiles

`enterprise` · `medical` · `ai_research` · `education` · `analytics`

Each defines colors (CSS vars), spacing, typography, motion intensity, diagram preference.

Legacy backend `style` maps via `legacyStyleToProfile()`:
- `minimal` / `corporate` → `enterprise`
- `tech` → `ai_research`
- `bold` → `analytics`

## Layout presets

`architecture_first` (default) · `dashboard` · `research_report` · `enterprise_overview` · `technical_system`

Controls section order, widths, grid logic, diagram placement.

Override per project in browser: `localStorage` key `alf_render_config_{projectId}` or dev panel (`?dev=1`).

Backend optional: `presentation_style: "layout:technical_system"`.

## Section registry

| Contract block key | Section type |
|--------------------|--------------|
| tagline | hero |
| essence, purpose | essence |
| inputs, outputs | architecture (merged) |
| tasks | modules (tabs) |
| results | metrics (Recharts) |
| tech_stack | stack (explorer) |
| team | team (expandable) |
| outlook | roadmap (timeline) |
| — | footer (meta) |

### Add a new section

1. Add `SectionType` in `rendering/types.ts`
2. Map block keys in `rendering/contract_adapter.ts`
3. Create `sections/MySection/MySection.tsx`
4. Register in `rendering/registry.ts`
5. Add to preset `sectionOrder` in `design/layout_presets.ts`

## Hallmark quality gate

`design/hallmark_rules.ts` — static rules (no runtime Hallmark dependency).

Violations log to console in dev; listed in dev panel.

## Motion

`design/motion.ts` — subtle reveal only. No parallax, blobs, or infinite loops.

## Dev panel

Open preview with `?dev=1`:

- Switch style profile / layout preset
- Section tree (source block keys)
- Hallmark warnings
- Render timing (ms)

## Tests

```powershell
cd c:\Dima\Projects\CURSOR\Lend\frontend
npm install
npm test
```

## Export

Preview uses `print:` Tailwind classes and semantic HTML for future PDF / static export.

Legacy backend HTML export remains available from the toolbar.

## Configuration example

```json
{
  "profileId": "medical",
  "layoutId": "research_report"
}
```

Saved automatically when changed in dev panel.

# WOW Hero — Real 3D Scene (React Three Fiber) · Stage P.7.1

## What changed

The WOW preview hero was rebuilt from a styled dark block with a small embed
into a **dominant interactive 3D scene** (React Three Fiber) with an accessible
HTML overlay. It is an **isolated, opt-in addition** to the frontend preview —
standard mode, simple mode, and the backend export contracts are untouched.

### New preview modes (opt-in via `?mode=`)

| `?mode=`   | Behaviour                                                        |
|------------|------------------------------------------------------------------|
| *(absent)* | `standard` — classic interactive renderer only (**unchanged**).  |
| `wow`      | Premium R3F hero, **lite** intensity (fewer particles, calmer).  |
| `wow3d`    | Full immersive R3F hero (more particles, full motion, parallax). |

A "Режим preview" switcher in `LandingPreview` toggles between them. The WOW
hero is rendered **above** the normal landing; the standard content stays in a
`#wow-landing-content` anchor that the hero CTA scrolls to.

## Scene concept

AI Cockpit + Holographic Project Map hybrid:

- **Central data core** — emissive icosahedron + wireframe shell, slow rotation.
- **Floating module nodes** — one per project module/subsystem, colored by kind
  (data / ml / service / ui / storage), orbiting the core with gentle float.
- **Animated data-flow beams** — lines from core to each node with traveling
  pulse spheres (the "pipeline flow").
- **Particle field + grid floor** — subtle depth and volumetric feel.
- **Mouse parallax** — the whole rig eases toward the pointer.

All geometry is **procedural** (no models, no textures, no asset downloads). The
layout is **deterministic** — seeded from the project title + structure — so the
same project always renders the same scene.

## Interactive vs export (no fake parity)

- **Interactive preview (web):** the new premium R3F hero (this stage).
- **HTML export (`/export?mode=wow` and `+ wow_3d_runtime=aframe`):**
  **unchanged** in this stage. The exported WOW HTML is still the existing
  self-contained CSS + optional vendored A-Frame build.

Rationale: a full R3F runtime cannot be embedded into a single self-contained,
CDN-free HTML file without shipping a bundled three.js build, which is out of
scope here and risks the export-safety guarantees. The interactive preview is
the premium artifact; the export remains the portable/offline artifact. This is
stated explicitly rather than claiming parity.

## Data mapping (`frontend/src/lib/wowHeroMapping.ts`)

| Scene element        | Source                                                            |
|----------------------|-------------------------------------------------------------------|
| Central identity     | `contract.title` → hero block title → fallback `"AI-проект"`      |
| Subtitle             | `semantic.narrative.system` → essence block → quote → first block |
| Chips                | `contract.client` / `timeline` / `lead`                           |
| Metric cards         | extracted impact numbers (`37 000+ постов`) + derived counts      |
| Derived metrics      | modules / team / stack / tasks / results counts                   |
| 3D nodes             | `fidelity.modules` → semantic architecture nodes → stack groups   |
| Pipeline rail        | 5-stage keyword detection (mirrors backend `wow_pipeline.py`)     |

Mapping mirrors the backend WOW metric/pipeline logic so the preview stays
semantically consistent with the export. It degrades gracefully: with no
contract it still yields a title, ≥4 metrics, a generic 5-stage pipeline, and a
generic node set.

## Dependencies added (frontend only)

```
three@^0.171.0
@react-three/fiber@^9.6.1
@react-three/drei@^10.7.7
@types/three@^0.171.0   (dev)
```

- Backend `requirements` are **not** touched → simple-mode dependency audit
  still passes (no OCR/VLM/torch added).
- `three` is loaded **client-only** via `next/dynamic({ ssr: false })`, so it is
  fetched only when a user actually opens `?mode=wow|wow3d`.

## Performance guardrails

- Procedural geometry only; no models/textures/asset fetches.
- Particle count capped (full = 260, lite = 90); ≤ 8 nodes / beams.
- `dpr` clamped to `[1, 1.8]`.
- Reduced-motion: animations frozen and `frameloop="demand"` (renders once).
- WebGL probe → static CSS fallback if unavailable (never a blank hero).

## Accessibility / UX

- Per modern-web-guidance, HTML is overlaid on the canvas with CSS (HTML-in-
  Canvas is not Baseline) → text stays selectable, translatable, screen-reader
  readable, and the CTA stays a real clickable `<a>`.
- SSR / first paint renders the **static fallback** (text present for LCP / no-JS).
- `prefers-reduced-motion` respected in both CSS and the 3D scene.
- Mobile: node labels hidden, reduced min-height.

## Files

**Added**
- `frontend/src/lib/wowHeroMode.ts` — mode parsing, intensity, WebGL / reduced-motion probes
- `frontend/src/lib/wowHeroMapping.ts` — deterministic contract → scene mapping
- `frontend/src/components/wow/WowHeroCanvas.tsx` — orchestrator (capability + overlay)
- `frontend/src/components/wow/WowHeroR3F.tsx` — `<Canvas>` wrapper (dynamic, ssr:false)
- `frontend/src/components/wow/WowHeroScene.tsx` — the 3D scene
- `frontend/src/components/wow/WowHeroOverlay.tsx` — HTML overlay (title/CTA/metrics)
- `frontend/src/components/wow/WowMetricStrip.tsx` — metric cards
- `frontend/src/components/wow/WowHeroFallback.tsx` — static premium fallback
- `frontend/src/components/wow/wow-hero.css` — hero styling
- Tests: `frontend/src/lib/wowHeroMode.test.ts`, `wowHeroMapping.test.ts`,
  `frontend/src/components/wow/WowHero.test.tsx`

**Modified**
- `frontend/src/components/preview/LandingPreview.tsx` — preview-mode switcher +
  conditional WOW hero + `#wow-landing-content` anchor
- `frontend/package.json` / lockfile — 3D dependencies

**Untouched**
- All backend files (export, WOW exporter, A-Frame, showcase, PII).
- Standard preview/export path.

## Manual QA

```powershell
# from repo root, with backend + frontend running (run.ps1 / start_dev.ps1)
# 1. standard (must be unchanged)
start http://localhost:3000/preview/<projectId>
# 2. premium WOW (lite)
start "http://localhost:3000/preview/<projectId>?mode=wow"
# 3. full immersive
start "http://localhost:3000/preview/<projectId>?mode=wow3d"
```

Check:
1. Standard mode looks exactly as before (no WOW hero).
2. WOW / WOW3D show a dominant 3D core with module nodes, beams, particles.
3. Title, chips, metrics, CTA are readable and the CTA scrolls to the landing.
4. DevTools console: zero errors.
5. OS reduced-motion on → scene is frozen but composed (no blank hero).
6. Disable WebGL → static fallback with backdrop + constellation still renders.

```powershell
# automated
cd frontend; npm test; npm run build
cd backend; ..\.venv\Scripts\python.exe scripts\audit_simple_dependencies.py
```

## Known limitations

- HTML export parity is intentionally partial (interactive ≠ export); documented above.
- Node labels live in the overlay/fallback (not as 3D text) to avoid CDN font
  loads from `troika-three-text`/drei `Text`.
- The `?mode=` flag is the lightweight smoke marker; no separate debug page added.

## Follow-up: portable interactive export (Stage P.7.2)

The export-parity gap above is closed by **Interactive WOW Bundle (P.7.2)** — a
standalone React/R3F app (`frontend/src/wow-bundle`) bundled with esbuild into a
portable ZIP that runs the real 3D hero offline (no backend / dev server / CDN).
It is a **separate** export mode and does not change standard / WOW HTML export.
See [WOW_INTERACTIVE_BUNDLE_P7_2.md](WOW_INTERACTIVE_BUNDLE_P7_2.md).

# Visual Acceptance — university_platform (Preview ≈ Export)

Structural + visual sanity regression gate for **Эндокринология+** and similar university-style landings.  
Not pixel-perfect — validates content parity, style markers, and section presence.

## Target project

| Field | Value |
|-------|-------|
| `project_id` | `55a98f90-73fc-4d26-a477-3c974a0cbeed` |
| Preview | http://localhost:3000/preview/55a98f90-73fc-4d26-a477-3c974a0cbeed?style=university_platform&fidelity_debug=1 |
| Export | http://127.0.0.1:8001/api/v1/projects/55a98f90-73fc-4d26-a477-3c974a0cbeed/export/html?theme=university_platform |

## Automated smoke

```powershell
cd C:\Dima\Projects\CURSOR\Lend\frontend
node scripts\smoke-visual-acceptance.mjs --project-id 55a98f90-73fc-4d26-a477-3c974a0cbeed
```

Optional screenshots (requires Playwright installed separately):

```powershell
node scripts\smoke-visual-acceptance.mjs --project-id 55a98f90-73fc-4d26-a477-3c974a0cbeed --screenshots
```

Outputs to `frontend/artifacts/visual/`:

- `preview-university-desktop.png` (1440px)
- `preview-university-mobile.png` (390px)
- `export-university-desktop.png`
- `export-university-mobile.png`

### CLI options

| Flag | Default | Description |
|------|---------|-------------|
| `--project-id` | Endocrinology UUID | Project to validate |
| `--frontend-url` | `http://localhost:3000` | Next.js dev server |
| `--backend-url` | `http://127.0.0.1:8001` | FastAPI base (no `/api/v1`) |
| `--style` | `university_platform` | Preview style / export theme |
| `--screenshots` | off | Playwright screenshots if available |

### Exit codes

- `0` — `preview_ok`, `export_ok`, `parity_ok`
- `1` — any critical check failed

## What the script checks

### Preview

- HTTP 200
- Title **Эндокринология+**
- Modules: **GlaucoLogic**, **Copilot врача**, **VitaCalc**
- Sections: **Команда проекта**, **Используемый технологический стек**
- University style markers (`university_platform`, `--alf-bg`, purple accent)
- No duplicate bullet glyphs (`● ●`)

Preview is client-rendered. Resolution order:

1. Static HTML fetch
2. Playwright DOM (if `playwright` package available)
3. Contract API fallback (fidelity fields) with warning

### Export

- HTTP 200 + JSON `html` field
- Same major content as preview
- CSS/HTML markers: `team-card`, `stack-tag`, `module-card`, `max-width: 1200px`
- Purple accent `#7C3AED` / `#8B5CF6`
- Light background markers
- **Must not** contain dark enterprise fallback:
  - `--bg: #0f1419`
  - `--surface: #1a2332`
  - `max-width: 720px`
  - `Project Landing`
- ≥3 module cards, ≥15 team cards, ≥5 stack tags

### Parity

- All three modules present in both surfaces
- Team + stack section titles in both
- Hero title in both

## Expected visual markers

| Area | Preview | Export |
|------|---------|--------|
| Hero | White/light bg, dark heading | `.hero`, light `--bg` |
| Modules | 3 cards, type badges | `.module-card` × 3 |
| Stack | Grouped categories + tags | `.stack-group`, `.stack-tag` |
| Team | Card grid, collapsed contributions | `.team-card` × 15+ |
| Layout | `max-w-7xl` Tailwind | `max-width: 1200px` |
| Accent | `#7C3AED` / `--alf-accent` | `#7C3AED` / `--accent` |

## Manual browser checklist

1. **Backend**

   ```powershell
   cd C:\Dima\Projects\CURSOR\Lend\backend
   ..\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8001
   ```

2. **Frontend**

   ```powershell
   cd C:\Dima\Projects\CURSOR\Lend\frontend
   npm run dev
   ```

3. **Preview** — open preview URL above. Verify:
   - White theme, black headings, purple accents
   - Modules as cards (GlaucoLogic, Copilot врача, VitaCalc)
   - Team as cards (not plain text wall)
   - Stack grouped by category
   - Architecture graph visible (if topology exists)
   - No empty core sections
   - DevTools Console: zero errors

4. **Export** — open export URL in browser. Verify:
   - Same content family, static HTML
   - Readable at desktop and 360px width (no horizontal scroll)
   - No debug panels

5. **Compare** side-by-side: same sections, same modules/team/stack, light university style.

## Acceptable differences

| OK | Not OK |
|----|--------|
| Preview interactive expand/collapse on team | Dark theme in university style |
| Export static HTML | Empty team or stack |
| Preview `fidelity_debug` panel when query set | Missing modules |
| Export simplified architecture block | Duplicate `● ●` bullets |
| Preview framer-motion reveals | Legacy 720px / Project Landing fallback |

## Related gates

```powershell
# Backend export smoke
cd C:\Dima\Projects\CURSOR\Lend\backend
..\.venv\Scripts\python.exe scripts\smoke_university_export.py --project-id 55a98f90-73fc-4d26-a477-3c974a0cbeed

# Endocrinology acceptance
..\.venv\Scripts\python.exe scripts\smoke_endocrinology_acceptance.py --project-id 55a98f90-73fc-4d26-a477-3c974a0cbeed

# Frontend unit tests
cd C:\Dima\Projects\CURSOR\Lend\frontend
npm test
```

## Pure functions (unit-tested)

`src/lib/visual_acceptance.ts`:

- `detectRequiredMarkers(html, surface)`
- `detectDarkThemeMarkers(html)`
- `comparePreviewExportMarkers(previewHtml, exportHtml)`
- `validatePreviewHtml` / `validateExportHtml`

Run: `npm test -- visual_acceptance`

## Known limitations

- Preview DOM checks need running frontend + backend; Playwright improves fidelity but is optional.
- Contract API fallback validates **content** parity, not rendered CSS/Tailwind.
- No pixel diff / Percy / Chromatic integration (by design).
- Mobile overflow (360px) requires manual check or `--screenshots` mobile captures.

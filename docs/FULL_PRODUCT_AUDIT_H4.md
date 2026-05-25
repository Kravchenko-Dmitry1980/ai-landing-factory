# FULL PRODUCT AUDIT — Stage H.4

Date: 2026-05-25  
Scope: Multi-file upload, live E2E path, team recovery, export integrity

## 1. Upload UI behavior

| Check | Result |
|-------|--------|
| `<input type="file" multiple>` | **PASS** — attribute present in `UploadForm.tsx` |
| State holds multiple files | **PASS** (after fix) — `File[]` + merge on each selection |
| Visible file list before upload | **FIXED** — shows count, filenames, per-file remove |
| Empty submit blocked | **PASS** — button disabled when `files.length === 0` + validation |
| UX hint about team in DOCX | **ADDED** — helper text under file input |

**Prior issue:** Browser file input shows only the last filename in native control; without a custom list users believed only one file was selected (screenshot: single `Proekt-Intellektualnyj-agregator.pptx`).

## 2. Upload API contract

| Check | Result |
|-------|--------|
| Endpoint | `POST /api/v1/projects/{id}/upload` |
| Parameter | `files: list[UploadFile] = File(...)` |
| Backward compatible single file | **YES** — one-element list works |
| Optional description | `Form(description=...)` → `description.txt` |

File: `backend/app/api/v1/uploads.py`

## 3. Multi-file FormData verification

| Hypothesis | Verdict |
|------------|---------|
| H1 input without multiple | **FALSE** — already had `multiple` |
| H2 stores only one File | **FALSE** — was `FileList`, now explicit `File[]` |
| H3 sends only first file | **FALSE** — `files.forEach(f => form.append("files", f))` |
| H4 backend accepts files[] but UI doesn't | **FALSE** — both sides aligned |

Frontend: `frontend/src/lib/api.ts` lines 77–78  
Unit test: `UploadForm.test.tsx` → `appendFilesToFormData` / `uploadMaterials`

## 4. Backend extraction verification

Pipeline: `ContentPipeline.run_after_upload` → `DispatcherExtractionService.extract` iterates **all** uploads from file store.

| Check | Result |
|-------|--------|
| One `FileExtraction` per uploaded file | **PASS** |
| Multi-file in one project | **PASS** — `list_files` loop |

## 5. Evidence assembly verification

| Check | Result |
|-------|--------|
| `parser_mode=multi_source_assembly` for PPTX+DOCX | **PASS** (corpus + service tests) |
| `source_count == uploaded files` | **PASS** when all files uploaded |
| `evidence_count > 0` | **PASS** for Indlab golden |

## 6. Team extraction verification

| Scenario | team_structured | Evidence coverage |
|----------|-----------------|-------------------|
| PPTX + DOCX (Indlab) | ≥ 10 members | **strong** |
| PPTX only | 0 or partial | **missing/weak** |
| Corpus smoke | PASS | offline snapshots |

**Root cause for missing team in live Indlab export:** only presentation uploaded; team lives in `02_landing.docx` (H9 **CONFIRMED**).

## 7. Generate / preview / export verification

| Step | Behavior |
|------|----------|
| Upload | auto `build_and_save` + `generate` |
| Reparse | `reparse_structured` + **regenerates landing** (`contracts.py:63`) |
| Export | `StyledHtmlExporter._render_from_contract` uses `fidelity.team_structured` |
| Team in HTML | `section#team` + `team-card` when valid members exist |

Export does **not** hide team when contract has valid `team_structured` (verified in `test_live_multifile_team_pipeline.py`).

## 8. Live UI vs corpus discrepancy

| Path | Files | Team in export |
|------|-------|----------------|
| Corpus smoke | pptx.txt + docx.txt snapshots | YES |
| Live UI (reported) | pptx only | NO |
| Live HTTP smoke (new) | temp pptx + docx from snapshots | YES |

**H6 CONFIRMED:** assembly works in corpus but failed in live when only one source uploaded.  
**H7/H8 NOT REPRODUCED:** reparse triggers regeneration; export reads current contract.

## 9. Bugs found

1. **UX:** No visible multi-file list → user uploads single PPTX (severity: high, product)
2. **Documentation:** No explicit multi-file + team guidance (severity: medium)
3. **QA gap:** No live HTTP multifile smoke in `check_all.ps1` (severity: medium)

Not bugs (already correct):

- Backend multi-file API
- Frontend FormData multi append
- Export team rendering logic
- Strict team validation / false positive guard

## 10. Fixes applied

| Area | Change |
|------|--------|
| `UploadForm.tsx` | File list UI, remove file, merge selections, hints |
| `uploadFormUtils.ts` | Testable pure helpers |
| `UploadForm.test.tsx` | multiple attribute, FormData, validation |
| `smoke_live_multifile_project.py` | Live HTTP E2E with corpus snapshot → binary |
| `test_live_multifile_team_pipeline.py` | Service-level multifile + team + export |
| `check_all.ps1` | `Live multifile smoke` step, `-SkipLiveMultifileSmoke` |
| `README_RUN.md` | Multi-file project upload section |

## 11. Regression tests

```powershell
# Backend
cd backend
..\.venv\Scripts\python.exe -m pytest tests\test_live_multifile_team_pipeline.py tests\test_team_visibility_pipeline.py -q
..\.venv\Scripts\python.exe scripts\smoke_corpus.py
..\.venv\Scripts\python.exe scripts\smoke_team_export.py --project indlab_telegram_news

# Frontend
cd frontend
npm test

# Live (backend running)
cd backend
..\.venv\Scripts\python.exe scripts\smoke_live_multifile_project.py --corpus-project indlab_telegram_news

# Full QA
cd ..
.\scripts\check_all.ps1 -SkipFrontendBuild
```

## 12. Remaining limitations

1. Binary PPTX/DOCX not stored in git — live smoke builds temp files from `.txt` snapshots.
2. Playwright UI E2E not added (no Playwright in frontend deps); covered by unit + HTTP smoke.
3. Existing projects with stale single-file extraction require manual re-upload or reparse after adding DOCX.
4. OCR for image-only team slides not supported (non-goal).

---

**Acceptance:** Live path proven via `smoke_live_multifile_project.py`: upload ≥2 files → `source_count≥2` → team strong → `section#team` in university export without forbidden false names.

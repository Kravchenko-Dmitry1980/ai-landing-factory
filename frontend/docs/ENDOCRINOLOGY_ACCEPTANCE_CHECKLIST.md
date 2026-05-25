# Endocrinology+ — Manual Acceptance Checklist

## Prerequisites

1. Backend: `cd backend` → `..\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8001`
2. Frontend: `cd frontend` → `npm run dev` → http://localhost:3000
3. PII env: `..\.venv\Scripts\python.exe scripts\check_pii_env.py` → `PII env OK`

## Upload & PII

1. Create project or open existing (`55a98f90-73fc-4d26-a477-3c974a0cbeed`).
2. Upload `Ленд проекта Эндокринология.docx`.
3. **PII panel**: `has_pii=true`, redaction count > 0, no raw FIO in public report.
4. **Safe cloud payload** (Advanced): placeholders `[PERSON_*]`, `[EMAIL_*]` — no raw values.

## Contract Quality

5. Open **Editor** → **Contract Quality Panel**:
   - Parser mode: `structured`
   - Completeness ≥ 85
6. **Source Structure Panel**: sections essence, tasks, purpose, team, tech_stack with lengths.
7. If score < 70: click **«Перепарсить как готовый ленд»**.

## Expected contract fields

| Field | Expected |
|-------|----------|
| title | Эндокринология+ |
| client | Древаль (or redacted placeholder in cloud) |
| timeline | февраль – апрель 2026 |
| lead | Кравченко |
| modules | GlaucoLogic, Copilot врача, VitaCalc |
| tasks | ≥ 8 bullets |
| purpose | ≥ 5 bullets |
| team | ≥ 15 cards (collapsed) |
| tech_stack | grouped: AI/LLM, Backend, Frontend, Data, Infra |

## Generate & Preview

8. Click **«Сформировать ленд»**.
9. Open **Preview**:
   - Hero: title + client + timeline
   - Modules tab: GlaucoLogic / Copilot / VitaCalc by name
   - Stack: grouped categories
   - Team: cards, not empty textarea
   - Architecture graph visible

## Debug panels

10. Preview URL params (optional):
    - `?domain_debug=1` — medical_ai domain, archetypes, patterns
    - `?architecture_debug=1` — nodes ≥ 5, edges ≥ 3
    - `?semantic_debug=1` — section plan, confidence

## Export

11. Download HTML export (`GET /api/v1/projects/{id}/export/html` or UI).
12. Verify:
    - Dark styled layout, `max-width: 1200px`
    - Module cards, team cards, grouped stack
    - **Not** plain `max-width:720px` fallback

## Compare with Word

13. Side-by-side with source DOCX:
    - All major sections present
    - No empty «Для чего», «Выходные данные», «Перспектива»
    - Team majority preserved
    - No invented marketing text

## Automated smoke

```powershell
cd C:\Dima\Projects\CURSOR\Lend\backend
..\.venv\Scripts\python.exe scripts\smoke_endocrinology_acceptance.py --project-id 55a98f90-73fc-4d26-a477-3c974a0cbeed
```

Expected: `ENDOCRINOLOGY ACCEPTANCE PASSED`

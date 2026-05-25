# endocrinology

Golden-кейс: **один LandingContract** для проекта «Эндокринология+» (GlaucoLogic, AI Copilot, VitaCalc).

## Источники (`sources/`)

| Файл | Оригинал |
|------|----------|
| `01_landing.docx` | `Ленд проекта Эндокринология.docx` |
| `02_glaucologic_presentation.pptx` | `GlaucoLogic_ОКТ_аналитика.pptx` |
| `03_ai_copilot_presentation.pptx` | `AI Copilot_final3.pptx` |

В git — `*.txt` снимки. Бинарники — только локально.

Примечание: `AI Copilot_final3.pptx` — слайды без извлекаемого текста (картинки); содержание Copilot берётся из `01_landing.docx`.

## Ожидания

Title содержит «Эндокринология», высокий completeness, модуль GlaucoLogic.

## Проверка

```powershell
cd C:\Dima\Projects\CURSOR\Lend\backend
..\.venv\Scripts\python.exe scripts\smoke_corpus.py --project endocrinology
```

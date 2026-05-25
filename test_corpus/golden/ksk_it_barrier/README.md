# ksk_it_barrier

Golden-кейс: **один LandingContract** для проекта КСК ИТ — CV-система автоматического открытия шлагбаума по госномеру.

## Источники (`sources/`)

| Файл | Оригинал |
|------|----------|
| `01_presentation.pptx` | `КСК_ИТ.pptx` (локально; в задании — `КСК_ИТ(2).pptx`) |

В git — `01_presentation.pptx.txt`. Бинарник `.pptx` — только локально.

## Ожидания

`expected_parser_mode: project_presentation`, модули детекции/номеров, стек YOLOv8, Streamlit, CVAT, Roboflow.

## Проверка

```powershell
cd C:\Dima\Projects\CURSOR\Lend\backend
..\.venv\Scripts\python.exe scripts\smoke_corpus.py --project ksk_it_barrier
```

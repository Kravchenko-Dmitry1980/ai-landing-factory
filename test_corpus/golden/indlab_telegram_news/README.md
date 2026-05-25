# indlab_telegram_news

Golden-кейс: **один LandingContract** для проекта Индлаб — интеллектуальный агрегатор новостных потоков Telegram.

## Источники (`sources/`)

| Файл | Оригинал |
|------|----------|
| `01_presentation.pptx` | `Proekt-Intellektualnyj-agregator.pptx` |
| `02_landing.docx` | `Ленд Индлаб (1).docx` |

В git хранятся `*.pptx.txt` / `*.docx.txt` снимки. Бинарники — только локально (см. `.gitignore`).

## Ожидания

`expected_parser_mode: multi_source_assembly`, title содержит «Интеллектуальный агрегатор» или «Telegram», стек: Qdrant, BERTopic, Neo4j.

## Проверка

```powershell
cd C:\Dima\Projects\CURSOR\Lend\backend
..\.venv\Scripts\python.exe scripts\smoke_corpus.py --project indlab_telegram_news
```

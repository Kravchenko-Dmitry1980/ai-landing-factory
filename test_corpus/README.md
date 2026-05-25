# Test corpus — AI Landing Factory

Регрессионный корпус для проверки сборки **одного** `LandingContract` из проектных материалов.

## Главное правило

**Одна папка = один проект = один LandingContract.**

Внутри папки проекта лежат все исходники этого проекта и один файл ожиданий `expected_contract.yml`. Скрипт `backend/scripts/smoke_corpus.py` читает `sources/`, прогоняет pipeline (`ContractBuilderService.build`) и сверяет результат с `expected_contract.yml`.

## Структура

```
test_corpus/
├── README.md
├── expected_contract.yml.template   # шаблон полей ожиданий
├── golden/                          # эталонные кейсы (должны проходить CI/smoke)
│   ├── endocrinology/
│   ├── indlab_telegram_news/
│   └── ksk_it_barrier/
├── messy/                             # намеренно «грязные» / неполные материалы
└── regression/                        # новые кейсы перед переносом в golden
```

### Папка golden-проекта

```
golden/<project_slug>/
├── expected_contract.yml    # критерии приёмки
└── sources/                 # материалы проекта (см. ниже)
    ├── README.md
    └── …
```

## Материалы в `sources/` (без тяжёлых бинарников в git)

В репозитории по умолчанию лежат **лёгкие текстовые снимки** извлечённого текста, а не бинарные PPTX/DOCX/PDF:

| Файл в git | Интерпретация скриптом |
|------------|-------------------------|
| `*.pptx.txt` | текст как после PPTX extractor, `file_type=pptx` |
| `*.docx.txt` | текст как после DOCX extractor, `file_type=docx` |
| `*.pdf.txt` | текст как после PDF extractor, `file_type=pdf` |
| `*.txt`, `*.md` | вспомогательные заметки, `file_type=txt` |

Имя для сборки: `presentation.pptx.txt` → файл `presentation.pptx`, тип `pptx`.

### Локальные бинарники (не в git)

При необходимости положите реальные файлы в `sources/` локально:

- `presentation.pptx`, `spec.docx`, `report.pdf`, …

Они перечислены в `.gitignore`. Перед smoke с бинарниками нужен прогон через backend extractor (или замена `.txt`-снимков).

## Шаблон `expected_contract.yml`

Скопируйте `expected_contract.yml.template` и заполните:

| Поле | Назначение |
|------|------------|
| `title_contains` | список подстрок; хотя бы одна должна быть в `contract.title` |
| `min_completeness` | минимальный `fidelity.completeness.score` |
| `must_have_stack` | технологии в `fidelity.tech_stack_grouped` (регистронезависимо) |
| `must_have_modules` | подстроки в `fidelity.modules[].name` |
| `min_modules` | минимум модулей (0 = не проверять) |
| `must_have_team` | подстроки в team (пусто = не проверять) |
| `expected_parser_mode` | `structured`, `project_presentation`, `multi_source_assembly`, `heuristic` |
| `reject_essence_slide1_only` | essence не должна быть дампом только Slide 1 |
| `reject_generic_title` | title не «Проект» / «Презентация» / … |

## Golden-кейсы (в репозитории)

| Проект | Назначение |
|--------|------------|
| `endocrinology` | ready landing DOCX → `structured`, высокий completeness |
| `ksk_it_barrier` | PPTX CV/шлагбаум → `project_presentation` или лучший режим, модули + стек |
| `indlab_telegram_news` | PPTX + DOCX Индлаб/Telegram → `multi_source_assembly`, title + Qdrant/BERTopic/Neo4j |

## Запуск smoke

```powershell
cd C:\Dima\Projects\CURSOR\Lend\backend
..\.venv\Scripts\python.exe scripts\smoke_corpus.py
..\.venv\Scripts\python.exe scripts\smoke_corpus.py --project endocrinology
..\.venv\Scripts\python.exe scripts\smoke_corpus.py --corpus-dir ..\test_corpus\golden
```

Код выхода: `0` — все проверенные проекты прошли, `1` — есть ошибки.

## Каталоги `messy/` и `regression/`

- **messy/** — неполные/шумные загрузки; ожидания опциональны, кейсы могут падать намеренно.
- **regression/** — черновики новых проектов; после стабилизации переносите в `golden/`.

## Как добавить новый проект

1. **Создайте папку** — `golden/<project_slug>/` (черновик можно начать в `regression/<project_slug>/`).
2. **Положите материалы** в `sources/`:
   - в git: лёгкие снимки `presentation.pptx.txt`, `spec.docx.txt`, `notes.txt`;
   - локально (не в git): реальные `.pptx` / `.docx` / `.pdf` при необходимости.
3. **Заполните** `expected_contract.yml` (скопируйте из `expected_contract.yml.template`).
4. **Проверьте один проект:**

```powershell
cd C:\Dima\Projects\CURSOR\Lend\backend
..\.venv\Scripts\python.exe scripts\smoke_corpus.py --project <project_slug>
```

5. После стабилизации перенесите из `regression/` в `golden/` и прогоните полный корпус:

```powershell
..\.venv\Scripts\python.exe scripts\smoke_corpus.py
```

Шаг **Test corpus smoke** в `.\scripts\check_all.ps1` использует тот же скрипт для всех папок в `test_corpus/golden/`.

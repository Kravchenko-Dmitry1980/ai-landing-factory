# Showcase Registry & Project CRUD (Stage P.6)

## 1. Purpose

До P.6 витрина существовала только как разовый экспорт (service/script/API),
но не как пользовательский объект. Stage P.6 делает витрину **управляемым
объектом продукта**: её можно создать, наполнить проектами/лендами, отредактировать
и переоткрыть позже, а затем экспортировать в HTML или портативный ZIP.

Пользователь может:

1. создать витрину;
2. добавить проекты/ленды вручную;
3. прикрепить `demo_url` (например, из AI Google Studio);
4. указать `landing_url` или выбрать существующий generated landing (при выборе
   из лендов `landing_url` подставляется как `/preview/{project_id}`);
5. выбрать layout/theme;
6. отредактировать список проектов (правка / удаление / порядок);
7. экспортировать HTML или ZIP;
8. повторно открыть витрину и продолжить редактирование.

Showcase **не** входит в Simple Gate и не меняет обычный landing export.

## 2. Data model

`backend/app/services/showcase/showcase_schema.py`:

```text
ShowcaseProject {
  id, title, description,
  landing_url?, demo_url?, demo_label?,
  category?, tags[], accent?, source_project_id?,
  order_index
}

ShowcaseConfig {
  id, title, subtitle?, organization?,
  layout: gallery_arc | grid_hall | circle_booths,
  mode:   web3d | vr_ready,
  theme:  university | tech | dark,
  projects: ShowcaseProject[],
  created_at, updated_at
}
```

`id` / `created_at` / `updated_at` в `ShowcaseConfig` опциональны на уровне
схемы (чтобы stateless export-эндпоинты P.5 продолжали принимать «голые»
конфиги), но реестр всегда их заполняет.

Request-контракты: `ShowcaseCreateRequest`, `ShowcaseUpdateRequest`,
`ShowcaseProjectCreateRequest`, `ShowcaseProjectUpdateRequest`,
`ShowcaseReorderRequest`. List-вью: `ShowcaseSummary`. Кандидаты лендов:
`LandingCandidate`.

## 3. Storage

Простое JSON-хранилище без БД:

```text
backend/data/showcases/
  {showcase_id}.json   # один файл = одна витрина (сериализованный ShowcaseConfig)
```

Сервис: `backend/app/services/showcase/showcase_registry.py`
(`ShowcaseRegistry`). Особенности:

- атомарная запись (temp-файл + `os.replace`);
- директория создаётся при необходимости;
- стабильные UUID-идентификаторы;
- `updated_at` обновляется при каждой мутации;
- проекты всегда отдаются в порядке `order_index`;
- `base_dir` можно переопределить (используется в тестах/смоуке — temp dir).

Методы: `list_showcases`, `list_summaries`, `get_showcase`, `create_showcase`,
`update_showcase`, `delete_showcase`, `add_project`, `update_project`,
`delete_project`, `reorder_projects`.

## 4. API endpoints

Реестр (`/api/v1/showcases`):

| Метод | Путь | Тело | Ответ |
|---|---|---|---|
| GET | `/showcases` | — | `ShowcaseSummary[]` |
| POST | `/showcases` | `ShowcaseCreateRequest` | `ShowcaseConfig` (201) |
| GET | `/showcases/{id}` | — | `ShowcaseConfig` |
| PATCH | `/showcases/{id}` | `ShowcaseUpdateRequest` | `ShowcaseConfig` |
| DELETE | `/showcases/{id}` | — | `{ "deleted": true }` |
| POST | `/showcases/{id}/projects` | `ShowcaseProjectCreateRequest` | `ShowcaseConfig` |
| PATCH | `/showcases/{id}/projects/{pid}` | `ShowcaseProjectUpdateRequest` | `ShowcaseConfig` |
| DELETE | `/showcases/{id}/projects/{pid}` | — | `ShowcaseConfig` |
| POST | `/showcases/{id}/projects/reorder` | `{ ordered_ids: [...] }` | `ShowcaseConfig` |
| POST | `/showcases/{id}/export-html` | — | `ShowcaseExportResult` (HTML) |
| POST | `/showcases/{id}/export-zip` | — | `application/zip` |

Существующие ленды (`/api/v1/showcase`):

| Метод | Путь | Ответ |
|---|---|---|
| GET | `/showcase/landing-candidates` | `LandingCandidate[]` |

`LandingCandidate { project_id, title, client?, description?, preview_url, export_html_url, landing_url, export_available, updated_at? }`
строится из текущего project registry + LandingContract (title/client/lead).

- `preview_url` — относительный маршрут фронтенда `/preview/{project_id}`;
- `export_html_url` — backend HTML export `/api/v1/projects/{project_id}/export/html`;
- `landing_url` — по умолчанию равен `preview_url` (подставляется автоматически при
  «Добавить из лендов»);
- `demo_url` (AI Google Studio и т.п.) пользователь добавляет вручную в форме.

## 5. UI flow

- `frontend/src/app/showcase/page.tsx` → список витрин (`ShowcaseList`):
  название, число проектов, `updated_at`, кнопки **Открыть / Экспорт ZIP /
  Удалить**, поле **Создать витрину**.
- `frontend/src/app/showcase/[id]/page.tsx` → редактор (`ShowcaseBuilder`).

Компоненты (`frontend/src/components/showcase/`):

```text
ShowcaseList.tsx           — список + создание/удаление/быстрый ZIP
ShowcaseBuilder.tsx        — редактор витрины (registry-backed)
ShowcaseSettingsPanel.tsx  — title/subtitle/organization/layout/theme
ShowcaseProjectForm.tsx    — добавление/правка проекта вручную
ShowcaseProjectCard.tsx    — карточка проекта + ↑/↓ + edit/delete
LandingCandidatePicker.tsx — «Добавить из лендов»
ShowcaseExportActions.tsx  — Экспорт HTML / Экспорт ZIP
```

API-клиент: `frontend/src/lib/showcaseApi.ts`; типы и чистые helper'ы —
`frontend/src/lib/showcase.ts` (`moveProjectInList`, `candidateToProjectRequest`,
`validateProjectRequest`, …). Порядок меняется простыми кнопками ↑/↓ — без
drag-and-drop зависимостей.

## 6. Export HTML / ZIP from saved showcase

Сохранённый `ShowcaseConfig` передаётся в существующие экспортёры:

- `ShowcaseHtmlExporter().export(config)` → self-contained HTML (A-Frame + 2D fallback);
- `build_showcase_zip(config)` → `ai-showcase.zip` (`showcase.html` + локальный
  vendored A-Frame runtime + LICENSE).

Layout/theme берутся из сохранённого конфига, порядок карточек — из
`order_index`, число карточек в экспорте совпадает с сохранённым.

## 7. Safety

- URL'ы (`demo_url`, `landing_url`) проходят `sanitize_url`: разрешены
  `http(s)://` и относительные пути; отклоняются `javascript:`, `data:`,
  `vbscript:`, `file:`, `blob:`, `about:` → сохраняется `None`.
- Caps: `title` ≤ 200, `description` ≤ 1000, тегов ≤ 10, длина тега ≤ 40.
- Пустой `title` отклоняется (валидация Pydantic / формы).
- Весь текст экранируется экспортёром (`escape_text`) перед вставкой в HTML.
- ZIP использует только hardcoded entry names (нет path traversal,
  пользовательских имён файлов, `.env`, логов, backend/data).

## 8. Release checks

- Backend: `tests/test_showcase_registry.py`, `tests/test_showcase_api.py`
  (плюс уже существующие `test_showcase_exporter.py`,
  `test_showcase_zip_exporter.py`). Все тесты пишут в temp-директорию.
- Frontend: `src/lib/showcase.test.ts`, `src/lib/showcaseApi.test.ts`,
  `src/components/showcase/ShowcaseBuilder.test.tsx`.
- Smoke: `backend/scripts/smoke_showcase_registry.py` (изолированный temp
  storage, очищается сам).

**Full gate (`release_check.ps1 -Full`):**

- `smoke_showcase_zip_export.py` — portable ZIP bundle;
- `smoke_showcase_registry.py` — registry lifecycle (create → projects → export → delete);
- pytest: `test_showcase_zip_exporter.py`, `test_showcase_exporter.py`,
  `test_showcase_registry.py`, `test_showcase_api.py`.

Simple Gate **не** запускает registry smoke. Флаг `-SkipShowcaseSmoke` пропускает
и ZIP smoke, и registry smoke, и связанные pytest.

```powershell
cd C:\Dima\Projects\CURSOR\_uat\ai-landing-factory-fresh\backend
..\.venv\Scripts\python.exe -m pytest tests\test_showcase_registry.py tests\test_showcase_api.py -q
..\.venv\Scripts\python.exe scripts\smoke_showcase_registry.py
```

## 9. Limitations

- Хранилище — JSON-файлы, без БД, без конкурентных транзакций (атомарная
  запись на файл, но без блокировок между процессами).
- Нет авторизации/мультипользовательского доступа.
- `landing_url` для кандидатов лендов подставляется автоматически как
  `/preview/{project_id}`; пользователь может отредактировать перед сохранением.
- Нет drag-and-drop, нет полноценного 3D scene editor, нет R3F/SuperSplat,
  нет multiplayer (см. NON-GOALS).
- Showcase не обязателен в Simple Gate и не влияет на `run.ps1`.

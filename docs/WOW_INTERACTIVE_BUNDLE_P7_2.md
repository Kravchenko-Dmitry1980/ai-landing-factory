# Interactive WOW Bundle (Stage P.7.2)

Переносимый интерактивный демо-артефакт: ZIP с настоящей React/R3F-версией
лендинга, который открывается на любом компьютере офлайн.

## 1. Зачем нужен bundle

P.7.1 добавил «вау» только в интерактивный preview (`/preview/{id}?mode=wow`).
Экспортируемый HTML оставался degraded-вариантом (CSS / A-Frame). Руководителю
или заказчику нужен переносимый артефакт с **настоящим интерактивным R3F-hero**,
который можно распаковать и показать как экспонат без backend, dev-сервера и
интернета.

Interactive WOW Bundle закрывает этот разрыв: один ZIP → двойной клик по
`index.html` → полноценный интерактивный WOW-лендинг.

## 2. Чем отличается от standard / wow HTML

| Режим экспорта | Что это | Интерактив | Зависимости |
|----------------|---------|------------|-------------|
| `standard HTML` | Обычная статическая страница лендинга | CSS-hover | нет |
| `wow HTML` | Self-contained / degraded WOW HTML | CSS / опц. A-Frame | vendored A-Frame |
| `wow HTML + 3D` | WOW HTML + A-Frame runtime | A-Frame-сцена | vendored A-Frame |
| **`Interactive WOW ZIP`** | **Standalone React/R3F app + данные** | **полноценный R3F hero** | всё встроено в bundle |

Interactive WOW Bundle — **отдельный** режим. Он **не заменяет** standard / wow
HTML и **не является** значением по умолчанию.

## 3. Состав ZIP

```
ai-wow-landing-{project_id}.zip
├── index.html                 # точка входа (+ встроенный JSON данных проекта)
├── assets/
│   ├── wow-app.js             # React + R3F + three, всё в одном IIFE-файле
│   └── wow-app.css            # стили bundle (если собраны)
├── data/
│   └── landing-contract.json  # данные проекта (WowBundleData) для отладки
└── README_DEMO.txt            # инструкция для получателя
```

Данные проекта встроены прямо в `index.html`:

```html
<script id="wow-data" type="application/json">{ ... WowBundleData ... }</script>
```

Bundle читает их через `JSON.parse` без `fetch`, поэтому всё работает с
`file://`.

## 4. Как собрать frontend bundle

Сборка идёт через **esbuild** (уже доступен в проекте) в один IIFE-файл — без
ограничений ES-модулей, что делает артефакт `file://`-friendly.

```powershell
cd C:\Dima\Projects\CURSOR\_uat\ai-landing-factory-fresh\frontend
npm run build:wow-bundle
```

Результат:

```
frontend/dist-wow/assets/wow-app.js   (~1 MB: React + R3F + three)
frontend/dist-wow/assets/wow-app.css
```

Из корня доступен враппер:

```powershell
.\scripts\build_wow_bundle.ps1            # только сборка
.\scripts\build_wow_bundle.ps1 -Smoke     # сборка + backend smoke
```

> `dist-wow/` в `.gitignore` — это генерируемый артефакт, в репозиторий не
> коммитится. Backend export требует, чтобы bundle был собран заранее.

## 5. Как экспортировать

**Через UI:** на странице preview панель «Экспорт для демонстрации» →
кнопка **«Экспорт интерактивного WOW ZIP»**.

**Через API:**

```
GET /api/v1/projects/{project_id}/export/wow-bundle
    ?demo_url=https://...        (optional)
    &showcase_url=/showcase/...  (optional)
```

Ответ: `application/zip`, `Content-Disposition: attachment;
filename="ai-wow-landing-{project_id}.zip"`.

Если frontend bundle не собран — endpoint вернёт **503** с инструкцией
`cd frontend && npm run build:wow-bundle`.

## 6. Как открыть

1. Распаковать архив целиком (со всеми папками `assets/` и `data/`).
2. Открыть `index.html` двойным кликом.

## 7. Ограничения file://

Большинство браузеров открывают bundle напрямую (`file://`), потому что JS
собран как один IIFE-файл (без ES-module loading) и данные встроены inline (без
`fetch`). Если конкретный браузер всё же блокирует локальный запуск — поднять
простой статический сервер из папки с `index.html`:

```powershell
python -m http.server 8080
# затем открыть http://localhost:8080/
```

## 8. Безопасность

- весь текст экранируется (`escape_text`) на границе встраивания в HTML;
- встроенный JSON экранирует `<`, `>`, `&` → `\uXXXX` (невозможен `</script>`-breakout и инъекция разметки);
- `demo_url` / `showcase_url` проходят `sanitize_url` — `javascript:`, `data:`, `file:` и т.п. отклоняются;
- никаких внешних скриптов / CDN / удалённых ассетов;
- bundle-app трактует все значения как текст и никогда не интерпретирует их как HTML;
- ZIP: фиксированные имена, проверка на path traversal и абсолютные пути; в архив не попадают `.env`, логи, backend-данные.

## 9. Release checks

P.7.2 **не добавляется** в Simple Gate и по умолчанию **не входит** в Full Gate
(сборка bundle требует frontend toolchain). Проверки — ручные:

```powershell
# 1. Сборка bundle
cd frontend
npm run build:wow-bundle
npm test
npm run build

# 2. Backend
cd ..\backend
..\.venv\Scripts\python.exe -m pytest tests/test_wow_bundle_exporter.py -q
..\.venv\Scripts\python.exe scripts\smoke_wow_bundle_export.py
```

`release_check.ps1` (Simple и Full) проходит без изменений — bundle от него не
зависит.

## 10. Будущее

- опциональный флаг `-RunWowBundleSmoke` для Full Gate, когда сборка стабильна на CI/Windows;
- static hosting bundle (R2 / Pages) одной командой;
- poster/preview fallback (статический скриншот hero) для окружений без WebGL;
- `landing_url` в `links` и кросс-ссылки между bundle и витриной.

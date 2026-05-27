# Stage P.2 — Fresh Clone User Acceptance Test

Ручной release gate для проверки пути **нового пользователя** без dev-артефактов (`.venv`, `node_modules`, `.env`, кэши OCR).

## Предусловия

| Инструмент | Минимум |
|------------|---------|
| Python | 3.12+ |
| Node.js | 20+ |
| npm | 10+ |
| Git | 2.40+ |
| PowerShell | 5.1+ |

Проверка:

```powershell
python --version
node --version
npm --version
git --version
```

Если чего-то нет — установите вручную. Скрипты **не** ставят Python/Node автоматически.

## Fresh clone (отдельная папка)

**Не** используйте рабочую dev-папку `Lend` для UAT.

```powershell
cd C:\Dima\Projects\CURSOR
mkdir _uat -Force
cd _uat

git clone https://github.com/Kravchenko-Dmitry1980/ai-landing-factory.git ai-landing-factory-fresh
cd ai-landing-factory-fresh

.\run.ps1
```

В другом терминале (после старта серверов):

```powershell
cd C:\Dima\Projects\CURSOR\_uat\ai-landing-factory-fresh
.\scripts\uat_fresh_clone_check.ps1
```

Остановка:

```powershell
.\scripts\stop_dev.ps1
```

## Что проверяет `uat_fresh_clone_check.ps1`

1. `backend/scripts/audit_simple_dependencies.py` — запрещённые OCR/VLM пакеты отсутствуют в `.venv`.
2. `backend/scripts/smoke_product_mode_runtime.py` — `/health`, `PRODUCT_MODE=simple`, OCR/VLM off.
3. `backend/scripts/smoke_user_flow_simple.py` — upload → contract → generate → HTML export.
4. `scripts/smoke_frontend_simple.ps1` — HTTP 200 на frontend (опционально, без Playwright).

## Ожидания `run.ps1`

- Создаёт `.venv` и ставит **только** `backend/requirements.txt` (base).
- Ставит frontend (`npm install`) при отсутствии `node_modules`.
- Создаёт `backend\.env` из `.env.example` с `PRODUCT_MODE=simple`.
- Запускает backend + frontend, пишет `.runtime/ports.json`.
- Печатает URL и команду остановки.

## Запрещено в simple UAT

- Tesseract, EasyOCR, PaddleOCR, Paddle, Surya
- Ollama, LM Studio, vLLM
- CUDA / локальные модели для OCR/VLM
- `PRODUCT_MODE=advanced` без явного запроса

## Отчёт

После прогона заполните или сгенерируйте:

- `UAT_FRESH_CLONE_REPORT.md` в корне fresh clone (шаблон создаётся при UAT-прогоне).

## Связь с CI

Fresh clone UAT **не** входит в `check_all.ps1` по умолчанию. Это ручной gate перед релизом.

Для dev-репозитория:

```powershell
.\scripts\check_all.ps1 -Simple
```

## Локальный clone (если GitHub отстаёт)

Только для внутренней проверки до push:

```powershell
git clone file:///C:/Dima/Projects/CURSOR/Lend ai-landing-factory-fresh
```

В отчёте укажите источник clone и commit hash.

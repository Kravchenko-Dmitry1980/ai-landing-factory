# VR/AR Showcase — Demo Checklist

Пошаговый сценарий для демонстрации руководству и optional QA перед показом.

## 1. Pre-demo setup

```powershell
cd C:\Dima\Projects\CURSOR\_uat\ai-landing-factory-fresh
git pull
.\scripts\stop_dev.ps1
.\run.ps1 -SkipInstall
```

Проверьте URL из `.runtime/ports.json` (обычно `http://localhost:3000` и `http://127.0.0.1:8001`).

Optional release gate (без browser smoke):

```powershell
.\scripts\release_check.ps1 -Full -SkipFrontendBuild
```

Optional browser/API smoke (dev-серверы должны быть запущены):

```powershell
.\scripts\smoke_showcase_browser.ps1
# или строго:
.\scripts\smoke_showcase_browser.ps1 -RequireBrowser
# через release gate:
.\scripts\release_check.ps1 -Full -RunBrowserSmoke -SkipFrontendBuild
```

Browser smoke **не** входит в Simple Gate и **не** запускается в Full Gate по умолчанию.

## 2. Create showcase

1. Откройте `{frontend_url}/showcase`.
2. Убедитесь в заголовке **VR/AR витрина проектов**.
3. Нажмите **Создать витрину AI-проектов УИИ**.
4. Откроется `/showcase/{id}` с prefilled:
   - title: «Витрина AI-проектов УИИ»;
   - layout `gallery_arc`, theme `tech`, mode `vr_ready`.

## 3. Add projects

### Из готового ленда

1. **Добавить из лендов** → выберите проект.
2. Проверьте autofill `landing_url` = `/preview/{project_id}`.
3. Badge **Подставлено автоматически**.
4. Добавьте `demo_url` (например `https://aistudio.google.com/`).
5. Сохраните.

### Вручную

1. **Добавить проект вручную**.
2. Заполните title, description, `landing_url`, `demo_url`, category.
3. Сохраните.

## 4. Check readiness

Панель **Готовность к демонстрации** должна показать:

- число проектов > 0;
- demo-ссылки добавлены (или warning, если нет);
- **ZIP-экспорт доступен**;
- **3D runtime (A-Frame) включён в ZIP**;
- **Demo-ссылки требуют интернет**.

Карточки проектов:

- **Ленд:** `/preview/...`
- **Демо:** AI Google Studio / внешняя ссылка (или «Demo-ссылка не добавлена»).

## 5. Export

1. **Экспорт ZIP для офлайн-демо** (не экспортируйте пустую витрину).
2. Распакуйте ZIP.
3. Откройте `showcase.html` в браузере.
4. Проверьте:
   - 3D-стенд A-Frame (офлайн);
   - 2D fallback;
   - карточки проектов;
   - demo-ссылки открываются только с интернетом.

## 6. Troubleshooting

| Проблема | Что проверить |
|----------|----------------|
| Страница не открывается | `.runtime/ports.json`, `.\run.ps1`, firewall |
| API ошибки | backend `.env`, `PRODUCT_MODE=simple`, uvicorn log |
| Нет лендов в picker | есть ли projects в registry, backend running |
| landing_url пустой | выберите «Добавить из лендов», не только manual |
| Demo не открывается | интернет, блокировка внешних URL |
| ZIP пустой / ошибка | добавьте проекты; vendored A-Frame: `frontend/public/vendor/aframe/` |
| 3D не грузится offline | открывайте `showcase.html` из распакованной папки, не `file://` без vendor |
| Browser smoke SKIP | поднимите dev-серверы; `-RequireBrowser` для strict fail |

## Related

- [SHOWCASE_REGISTRY_P6.md](SHOWCASE_REGISTRY_P6.md) — registry API и release checks
- [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) — Simple / Full gates
- [VR_AR_SHOWCASE_P5.md](VR_AR_SHOWCASE_P5.md) — ZIP/HTML export

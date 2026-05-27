# Frontend Style System (P.3)

Управляемая система визуальных стилей для preview и static HTML export в `PRODUCT_MODE=simple`.

## Profiles (presets)

| Profile | Renderer profile | Export theme |
|---------|------------------|--------------|
| `university_platform` (default) | `university_platform` | `university_platform` |
| `minimal` | `enterprise` | `enterprise_dark` |
| `corporate` | `enterprise` | `enterprise_dark` |
| `tech` | `ai_research` | `enterprise_dark` |
| `bold` | `analytics` | `enterprise_dark` |
| `custom` | `university_platform` + tokens | `university_platform` + token CSS |

**Auto** в UI — вторичный режим: не переопределяет сохранённый контракт.

## Contract: `LandingStyleConfig`

```json
{
  "profile": "university_platform",
  "custom_style_prompt": "optional user text",
  "theme_tokens": {
    "color_scheme": "light",
    "accent": "violet",
    "radius": "soft",
    "density": "normal",
    "motion": "subtle",
    "hero_mode": "classic"
  }
}
```

- `custom_style_prompt` — только ввод пользователя (не попадает в HTML).
- `theme_tokens` — контролируемый выход парсера `parseStyleIntent()` (`frontend/src/lib/styleIntent.ts`).

## Custom style intent

Детерминированный парсер без LLM:

- «тёмный» → `color_scheme: dark`
- «синий» → `accent: blue`
- «3d / интерактив» → `hero_mode: future_3d`, `motion: expressive`
- Попытки raw CSS/`<script>` → сброс к university defaults

## Rendering

- CSS variables: `--alf-bg`, `--alf-surface`, `--alf-accent`, `--alf-radius`, `--alf-gap`, `--alf-motion-duration`, `--alf-hero-mode`
- Preview: `InteractiveRenderer` + section components
- Export: backend `StyledHtmlExporter` + optional `style_config` query JSON

## Future 3D hook

`hero_mode: future_3d` добавляет CSS-only pseudo-3D hero (gradient + perspective).  
Комментарии в коде помечают точку для будущего Three.js/WebGL — **без** зависимостей в simple mode.

## Interactive foundation (export-safe)

Self-contained CSS в экспорте:

- `scroll-behavior: smooth`
- hover lift на cards / module cards / team cards
- hover на stack tags
- `<details>` для длинного вклада команды (без JS)

## API

- `PATCH /contract` — поле `style_config`
- `GET /export/html?theme=university_platform&style_config={json}`

## Tests

```powershell
cd frontend
npm test
```

```powershell
.\scripts\smoke_style_export.ps1
```

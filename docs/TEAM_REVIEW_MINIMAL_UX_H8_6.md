# Team Review Minimal UX (Stage H.8.6)

## Продуктовое решение

После H.8.5 public export стал безопасным, но редактор терял OCR-кандидатов.  
H.8.6 вводит режим **auto-fill first, review only if needed**:

- Редактор показывает полную draft-команду (verified + probable + needs_review).
- Public export по умолчанию — только verified (`safe_public` / `draft_auto`).
- Пользователь может одним действием принять всё или отредактировать текстом.

**Нет per-person approve/reject** — только bulk actions + textarea.

## Режимы публикации

| Mode | Редактор | Public export |
|------|----------|---------------|
| `draft_auto` | verified + probable + needs_review | verified only |
| `safe_public` | verified only | verified only |
| `user_accepted` | all accepted | verified + accepted_by_user |
| `manual_edited` | user text | manual team as-is |

## UI в редакторе

Блок «Команда проекта»:

- Сводка: найдено / уверенно / требуют проверки
- Предупреждение OCR
- Кнопки: **Принять всё** · **Оставить только уверенных** · **Редактировать текстом**

Формат редактируемого текста:

```
Игорь Колесов — тимлид
- вклад 1

# OCR требует проверки:
Наденда Глазунова — аналитика
```

## API

```
GET  /api/v1/projects/{id}/team-review
POST /api/v1/projects/{id}/team-review/bulk-action
POST /api/v1/projects/{id}/team-review/manual-text
```

## Indlab flow

1. OCR slide 25 → draft_auto с 7 кандидатами, 6 needs_review
2. Public export без bad names
3. «Принять всё» → user_accepted → export включает принятых
4. «Редактировать текстом» → исправить ФИО → manual_edited → export с corrected names

## Smoke

```powershell
cd C:\Dima\Projects\CURSOR\Lend\backend
..\.venv\Scripts\python.exe scripts\smoke_team_review_flow.py
```

## Limitations

- Нет per-candidate toggle в UI
- Reparse сбрасывает bulk/manual decisions (кроме явного reset)
- Manual approval audit trail — следующий этап

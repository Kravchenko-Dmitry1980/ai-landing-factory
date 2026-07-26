# Static demo deploy (Mode A)

Самый безопасный публичный режим: nginx отдаёт готовый demo pack.
Backend / AI / upload / generate **не используются**.

## Что нужно

1. Собрать архив локально:

```powershell
.\scripts\build_static_demo_release.ps1
```

Артефакт: `.runtime/release/ai-landing-static-demo.zip`

2. На сервере:

```bash
sudo mkdir -p /var/www/ai-landing-demo
sudo unzip -o ai-landing-static-demo.zip -d /var/www/ai-landing-demo
sudo cp deploy/nginx/ai-landing-static.conf /etc/nginx/sites-available/ai-landing-static.conf
# заменить YOUR_DOMAIN
sudo ln -sfn /etc/nginx/sites-available/ai-landing-static.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

## Содержимое релиза

| Path | Content |
|---|---|
| `index.html` | Навигация по демо |
| `wow/` | Interactive WOW landing (unpacked) |
| `standard/` | Standard HTML landing |
| `static-wow/` | Static WOW HTML |
| `showcase/` | VR/AR showcase (unpacked) |
| `README_DEMO_RU.md` | Demo instructions |
| `CHECKS/` | Checklists / reports |

## Ограничения

- Нет API, нет редактора, нет генерации
- Только готовые артефакты из `demo_release_*`
- Ideal first step before full systemd deploy

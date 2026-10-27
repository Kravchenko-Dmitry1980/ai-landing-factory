# Памятка: выкладка Ленда на 195.209.218.235

Готовые команды для сервера `landing-factory.neural-university.ru`.

**Сервер.** Общий с проектом Романа (`hr-platform`, `127.0.0.1:5173`). Порты 80/443 держит nginx сервера, его ведёт Никита. Docker Compose v5, команды пишутся через пробел: `docker compose`.

**Где живёт Ленд.** В `/opt/ai-landing-factory`. Слушает только `127.0.0.1:18080`, а также `18443`, `18001`, `13000` на том же `127.0.0.1`.

Подробности и объяснения — в [README_DOCKER_FIRST_DEPLOY.md](README_DOCKER_FIRST_DEPLOY.md). Здесь только команды по порядку.

Релиз: `lend-release-20261026_1146-bd31e2e.zip`, коммит `bd31e2e`.

Ваш логин на сервере в командах ниже обозначен `ЛОГИН`.

## 1. Залить архив (PowerShell на рабочем компьютере)

```powershell
scp "D:\AI\Projects\Active\Lend\ai-landing-factory\.runtime\release\lend-release-20261026_1146-bd31e2e.zip" ЛОГИН@195.209.218.235:/tmp/
ssh ЛОГИН@195.209.218.235
```

Всё дальше — на сервере.

## 2. Проверить сервер

```bash
sudo -v && echo "sudo есть"
sudo docker compose version
sudo docker buildx version
sudo ss -ltnp | grep -E ':(18080|18443|18001|13000) ' || echo "порты Ленда свободны"
df -h /
curl -sS -o /dev/null -w 'Docker Hub: %{http_code}\n' https://registry-1.docker.io/v2/
command -v unzip || sudo apt-get install -y unzip
```

Должно быть:

- `sudo есть`;
- версия compose и buildx;
- `порты Ленда свободны`;
- свободно больше 10 ГБ;
- `Docker Hub: 401`. Это нормально: сервер дотянулся до интернета.

## 3. Распаковать релиз

```bash
RELEASE_ID=20261026_1146-bd31e2e
sudo mkdir -p /opt/ai-landing-factory/releases/${RELEASE_ID} /opt/ai-landing-factory/shared /opt/ai-landing-factory/backups
sudo unzip -q /tmp/lend-release-${RELEASE_ID}.zip -d /opt/ai-landing-factory/releases/${RELEASE_ID}
sudo ln -sfn /opt/ai-landing-factory/releases/${RELEASE_ID} /opt/ai-landing-factory/current
ls /opt/ai-landing-factory/current/deploy/docker
```

Должно быть видно `docker-compose.yml`, `backup.sh`, `healthcheck.sh` и папку `gateway`.

## 4. Настройки (один раз)

Файл целиком, уже заполненный для этого сервера:

```bash
sudo tee /opt/ai-landing-factory/shared/lend.env > /dev/null <<'EOF'
# Lend on 195.209.218.235, behind the server's nginx (landing-factory.neural-university.ru).
COMPOSE_PROJECT_NAME=lend

# The server's nginx sends landing-factory.neural-university.ru to 127.0.0.1:18080.
LEND_GATEWAY=proxy
LEND_BIND=127.0.0.1
LEND_HTTP_PORT=18080
LEND_HTTPS_PORT=18443
LEND_BACKEND_LOCAL_PORT=18001
LEND_FRONTEND_LOCAL_PORT=13000
LEND_DOMAIN=landing-factory.neural-university.ru
BACKEND_CORS_ORIGINS=https://landing-factory.neural-university.ru

SESSION_COOKIE_SECURE=auto
SESSION_TTL_DAYS=30
INVITE_TTL_DAYS=7

LEND_DATA_VOLUME=lend_data

# No GPU, no external AI.
PRODUCT_MODE=simple
LLM_ENABLED=false
LLM_PROVIDER=mock
SEMANTIC_GENERATION_ENABLED=true
SEMANTIC_USE_LLM=false
DOMAIN_INTELLIGENCE_ENABLED=true
DOMAIN_USE_LLM=false
PRIVACY_MODE=hybrid_safe
ENABLE_PII_DETECTION=true
PII_ENCRYPT_REPORTS=false
PII_REPORT_TTL_HOURS=72
OCR_ENABLED=false
VLM_ENABLED=false
EOF
sudo chmod 600 /opt/ai-landing-factory/shared/lend.env
sudo ln -sfn /opt/ai-landing-factory/shared/lend.env /opt/ai-landing-factory/current/deploy/docker/.env
```

## 5. Собрать и запустить

Сборка идёт 10–20 минут. Если SSH оборвётся, сборка тоже прервётся, поэтому лучше запускать её внутри `tmux` (`sudo apt-get install -y tmux`, затем `tmux`; вернуться после обрыва — `tmux attach`).

```bash
cd /opt/ai-landing-factory/current/deploy/docker
sudo docker compose build
sudo docker compose up -d --renew-anon-volumes
```

Предупреждение `the attribute version is obsolete` безвредно.

Подождите минуту и проверьте:

```bash
sudo bash ./healthcheck.sh
```

Пока Никита не подключил сайт Ленда в nginx, в выводе будет:

- **OK** у контейнеров, базы и `Through the gateway`;
- **FAIL** у `backend health` и `sign-in page` в блоке `Through the shared proxy`: `SSL certificate problem` или чужой сертификат;
- **WARN** `no backups yet`.

Так и должно быть до шага 8. Другие `FAIL` — повод смотреть журнал: `sudo docker compose logs --tail=100 backend`.

## 6. Первый администратор

```bash
sudo docker compose exec backend python -m app.cli create-admin --login d.kravchenko --name "Дмитрий Кравченко"
```

Пароль спросит дважды, не короче 8 символов.

## 7. Бэкап сейчас и каждую ночь

```bash
sudo bash ./backup.sh
( sudo crontab -l 2>/dev/null | grep -v 'lend-backup.log'; echo "30 3 * * * cd /opt/ai-landing-factory/current/deploy/docker && bash ./backup.sh >> /var/log/lend-backup.log 2>&1 && find /opt/ai-landing-factory/backups -maxdepth 1 -name 'lend-data-*.tgz' -mtime +14 -delete" ) | sudo crontab -
sudo crontab -l
```

`backup.sh` должен написать `Backup ready: /opt/ai-landing-factory/backups/lend-data-….tgz`. Повторный запуск второй строки не задвоит задание.

## 8. Когда Никита подключит сайт

От Никиты нужно две вещи:

- в nginx: `landing-factory.neural-university.ru` → `http://127.0.0.1:18080`, файл сайта `deploy/nginx/ai-landing-docker.conf`;
- сертификат: `sudo certbot --nginx -d landing-factory.neural-university.ru`.

После этого:

```bash
cd /opt/ai-landing-factory/current/deploy/docker
sudo bash ./healthcheck.sh
```

Должно закончиться строкой `Lend is up.`

Потом откройте в браузере `https://landing-factory.neural-university.ru/login`, войдите администратором и на странице «Сотрудники» создайте приглашения для HR.

Если Никита попросит подключить сайт самим (только по согласованию с ним: nginx общий, сайт Романа не трогать):

```bash
sudo cp /opt/ai-landing-factory/current/deploy/nginx/ai-landing-docker.conf /etc/nginx/sites-available/landing-factory.conf
sudo ln -s /etc/nginx/sites-available/landing-factory.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d landing-factory.neural-university.ru
```

## Потом

**Новый релиз.** Залить архив (шаг 1), распаковать с новым `RELEASE_ID` (шаг 3), затем:

```bash
cd /opt/ai-landing-factory/current/deploy/docker && sudo bash ./backup.sh
sudo ln -sfn /opt/ai-landing-factory/shared/lend.env /opt/ai-landing-factory/current/deploy/docker/.env
cd /opt/ai-landing-factory/current/deploy/docker
sudo docker compose build
sudo docker compose up -d --renew-anon-volumes
sudo bash ./healthcheck.sh
```

**Журналы:**

```bash
cd /opt/ai-landing-factory/current/deploy/docker
sudo docker compose ps
sudo docker compose logs --tail=100 backend
sudo docker compose logs --tail=100 gateway
```

**Восстановление из копии:**

```bash
sudo bash ./restore.sh /opt/ai-landing-factory/backups/lend-data-ДАТА_ВРЕМЯ.tgz
```

**Никогда:** `docker compose down -v`: удаляет том с данными.

| Что видно | Что делать |
|---|---|
| `compose build requires buildx` | `sudo apt-get install -y docker-buildx-plugin` и повторить сборку |
| `port is already allocated` | Порт из ошибки кто-то занял: `sudo ss -ltnp`. Сдвинуть нужный `LEND_*_PORT` в `lend.env` и сообщить Никите новый порт для nginx |
| Вход отвечает «Запрос пришёл с другого сайта» | Сайт открыт не по `https://landing-factory.neural-university.ru`: проверить адрес или дописать его в `BACKEND_CORS_ORIGINS` |
| 502 от nginx | Ленд ещё запускается или упал: `sudo bash ./healthcheck.sh`, журналы |
| Браузер предупреждает о сертификате | Для `landing-factory` ещё нет своего сертификата: дождаться `certbot` (шаг 8) |

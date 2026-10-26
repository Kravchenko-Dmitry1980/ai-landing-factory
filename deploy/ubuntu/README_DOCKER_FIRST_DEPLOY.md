# Выкладка Ленда на сервер УИИ (Docker)

Инструкция для того, кто держит сервер. Команды выполняются по SSH на сервере, кроме первого шага.

**Что получится.** Один адрес для всех сотрудников. На сервере работают три контейнера:

| Контейнер | Что делает |
|---|---|
| `lend-gateway` | вход снаружи: nginx внутри Docker, на сам сервер nginx ставить не нужно. `/api/v1/` уходит в backend, всё остальное во frontend |
| `lend-backend` | FastAPI, один процесс |
| `lend-frontend` | Next.js |

Учётные записи, лендинги, загрузки и библиотека лежат в томе Docker `lend_data`. Том переживает перезапуски, пересборки и новые релизы.

**Сервер** (аудит `SERVER_AUDIT_UII_DEV.md`): Ubuntu 24.04, Docker 29, только `docker-compose` v1 (1.29.2, через `sudo`), порты 80 и 443 свободны. Папку `/opt/ai-portal` не трогать, Ленд живёт в `/opt/ai-landing-factory`.

Скрипты запускаются через `bash`: `sudo bash ./healthcheck.sh`. Так они работают, даже если при распаковке пропал признак исполняемого файла.

**Запуск и применение любых изменений — всегда `sudo docker-compose up -d --renew-anon-volumes`.**

- **Зачем флаг.** `docker-compose` 1.29 на Docker 29 не умеет пересоздавать контейнер обычным `up -d`. Он останавливает старый контейнер, падает с `'NoneType' object has no attribute 'get'` (или `KeyError: 'ContainerConfig'`), и сайт остаётся без backend. Флаг `--renew-anon-volumes` обходит эту ошибку.
- **Данные флаг не трогает.** Он касается только безымянных томов, а у Ленда их нет: всё лежит в томе `lend_data`.
- **Никогда не выполняйте `docker-compose down -v`:** `-v` удаляет том с данными.

## 0. Перед первой выкладкой

```bash
sudo docker version --format 'Docker {{.Server.Version}}, API {{.Server.MinAPIVersion}}–{{.Server.APIVersion}}'
sudo docker-compose version
sudo ss -ltnp | grep -E ':(80|443) ' || echo "80 и 443 свободны"
```

- Docker 29 принимает запросы только с версией API от 1.44, а `docker-compose` 1.29 по умолчанию шлёт 1.38. Поэтому в шаблоне настроек стоит `COMPOSE_API_VERSION=1.44`: не удаляйте эту строку.
- Если 80 или 443 заняты, см. `LEND_HTTP_PORT` в шаге 3 и раздел о порте 443 в шаге 6.

## 1. Архив релиза (на рабочем компьютере)

Архив собирается из коммита git. В него попадает только закоммиченное: никаких локальных данных, паролей и `.env`, а у скриптов переводы строк LF.

```powershell
pwsh scripts/build_full_release.ps1
```

Скрипт сам проверяет архив и пишет путь: `.runtime/release/lend-release-<дата>-<коммит>.zip`.

```bash
scp .runtime/release/lend-release-<дата>-<коммит>.zip dkravchenko@195.209.213.170:/tmp/
```

## 2. Распаковка

```bash
RELEASE_ID=<дата>-<коммит>
sudo mkdir -p /opt/ai-landing-factory/releases/${RELEASE_ID} /opt/ai-landing-factory/shared /opt/ai-landing-factory/backups
sudo unzip -q /tmp/lend-release-${RELEASE_ID}.zip -d /opt/ai-landing-factory/releases/${RELEASE_ID}
sudo ln -sfn /opt/ai-landing-factory/releases/${RELEASE_ID} /opt/ai-landing-factory/current
```

## 3. Настройки (один раз)

Файл настроек лежит в `shared` и переживает релизы; в каждом релизе на него ставится ссылка.

```bash
sudo cp /opt/ai-landing-factory/current/deploy/docker/.env.docker.example /opt/ai-landing-factory/shared/lend.env
sudo chmod 600 /opt/ai-landing-factory/shared/lend.env
sudo nano /opt/ai-landing-factory/shared/lend.env
```

Обязательно поправить:

- `BACKEND_CORS_ORIGINS` — адрес, который откроют сотрудники, со схемой и портом, если он не 80/443: `http://195.209.213.170` или `https://lend.example.ru`. Изменения с других адресов сервер отклоняет (защита от подделки запросов), поэтому перечислите через запятую все адреса, которыми пользуются.
- `LEND_HTTP_PORT` — если 80 занят, например `8080`, и тот же порт в адресе выше.

Остальное по умолчанию: без внешнего ИИ и без GPU. `COMPOSE_PROJECT_NAME=lend` и `COMPOSE_API_VERSION=1.44` не меняйте.

```bash
sudo ln -sfn /opt/ai-landing-factory/shared/lend.env /opt/ai-landing-factory/current/deploy/docker/.env
```

## 4. Сборка и запуск

```bash
cd /opt/ai-landing-factory/current/deploy/docker
sudo docker-compose build          # первый раз 10–20 минут
sudo docker-compose up -d --renew-anon-volumes
sudo bash ./healthcheck.sh
```

`healthcheck.sh` проверяет:

- контейнеры;
- базу и папку данных;
- путь посетителя через вход.

Он должен закончиться строкой `Lend is up.` При первом запуске будет предупреждение `WARN no backups yet`: оно уйдёт после шага 7.

Если сразу после запуска пишет `still starting`, подождите минуту и повторите.

## 5. Первый администратор

Учётных записей сначала нет, войти никто не может:

```bash
cd /opt/ai-landing-factory/current/deploy/docker
sudo docker-compose exec backend python -m app.cli create-admin --login <логин> --name "Имя Фамилия"
```

Команда дважды спросит пароль: не короче 8 символов. Дальше в браузере:

1. Откройте `http://<адрес>/login` и войдите.
2. На странице «Сотрудники» нажмите «Создать ссылку-приглашение».
3. Отправьте ссылку сотруднику HR.

Если войти не может ни один администратор:

```bash
sudo docker-compose exec backend python -m app.cli invite --role admin
```

Команда напечатает ссылку `/invite/…`. Допишите к ней адрес сервера.

## 6. HTTPS

Пока сайт работает по HTTP, пароли идут по сети открыто. Как только у адреса есть сертификат:

```bash
sudo mkdir -p /opt/ai-landing-factory/shared/certs
sudo cp fullchain.pem privkey.pem /opt/ai-landing-factory/shared/certs/
sudo chmod 600 /opt/ai-landing-factory/shared/certs/privkey.pem
sudo nano /opt/ai-landing-factory/shared/lend.env
```

В `lend.env` поменять три настройки:

```env
LEND_GATEWAY=https
LEND_CERTS_DIR=/opt/ai-landing-factory/shared/certs
BACKEND_CORS_ORIGINS=https://<адрес>
```

Проверить настройки входа с сертификатом, не трогая работающий сайт:

```bash
cd /opt/ai-landing-factory/current/deploy/docker
sudo docker-compose run --rm --no-deps gateway nginx -t
```

Должно быть `syntax is ok` и `test is successful`. Если nginx ругается на сертификат, сайт продолжает работать по HTTP: исправьте файлы и проверьте снова. Применить:

```bash
sudo docker-compose up -d --renew-anon-volumes
sudo bash ./healthcheck.sh
```

- **Порт 443.** HTTPS рассчитан на стандартный порт: перенаправление с HTTP ведёт на `https://<адрес>/` без номера порта. Если 443 занят, поставьте, например, `LEND_HTTPS_PORT=8443`. Тогда раздайте сотрудникам адрес с портом `https://<адрес>:8443` и укажите его же в `BACKEND_CORS_ORIGINS`: перенаправление с HTTP на такой порт не приведёт.
- **HSTS.** Сайт просит браузеры сутки открывать его только по HTTPS. Когда HTTPS проработает несколько недель без сбоев, разработчик поднимает срок до года в `gateway/https.conf`.
- **Обновление сертификата.** Положите новые `fullchain.pem` и `privkey.pem` в `shared/certs` и выполните `sudo docker-compose restart gateway`. `healthcheck.sh` предупреждает за три недели до окончания срока.

### Если HTTPS заканчивается на прокси университета

Если HTTPS держит прокси университета, а до сервера доходит HTTP:

- Оставьте `LEND_GATEWAY=http`.
- Поставьте `SESSION_COOKIE_SECURE=true`: сам сервер не видит, что посетитель пришёл по HTTPS.
- Прокси должен передавать заголовок `Host` без изменений. Иначе внешний адрес обязательно должен быть в `BACKEND_CORS_ORIGINS`.
- Сообщите разработчику адрес прокси. Он добавит в `gateway/routes.inc` строки `set_real_ip_from <адрес прокси>;` и `real_ip_header X-Forwarded-For;`. Без них сервер считает всех посетителей одним компьютером. Тогда десять неверных паролей к одной учётной записи блокируют её на 15 минут для всех, а сто неудачных входов подряд — вход для всего университета.

## 7. Резервные копии

```bash
cd /opt/ai-landing-factory/current/deploy/docker
sudo bash ./backup.sh
```

Скрипт кладёт архив в `/opt/ai-landing-factory/backups/lend-data-<дата>.tgz`. Сайт при этом работает: база копируется собственным механизмом SQLite, копия проверяется (`integrity_check`). Скрипт пишет, сколько в копии учётных записей и опубликованных лендингов. Если что-то пошло не так, архива не будет вовсе: недоделанных архивов скрипт не оставляет.

Каждую ночь, с хранением две недели (`sudo crontab -e`, одной строкой):

```cron
30 3 * * * cd /opt/ai-landing-factory/current/deploy/docker && bash ./backup.sh >> /var/log/lend-backup.log 2>&1 && find /opt/ai-landing-factory/backups -maxdepth 1 -name 'lend-data-*.tgz' -mtime +14 -delete
```

`healthcheck.sh` предупреждает, если последней копии больше 36 часов. Тогда смотрите `/var/log/lend-backup.log`.

Копируйте архивы и на другой компьютер: копия на том же диске не спасёт от его поломки.

### Восстановление

Восстановление заменяет все данные содержимым архива:

```bash
cd /opt/ai-landing-factory/current/deploy/docker
sudo bash ./restore.sh /opt/ai-landing-factory/backups/lend-data-<дата>.tgz
```

Что делает скрипт:

1. Читает архив целиком и проверяет, что в нём есть база. Повреждённый архив не тронет ничего.
2. Просит ввести `RESTORE`.
3. Останавливает Ленд и сохраняет текущие данные рядом с архивом: `lend-data-<дата>-before-restore.tgz`. Из этой копии можно восстановиться тем же скриптом.
4. Распаковывает архив рядом со старыми данными. Старые данные удаляются только после этого.
5. Запускает Ленд и ждёт, пока он ответит.

Если скрипт остановился с ошибкой, он пишет, где лежит копия прежних данных и какой командой их вернуть.

**На новый сервер:** шаги 1–4, затем `restore.sh` с архивом со старого сервера.

## 8. Новый релиз

```bash
cd /opt/ai-landing-factory/current/deploy/docker && sudo bash ./backup.sh     # сначала копия
# шаги 1–2 с новым RELEASE_ID, затем:
sudo ln -sfn /opt/ai-landing-factory/shared/lend.env /opt/ai-landing-factory/current/deploy/docker/.env
cd /opt/ai-landing-factory/current/deploy/docker
sudo docker-compose build                           # сайт пока работает на старой версии
sudo docker-compose up -d --renew-anon-volumes      # перерыв меньше минуты
sudo bash ./healthcheck.sh
```

Данные остаются в томе `lend_data`. База обновляет свою схему сама при запуске.

## 9. Откат

```bash
sudo ln -sfn /opt/ai-landing-factory/releases/<прежний RELEASE_ID> /opt/ai-landing-factory/current
sudo ln -sfn /opt/ai-landing-factory/shared/lend.env /opt/ai-landing-factory/current/deploy/docker/.env
cd /opt/ai-landing-factory/current/deploy/docker
sudo docker-compose build && sudo docker-compose up -d --renew-anon-volumes
sudo bash ./healthcheck.sh
```

Если новый релиз успел обновить схему базы, прежняя версия откажется с ней работать: в журнале будет «newer than this code». Тогда восстановите копию, сделанную перед обновлением (`restore.sh`).

## 10. Журналы и неполадки

```bash
cd /opt/ai-landing-factory/current/deploy/docker
sudo bash ./healthcheck.sh
sudo docker-compose ps
sudo docker-compose logs --tail=100 backend
sudo docker-compose logs --tail=100 gateway
```

| Что видно | Что делать |
|---|---|
| `client version 1.38 is too old` | В `lend.env` нет строки `COMPOSE_API_VERSION=1.44` или нет ссылки `.env` на `lend.env` (шаг 3) |
| `'NoneType' object has no attribute 'get'` или `KeyError: 'ContainerConfig'`, сайт отвечает 502 | Выполнили `up -d` без флага, backend остановлен: `sudo docker-compose up -d --renew-anon-volumes` |
| `Network "lend_lend_net" needs to be recreated - option "…" has changed` | Docker хранит у сети параметр, которого нет в `docker-compose.yml`. Выполните `sudo docker-compose down && sudo docker-compose up -d --renew-anon-volumes`. Сообщите разработчику, какой параметр назван |
| Страница входа открывается, но вход отвечает «Запрос пришёл с другого сайта» | Адреса, который в браузере, нет в `BACKEND_CORS_ORIGINS`. Добавить и выполнить `sudo docker-compose up -d --renew-anon-volumes` |
| 502 Bad Gateway | Контейнер ещё запускается или упал: `healthcheck.sh`, журналы `backend` и `frontend` |
| После входа снова страница входа | Cookie входа помечена `Secure`, а сайт открыт по HTTP: браузер её не сохраняет. Так бывает при `SESSION_COOKIE_SECURE=true` без HTTPS. Открывайте сайт по `https://` или верните `auto` |
| Порт 80 занят | Другой `LEND_HTTP_PORT` в `lend.env`, тот же порт в `BACKEND_CORS_ORIGINS` |
| «Слишком много неудачных попыток входа» | Подождать 15 минут или выдать ссылку для нового пароля на странице «Сотрудники» |
| `WARN the latest backup is older than 36 hours` | Ночная копия не сработала: `/var/log/lend-backup.log`, `sudo crontab -l` |

Подробнее об учётных записях, публикации и поиске — `docs/ACCOUNTS_AND_LIBRARY.md`. Инструкция для сотрудников — `docs/USER_QUICKSTART.md`.

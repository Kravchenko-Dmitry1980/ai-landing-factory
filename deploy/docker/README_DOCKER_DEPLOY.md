# Docker-комплект Ленда

Основной способ выкладки на сервер УИИ: Ubuntu 24.04, Docker и `docker-compose` v1 (1.29.x, через `sudo`). Пошаговая инструкция — [`deploy/ubuntu/README_DOCKER_FIRST_DEPLOY.md`](../ubuntu/README_DOCKER_FIRST_DEPLOY.md).

## Что в папке

| Файл | Зачем |
|---|---|
| `docker-compose.yml` | три контейнера: `gateway` (nginx, единственный вход снаружи), `backend`, `frontend`; том данных `lend_data`. Формат 3.8 для v1; у сети явно указаны опции, которые Docker 28+ добавляет сам, иначе v1 отказывается работать с существующей сетью |
| `gateway/http.conf`, `gateway/https.conf`, `gateway/routes.inc` | маршруты входа: `/api/v1/` в backend, остальное во frontend; HTTPS-вариант с перенаправлением и HSTS |
| `backend.Dockerfile`, `frontend.Dockerfile` | образы; собираются из корня репозитория, `.dockerignore` не пускает внутрь локальные данные и `.env` |
| `.env.docker.example` | все настройки с пояснениями; на сервере — `/opt/ai-landing-factory/shared/lend.env` |
| `backup.sh` | резервная копия всех данных без остановки сайта: копия базы через SQLite с `integrity_check`, архив проверяется до того, как получит своё имя |
| `restore.sh` | восстановление: сначала читает архив целиком и сохраняет текущие данные (`…-before-restore.tgz`), старые данные удаляет только после успешной распаковки |
| `healthcheck.sh` | контейнеры, база и папка данных (`/health/ready`), путь посетителя через вход (HTTP или HTTPS), срок сертификата, возраст последней копии |
| `lib.sh` | общее для трёх скриптов: полный `PATH` для cron, имена контейнеров, чтение `.env` |
| `certs/` | сюда кладутся `fullchain.pem` и `privkey.pem`, если сертификаты не в `shared/certs` |

## Порты

| Что | Адрес | Кому |
|---|---|---|
| Вход (gateway) | `LEND_BIND:LEND_HTTP_PORT` (по умолчанию `0.0.0.0:80`), `:443` для HTTPS | сотрудникам |
| Backend | `127.0.0.1:18001` | только проверкам с самого сервера |
| Frontend | `127.0.0.1:13000` | только проверкам с самого сервера |

HTTPS рассчитан на стандартный порт 443: перенаправление с HTTP ведёт на `https://<адрес>/` без номера порта.

## Проверено на ноутбуке разработчика (2026-10-26)

Docker 29. Стек проверен двумя способами:

- compose v2;
- docker-compose 1.29.2, та же версия, что на сервере: официальный образ `docker/compose:1.29.2` против локального Docker.

**Через compose v2:**

- сквозной сценарий:
  - первый администратор командой `app.cli create-admin`;
  - приглашение для сотрудника HR, его вход;
  - загрузка реальных PPTX и DOCX, правка, публикация;
  - поиск по фамилии, заказчику и похожей теме;
  - роль читателя;
- `backup.sh`;
- `restore.sh`:
  - восстановление из обычной копии и из копии `before-restore`;
  - отказ на повреждённом архиве, на чужом архиве и без ввода `RESTORE`; в этих случаях данные не меняются.

**Через docker-compose 1.29.2:**

- `build` (около 7 минут без кэша);
- `up -d --renew-anon-volumes`: и после смены `.env`, и с новым образом;
- `exec`, `run --rm --no-deps gateway nginx -t`;
- `backup.sh`, `restore.sh`, `healthcheck.sh`;
- режим HTTPS: перенаправление с HTTP, HSTS на сутки, cookie с флагами `Secure` и `HttpOnly`, роли, отказ входу с чужого сайта.

**Ошибки docker-compose 1.29.2 на Docker 29, которые обходит комплект:**

| Ошибка | Обход |
|---|---|
| `client version 1.38 is too old` | `COMPOSE_API_VERSION=1.44` в `.env` |
| `Network … needs to be recreated - option "com.docker.network.enable_ipv4"` при повторном `up` или `run` | `driver_opts` у сети в `docker-compose.yml` |
| Голый `up -d` при пересоздании контейнера останавливает старый и падает с `'NoneType' object has no attribute 'get'` | всегда `up -d --renew-anon-volumes`; `restore.sh` запускает те же контейнеры через `start` |

Через compose v2 эти ошибки не видны: проверять выкладку нужно версией 1.29.2.

Размер образов: backend около 1 ГБ, frontend около 1,4 ГБ.

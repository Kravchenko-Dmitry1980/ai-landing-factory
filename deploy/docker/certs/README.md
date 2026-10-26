# Сертификаты для HTTPS

Сюда кладутся `fullchain.pem` и `privkey.pem` для адреса сервера, после чего в `deploy/docker/.env`
ставится `LEND_GATEWAY=https` и выполняется `sudo docker-compose up -d --renew-anon-volumes`
(подробно: `deploy/ubuntu/README_DOCKER_FIRST_DEPLOY.md`, шаг 6).

Файлы ключей в git не попадают (`.gitignore`) и в образы тоже (`.dockerignore`).

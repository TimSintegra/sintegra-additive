# Развертывание сайта и админ-панели на сервере

Документ описывает фактическую схему, настроенную на сервере для `sintegra-additive.ru`.

## Важное предупреждение

На сервере работают другие проекты. Не выполнять без проверки:

```bash
docker system prune
docker compose down
docker stop $(docker ps -q)
```

Для этого сайта не используется `docker-compose up`. В репозитории есть `docker-compose.yml` для новой установки, но на текущем сервере уже работает отдельный контейнер сайта на порту `8085`. Запуск Compose в текущей конфигурации создаст второй Nginx и приведет к конфликту порта.

## Текущая архитектура

```text
Интернет
   ↓
Traefik (80/443)
   ↓
контейнер sintegra-additive (Nginx, 8085 → 80)
   ├── статические файлы сайта
   └── /api/ → контейнер sintegra-additive-api:8000
                       ↓
                 SQLite + загруженные файлы
```

### Контейнер сайта

- Имя: `sintegra-additive`
- Образ: `nginx:alpine`
- Порт сервера: `8085`
- Проброс: `0.0.0.0:8085 -> 80`
- Каталог сайта на сервере: `/var/www/sintegra-additive.ru`
- Монтирование: `/var/www/sintegra-additive.ru:/usr/share/nginx/html:ro`
- Сеть: стандартная Docker-сеть `bridge`

### Контейнер API

- Имя: `sintegra-additive-api`
- Образ: `sintegra-additive-api:20260916`
- Внутренний порт: `8000`
- Публичный порт не открывается
- Сеть: `sintegra-admin-net`
- Сетевой alias: `api`
- Переменные: `/var/www/sintegra-additive.ru/.env`
- Хранилище: `/var/lib/sintegra-additive-data:/data`
- База: `/var/lib/sintegra-additive-data/leads.db`
- Файлы заявок: `/var/lib/sintegra-additive-data/uploads/`
- Автозапуск: `restart unless-stopped`

Существующий контейнер `sintegra-additive` подключен одновременно к сетям `bridge` и `sintegra-admin-net`. Благодаря этому Nginx видит API по адресу `http://api:8000`.

## Админ-панель

Адрес:

```text
https://sintegra-additive.ru/api/admin
```

Пароль задается в `.env` переменной `ADMIN_PASSWORD`.

В панели доступны:

- просмотр заявок;
- поиск по имени, телефону, e-mail, задаче и комментарию;
- фильтр по датам;
- скачивание прикрепленных файлов;
- выгрузка текущего списка в Excel `.xlsx`.

Проверка API:

```bash
curl -i https://sintegra-additive.ru/api/health
```

Ожидаемый ответ:

```json
{"ok":true}
```

## Переменные окружения

Файл находится здесь:

```text
/var/www/sintegra-additive.ru/.env
```

Минимальные переменные:

```env
ADMIN_PASSWORD=пароль_администратора
SECRET_KEY=случайная_секретная_строка
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

Проверить наличие переменных без вывода секретов:

```bash
grep -E '^(ADMIN_PASSWORD|SECRET_KEY)=' /var/www/sintegra-additive.ru/.env | sed 's/=.*$/=<set>/'
stat -c '%a %n' /var/www/sintegra-additive.ru/.env
```

Ожидаемый режим файла `.env` — `600`.

## Что было сделано при интеграции

1. Обновлены файлы проекта через Git:

   ```bash
   cd /var/www/sintegra-additive.ru
   git pull --ff-only origin main
   ```

2. Создана отдельная сеть API:

   ```bash
   docker network create sintegra-admin-net
   ```

3. Действующий Nginx подключен к этой сети без остановки контейнера:

   ```bash
   docker network connect sintegra-admin-net sintegra-additive
   ```

4. Создан каталог постоянных данных:

   ```bash
   mkdir -p /var/lib/sintegra-additive-data
   chmod 700 /var/lib/sintegra-additive-data
   ```

5. Собран отдельный API-образ:

   ```bash
   docker build -t sintegra-additive-api:20260916 ./api
   ```

6. API запущен без публикации порта наружу:

   ```bash
   docker run -d \
     --name sintegra-additive-api \
     --restart unless-stopped \
     --network sintegra-admin-net \
     --network-alias api \
     --env-file /var/www/sintegra-additive.ru/.env \
     -v /var/lib/sintegra-additive-data:/data \
     sintegra-additive-api:20260916
   ```

7. Текущий конфиг Nginx был сохранен:

   ```text
   /root/sintegra-additive-nginx.backup.conf
   ```

8. Новый конфиг был скопирован внутрь действующего контейнера:

   ```bash
   docker cp /var/www/sintegra-additive.ru/nginx.conf sintegra-additive:/etc/nginx/conf.d/default.conf
   ```

9. Конфигурация проверена и Nginx перезагружен только после успешной проверки:

   ```bash
   docker exec sintegra-additive nginx -t
   docker exec sintegra-additive nginx -s reload
   ```

## Проверки после изменений

Статус контейнеров:

```bash
docker ps --filter name=sintegra-additive
```

Проверка API внутри контейнера API:

```bash
docker exec sintegra-additive-api wget -qO- http://127.0.0.1:8000/api/health
```

Проверка связи Nginx с API:

```bash
docker exec sintegra-additive sh -c 'wget -qO- http://api:8000/api/health'
```

Проверка логов API:

```bash
docker logs --tail 100 sintegra-additive-api
```

## Обновление API

Сначала обновить файлы проекта:

```bash
cd /var/www/sintegra-additive.ru
git status --short
git pull --ff-only origin main
```

Перед заменой контейнера проверить, что текущая база существует:

```bash
ls -lh /var/lib/sintegra-additive-data/leads.db
```

Создать резервную копию базы и файлов:

```bash
tar -czf /root/sintegra-leads-backup-$(date +%F-%H%M).tar.gz /var/lib/sintegra-additive-data
```

Собрать новый образ с новым тегом, например:

```bash
docker build -t sintegra-additive-api:YYYYMMDD ./api
```

Затем API-контейнер можно пересоздать с теми же параметрами сети и хранилища. Перед этим нужно проверить, что новый образ собрался успешно. Не удалять каталог `/var/lib/sintegra-additive-data` — там находятся заявки.

## Обновление статических файлов

Файлы сайта подключены в контейнер как read-only bind mount. Изменения в `/var/www/sintegra-additive.ru` становятся доступны контейнеру без пересоздания Nginx.

Если меняется JavaScript или CSS, браузер может использовать старую копию из кеша. Для проверки использовать жесткое обновление страницы:

```text
Ctrl + Shift + R
```

Если меняется `nginx.conf`, сначала сделать резервную копию, затем скопировать файл в контейнер, проверить `nginx -t` и только после этого выполнить reload.

## Откат конфигурации Nginx

Если после изменения Nginx возникла проблема:

```bash
docker cp /root/sintegra-additive-nginx.backup.conf sintegra-additive:/etc/nginx/conf.d/default.conf
docker exec sintegra-additive nginx -t
docker exec sintegra-additive nginx -s reload
```

## Если API не запускается

```bash
docker ps -a --filter name=sintegra-additive-api
docker logs --tail 100 sintegra-additive-api
docker inspect sintegra-additive-api --format '{{json .NetworkSettings.Networks}}'
```

Нельзя удалять каталог данных до проверки резервной копии. При необходимости контейнер API можно остановить отдельно:

```bash
docker stop sintegra-additive-api
```

Остановка этого контейнера не останавливает сайт и другие проекты, но временно отключает прием заявок.

## Известная доработка формы

После первой интеграции заявка сохранялась, но браузер показывал «Ошибка сети». Причина была в JavaScript: после успешной отправки использовалась переменная `label` из другой области видимости. На сервере точечно заменено:

```js
if (label) label.textContent = 'Файл не выбран';
```

на:

```js
if (formFileLabel) formFileLabel.textContent = 'Файл не выбран';
```

При следующих обновлениях сайта важно не потерять эту правку и зафиксировать ее в Git.

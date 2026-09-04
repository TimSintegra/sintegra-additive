Инструкция по восстановлению сайта sintegra-additive.ru при падении контейнера
Применимо для сервера с Docker и Traefik.
Предполагается, что сайт работает в контейнере nginx:alpine, а статика лежит в /var/www/sintegra-additive.ru.

1. Проверка состояния контейнера
bash
docker ps -a | grep sintegra-additive
Если контейнер отсутствует или имеет статус Exited, переходите к шагу 2.

2. Просмотр ошибок
Если контейнер не запускается, посмотрите причину:

bash
docker inspect sintegra-additive --format '{{.State.Error}}'
Также проверьте логи:

bash
docker logs sintegra-additive --tail 50
3. Сбор информации о старой конфигурации
Перед удалением контейнера сохраните его параметры (особенно монтирования и переменные окружения):

bash
docker inspect sintegra-additive
Обратите внимание на секции:

HostConfig.Binds – пути монтирования томов,

Config.Env – переменные окружения (если есть),

HostConfig.PortBindings – проброс портов.

В нашем случае было:

Бинд-маунт: /var/www/sintegra-additive.ru:/usr/share/nginx/html:ro

Проброс порта: 8085:80 (без указания IP)

4. Удаление нерабочего контейнера
bash
docker rm -f sintegra-additive
5. Запуск нового контейнера с корректными параметрами
Важно: не привязывайте порт к конкретному IP, если в этом нет острой необходимости. Используйте общий адрес 0.0.0.0 (стандартное поведение -p).

bash
docker run -d \
  --name sintegra-additive \
  -p 8085:80 \
  -v /var/www/sintegra-additive.ru:/usr/share/nginx/html:ro \
  --restart unless-stopped \
  nginx:alpine
Если были дополнительные переменные окружения, добавьте их через -e KEY=VALUE.

6. Проверка локальной доступности
bash
curl -I http://localhost:8085
Ожидается ответ HTTP/1.1 200 OK (или другой успешный код, но не 403/500). Если ответ 403 – проверьте, что в папке /var/www/sintegra-additive.ru есть index-файлы и права доступа.

7. Обновление маршрутов Traefik (если используется)
Если сайт проксируется через Traefik, перезапустите Traefik, чтобы он перечитал конфигурацию и начал направлять трафик на новый контейнер:

bash
docker restart proxy-server
Через несколько секунд проверьте доступ через домен:

bash
curl -I https://sintegra-additive.ru
Если ответ не 200, посмотрите логи Traefik:

bash
docker logs proxy-server --tail 100 | grep -i sintegra
Ошибки вида connection refused или 404 могут указывать на то, что Traefik пытается обратиться по старому IP/порту. В этом случае убедитесь, что в конфигурации Traefik (лейблы или файл) указан корректный адрес назначения. Если используется динамическое обнаружение через Docker, Traefik сам определит новый контейнер.

8. Автоматизация (рекомендация)
Чтобы в будущем избежать ручного восстановления, рекомендуется описать контейнер в docker-compose.yml. Пример:

yaml
version: '3'
services:
  sintegra-additive:
    image: nginx:alpine
    container_name: sintegra-additive
    restart: unless-stopped
    ports:
      - "8085:80"
    volumes:
      - /var/www/sintegra-additive.ru:/usr/share/nginx/html:ro
Тогда запуск будет одной командой:

bash
docker-compose up -d
9. Дополнительные советы
Избегайте привязки к конкретному IP в -p, если только это не требуется для специфической сетевой архитектуры. Используйте -p 8085:80 (без IP) – это эквивалентно привязке к 0.0.0.0.

Если вы всё же вынуждены использовать конкретный IP, убедитесь, что этот IP существует на интерфейсе и доступен Docker’у. Проверить можно командой ip addr show.

Регулярно делайте резервные копии статики (/var/www/sintegra-additive.ru) и, при необходимости, конфигураций.
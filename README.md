# 005 Бот - Telegram-бот

Сервис осуществляет взаимодействие с пользователями в Telegram и отправляет уведомления об отключениях, полученные через очередь сообщений. Дополнительно позволяет фильтровать уведомления по наименованию улицы.

Проект находится на стадии MVP и может содержать обратно несовместимые изменения.

## Используемые технологии, библиотеки

- [Python](https://www.python.org/)
- [Docker](https://www.docker.com/)
- [Pipenv](https://github.com/pypa/pipenv)
- [Redis](https://redis.io/)
- [aiogram](https://github.com/aiogram/aiogram)
- [pydantic](https://github.com/pydantic/pydantic)

## Настройки

Для настройки используются переменные окружения:

| Название          | Описание                                     | По умолчанию             |
| ----------------- | -------------------------------------------- | ------------------------ |
| `REDIS__URL`      | URL Redis                                    | `redis://localhost:6379` |
| `REDIS__PREFIX`   | Префикс ключей в Redis (хранилище и очередь) | `bot-005`                |
| `TELEGRAM__TOKEN` | Токен Telegram бота                          | **обязательно**          |


## Логика работы

Сервис выполняет 2 задачи:

1. Получает сообщеия из очереди и отправляет уведомления в Telegram подписавшимся пользователям с учетом фильтра.
2. Принимает от пользователей команды на изменения состояния подписки и фиксирует настройки в Redis.

## Лицензия

Проект распространяется под лицензией Apache 2.0.

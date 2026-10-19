# web-shop-FASTAPI

[![CI](https://github.com/wemnt/web-shop-FASTAPI/actions/workflows/ci.yml/badge.svg)](https://github.com/wemnt/web-shop-FASTAPI/actions/workflows/ci.yml)

[English](README.md) | **Русский**

Бэкенд интернет-магазина на FastAPI, асинхронном SQLAlchemy и NATS JetStream.

**API онлайн:** <https://api.wemnt.dev/docs>

**Стек:** Python 3.14, FastAPI, Pydantic v2, SQLAlchemy 2.0 (async), PostgreSQL, Redis, Alembic, NATS JetStream, FastStream, Docker Compose, uv, ruff, basedpyright, pytest, GitHub Actions

## Возможности

- JWT-аутентификация с ротацией refresh-токенов и защитой от повторного использования
- Ограничение частоты попыток логина на Redis
- Роли (`customer`, `admin`) и админские эндпоинты: заказы, пользователи, блокировка
- Каталог товаров, корзина с атомарным upsert, заказы с резервированием остатков
- Жизненный цикл заказа с явными переходами статусов
- Доменные события через transactional outbox в NATS JetStream
- Фоновый worker: relay outbox, идемпотентные consumer'ы, автоотмена невыкупленных заказов

## Архитектура

```
                          ┌──► Redis (rate limiting)
client ──► web (FastAPI) ─┤
                          └──► PostgreSQL
                                  │  outbox_events
                                  ▼
              worker ── relay ──► NATS JetStream ──► consumers
                    └── автоотмена (TTL)
```

- **Транзакция на запрос.** Сервисы делают только `flush`, запрос коммитится или откатывается целиком.
- **Transactional outbox.** Заказ и его событие сохраняются в одной транзакции, поэтому события не теряются и не бывают фантомными. Relay публикует их с `FOR UPDATE SKIP LOCKED`, так что несколько worker'ов могут работать параллельно.
- **Доставка at-least-once с двойной дедупликацией:** `Nats-Msg-Id` на стороне JetStream и таблица `processed_events` на стороне consumer'а.
- **Без перепродажи.** Товары блокируются через `SELECT ... FOR UPDATE` в фиксированном порядке, чтобы избежать взаимоблокировок.
- **Rate limiting логина.** Счётчик с фиксированным окном в Redis (атомарные `INCR` + `EXPIRE`), общий для всех процессов приложения: 5 попыток в минуту с одного IP, дальше `429`.

## Запуск

```bash
cp .env.example .env   # заполнить значения
make up
make migrate
```

Swagger UI: <http://localhost:8000/docs>

## Тесты

```bash
docker compose exec db createdb -U <POSTGRES_USER> webshop_test   # один раз
make test
make lint
```

Тесты работают с настоящим PostgreSQL. Каждый тест изолирован в транзакции, которая откатывается после него.

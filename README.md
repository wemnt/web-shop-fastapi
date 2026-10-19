# web-shop-FASTAPI

[![CI](https://github.com/wemnt/web-shop-FASTAPI/actions/workflows/ci.yml/badge.svg)](https://github.com/wemnt/web-shop-FASTAPI/actions/workflows/ci.yml)

**English** | [Русский](README_ru.md)

Online store backend on FastAPI, async SQLAlchemy and NATS JetStream.

**Live API:** <https://api.wemnt.dev/docs>

**Stack:** Python 3.14, FastAPI, Pydantic v2, SQLAlchemy 2.0 (async), PostgreSQL, Redis, Alembic, NATS JetStream, FastStream, Docker Compose, uv, ruff, basedpyright, pytest, GitHub Actions

## Features

- JWT auth with refresh token rotation and reuse detection
- Login rate limiting backed by Redis
- Roles (`customer`, `admin`) and admin endpoints: orders, users, block/unblock
- Product catalog, cart with atomic upsert, orders with stock reservation
- Order lifecycle with explicit status transitions
- Domain events through a transactional outbox to NATS JetStream
- Background worker: outbox relay, idempotent consumers, auto-cancel of orders not picked up in time

## Architecture

```
                          ┌──► Redis (rate limiting)
client ──► web (FastAPI) ─┤
                          └──► PostgreSQL
                                  │  outbox_events
                                  ▼
              worker ── relay ──► NATS JetStream ──► consumers
                    └── auto-cancel (TTL)
```

- **Transaction per request.** Services only `flush`; the request commits or rolls back as a whole.
- **Transactional outbox.** An order and its event are saved in one transaction, so events are never lost or phantom. The relay publishes them with `FOR UPDATE SKIP LOCKED`, so several workers can run in parallel.
- **At-least-once delivery, deduplicated twice:** `Nats-Msg-Id` on the JetStream side and a `processed_events` table on the consumer side.
- **No overselling.** Products are locked with `SELECT ... FOR UPDATE` in a fixed order to avoid deadlocks.
- **Login rate limiting.** A fixed-window counter in Redis (atomic `INCR` + `EXPIRE`), shared by all app processes: 5 attempts per minute per IP, then `429`.

## Quick start

```bash
cp .env.example .env   # fill in the values
make up
make migrate
```

Swagger UI: <http://localhost:8000/docs>

## Tests

```bash
docker compose exec db createdb -U <POSTGRES_USER> webshop_test   # once
make test
make lint
```

Tests run against a real PostgreSQL. Each test is isolated in a transaction that is rolled back afterwards.

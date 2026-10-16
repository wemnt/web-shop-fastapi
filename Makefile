.PHONY: up down logs migrate revision test lint fmt

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f web worker

migrate:
	docker compose run --rm web uv run alembic upgrade head

revision:
	docker compose run --rm web uv run alembic revision --autogenerate -m "$(m)"

test:
	docker compose run --rm web uv run pytest -v

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run basedpyright

fmt:
	uv run ruff check --fix .
	uv run ruff format .

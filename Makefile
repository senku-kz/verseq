VENV     := .venv
PYTHON   := $(VENV)/bin/python
PIP      := $(VENV)/bin/pip
UVICORN  := $(VENV)/bin/uvicorn
PYTEST   := $(VENV)/bin/pytest
RUFF     := $(VENV)/bin/ruff

.DEFAULT_GOAL := help

# ─── Help ─────────────────────────────────────────────────────────────────────

.PHONY: help
help:
	@echo ""
	@echo "  VerseQ — команды"
	@echo ""
	@echo "  Установка"
	@echo "    make install       Создать venv, установить зависимости BE + FE"
	@echo "    make install-be    Только бэкенд"
	@echo "    make install-fe    Только фронтенд"
	@echo ""
	@echo "  База данных"
	@echo "    make db-init       Создать таблицы (первый запуск)"
	@echo "    make db-migrate    Создать новую миграцию Alembic"
	@echo "    make db-upgrade    Применить миграции"
	@echo "    make db-reset      Удалить БД и пересоздать"
	@echo ""
	@echo "  Разработка"
	@echo "    make run           Запустить бэкенд + фронтенд (фоновые процессы)"
	@echo "    make start         Запустить только бэкенд"
	@echo "    make dev           Псевдоним для make run"
	@echo "    make be            Запустить только бэкенд (прямой вызов)"
	@echo "    make fe            Запустить только фронтенд"
	@echo "    make stop          Остановить все dev-серверы"
	@echo ""
	@echo "  Тесты и качество кода"
	@echo "    make test          Запустить все тесты"
	@echo "    make test-v        Запустить тесты подробно"
	@echo "    make test-file f=tests/test_auth.py   Один файл тестов"
	@echo "    make lint          Проверить код (ruff)"
	@echo "    make format        Форматировать код (ruff)"
	@echo ""
	@echo "  Сборка"
	@echo "    make build         Собрать фронтенд для продакшена"
	@echo "    make clean         Удалить артефакты сборки"
	@echo ""

# ─── Установка ────────────────────────────────────────────────────────────────

.PHONY: install install-be install-fe
install: install-be install-fe

install-be:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip -q
	$(PIP) install -r requirements.txt
	@echo "✓ Бэкенд: зависимости установлены"

install-fe:
	cd frontend && npm install
	@echo "✓ Фронтенд: зависимости установлены"

# ─── База данных ──────────────────────────────────────────────────────────────

.PHONY: db-init db-migrate db-upgrade db-reset
db-init:
	$(PYTHON) scripts/init_db.py

db-migrate:
	$(VENV)/bin/alembic revision --autogenerate -m "$(m)"

db-upgrade:
	$(VENV)/bin/alembic upgrade head

db-reset:
	rm -f verseq.db
	$(PYTHON) scripts/init_db.py
	@echo "✓ База данных пересоздана"

# ─── Разработка ───────────────────────────────────────────────────────────────

.PHONY: dev be fe stop
dev: ## alias → make run
	@make run

run:
	@make be &
	@make fe

start: ## alias → make be (только бэкенд)
	@make be

be:
	$(UVICORN) app.main:app --reload --port 8000

fe:
	cd frontend && npx quasar dev

stop:
	@pkill -f "uvicorn app.main:app" 2>/dev/null && echo "✓ Бэкенд остановлен" || true
	@pkill -f "quasar dev"           2>/dev/null && echo "✓ Фронтенд остановлен" || true

# ─── Тесты и качество кода ────────────────────────────────────────────────────

.PHONY: test test-v test-file lint format
test:
	$(PYTEST) tests/

test-v:
	$(PYTEST) tests/ -v

test-file:
	$(PYTEST) $(f) -v

lint:
	$(RUFF) check .

format:
	$(RUFF) format .

# ─── Сборка ───────────────────────────────────────────────────────────────────

.PHONY: build clean
build:
	cd frontend && npx quasar build

clean:
	rm -rf frontend/dist
	rm -rf __pycache__ app/__pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Артефакты удалены"

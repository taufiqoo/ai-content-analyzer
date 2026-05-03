.PHONY: setup up down migrate seed logs restart

# Copy env and bring up all services
setup:
	@cp -n .env.example .env || true
	@echo "✅ .env created (edit it with your credentials)"
	@docker compose build

up:
	docker compose up -d
	@echo "✅ Services running:"
	@echo "   Frontend:  http://localhost:3000"
	@echo "   Backend:   http://localhost:8000"
	@echo "   API Docs:  http://localhost:8000/docs"

down:
	docker compose down

restart:
	docker compose restart backend worker

# Run Alembic migrations
migrate:
	docker compose exec backend alembic upgrade head

# Seed default niche configs
seed:
	docker compose exec backend python scripts/seed.py

# Install Playwright browsers inside container
playwright-install:
	docker compose exec backend playwright install chromium

logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

logs-worker:
	docker compose logs -f worker

# Development: run backend locally (without Docker)
dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-worker:
	cd backend && celery -A app.celery_app worker --loglevel=info

dev-frontend:
	cd frontend && npm run dev

# Full local dev setup
dev: 
	@echo "Starting backend + worker + frontend in development mode..."
	@make dev-backend &
	@make dev-worker &
	@make dev-frontend &
	@wait

status:
	docker compose ps

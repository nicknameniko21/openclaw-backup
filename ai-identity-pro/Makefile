.PHONY: help dev-up dev-down prod-up prod-down build test lint

help:
	@echo "AI Identity Pro - Available Commands:"
	@echo ""
	@echo "  make dev-up      - Start development environment"
	@echo "  make dev-down    - Stop development environment"
	@echo "  make prod-up     - Start production environment"
	@echo "  make prod-down   - Stop production environment"
	@echo "  make build       - Build all Docker images"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run linting"
	@echo "  make logs        - View logs"
	@echo "  make shell       - Open backend shell"
	@echo ""

dev-up:
	docker-compose up -d
	@echo "✅ Development environment started"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"

dev-down:
	docker-compose down
	@echo "✅ Development environment stopped"

prod-up:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "✅ Production environment started"

prod-down:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
	@echo "✅ Production environment stopped"

build:
	docker-compose build
	@echo "✅ Docker images built"

test:
	cd backend && pytest
	@echo "✅ Tests completed"

lint:
	cd backend && flake8 .
	cd frontend && npm run lint
	@echo "✅ Linting completed"

logs:
	docker-compose logs -f

shell:
	docker-compose exec backend bash

# Database commands
migrate:
	docker-compose exec backend alembic upgrade head

backup:
	docker-compose exec postgres pg_dump -U postgres ai_identity > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Database backup created"

# Deployment commands
deploy-vercel:
	cd frontend && vercel --prod

deploy-railway:
	railway up

# Development shortcuts
frontend-dev:
	cd frontend && npm run dev

backend-dev:
	cd backend && uvicorn main:app --reload

# Clean up
clean:
	docker-compose down -v
	docker system prune -f
	@echo "✅ Cleaned up Docker resources"

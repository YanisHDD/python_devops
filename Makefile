.PHONY: up down logs test lint dev build

up:
	docker compose up --build -d

down:
	docker compose down -v

logs:
	docker compose logs -f

test:
	pytest tests/ -v --cov=api --cov-fail-under=75

lint:
	flake8 api/ dashboard/ tests/

dev:
	@echo "Starting backend and frontend locally..."
	API_KEY=dev-secret-change-in-prod API_BASE_URL=http://localhost:8000 uvicorn api.main:app --reload --port 8000 &
	API_KEY=dev-secret-change-in-prod API_BASE_URL=http://localhost:8000 streamlit run dashboard/app.py --server.port 8501

build:
	docker compose build

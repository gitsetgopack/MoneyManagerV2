# Help function to display available commands
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies in the virtual environment
	pip install --upgrade pip
	pip install -r requirements.txt
	pre-commit install
	npm install -g nodemon

api: ## Run the FastAPI app using the virtual environment
	python api/app.py

test: clean_docker ## Start MongoDB Docker container, run tests, and clean up
	docker run --name mongo-test -p 27017:27017 -d mongo:latest
	@sleep 5  # Wait for MongoDB to be ready
	pytest -v || (docker stop mongo-test && docker rm mongo-test && exit 1)
	docker stop mongo-test
	docker rm mongo-test

fix: ## Black format and isort on api dir
	black api/
	isort api/

clean_docker:
	@docker stop mongo-test || true
	@docker rm mongo-test || true

clean: clean_docker ## Clean up Python bytecode files and caches
	(find . -type f \( -name "*.pyc" -o -name ".coverage" -o -name ".python-version" \) -delete && \
	find . -type d \( -name "__pycache__" -o -name ".pytest_cache" -o -name ".mypy_cache" \) -exec rm -rf {} +)

no_verify_push: ## Stage, commit & push with --no-verify
	@read -p "Enter commit message: " msg; \
	git commit -a -m "$$msg" --no-verify
	git push

telegram: ## Run the Telegram bot with auto-reload on file changes
	python scripts/watch_and_run.py bots/telegram/main.py bots/telegram

.PHONY: all help install api test fix clean no_verify_push telegram

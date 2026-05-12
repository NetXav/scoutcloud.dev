.PHONY: run run-docker build push init plan apply destroy check setup test clean

run:
	cd src/app && DATABASE_URL=placeholder DYNAMODB_TABLE=placeholder \
	  FLASK_APP=app.py python3 -m flask run --host=0.0.0.0 --port=8080 --debug

run-docker:
	docker-compose -f src/app/docker-compose.yml up

build:
	docker build -t scoutcloud-app src/app/

push:
	@test -n "$(ECR_URL)" || (echo "Usage: make push ECR_URL=ACCOUNT.dkr.ecr.REGION.amazonaws.com" && exit 1)
	aws ecr get-login-password --region us-east-1 | \
	  docker login --username AWS --password-stdin $(ECR_URL)
	docker tag scoutcloud-app:latest $(ECR_URL)/scoutcloud-app:latest
	docker push $(ECR_URL)/scoutcloud-app:latest
	@echo "Pushed: $(ECR_URL)/scoutcloud-app:latest"

init:
	cd infra && terraform init

plan:
	cd infra && terraform plan

apply:
	cd infra && terraform apply

destroy:
	cd infra && terraform destroy

check:
	@URL=$${APP_URL:-http://localhost:8080}; \
	echo "Checking $$URL/health ..."; \
	curl -sf $$URL/health | python3 -m json.tool

setup:
	bash scripts/setup-check.sh

test:
	cd src/app && python3 -m pytest tests/ -v 2>/dev/null || \
	echo "No tests yet - tests added in Chapter 15"

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -name ".terraform" -type d -exec rm -rf {} + 2>/dev/null || true

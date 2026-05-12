FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DATABASE_URL=placeholder
ENV DYNAMODB_TABLE=placeholder
ENV COGNITO_USER_POOL_ID=
ENV COGNITO_CLIENT_ID=
ENV AWS_REGION=us-east-1
ENV SECRET_ARN=

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

CMD ["gunicorn", "app:app", \
     "--bind", "0.0.0.0:80", \
     "--workers", "2", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]

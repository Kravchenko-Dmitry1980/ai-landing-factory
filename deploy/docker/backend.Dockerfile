# Backend image — AI Landing Factory
# Build from repo root: docker build -f deploy/docker/backend.Dockerfile .
#
# Embeds frontend/dist-wow (wow-app.js) so WOW preview/export works without a
# separate frontend volume at runtime.

FROM node:20-bookworm-slim AS wow-builder
RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 \
      python3-pil \
    && ln -sf /usr/bin/python3 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend ./
RUN npm run build:wow-bundle

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
COPY --from=wow-builder /frontend/dist-wow /app/frontend/dist-wow

WORKDIR /app/backend
EXPOSE 8001

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]

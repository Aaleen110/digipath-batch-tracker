# Postman / Newman smoke tests

Collection and environment for DigiPath Batch Tracker API smoke runs.

## Prerequisites

1. API running locally:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

2. Env values in `local.postman_environment.json` match your API (default `apiKey` is `dev-secret-key`).

## Setup (once)

```bash
cd postman
npm install
```

## Run smoke tests

```bash
cd postman
npm run smoke
```

Verbose:

```bash
npm run smoke:verbose
```

CI-style (JUnit XML → `results/newman-junit.xml`):

```bash
npm run smoke:ci
```

Or without installing locally:

```bash
npx --yes newman run DigiPath-Batch-Tracker.postman_collection.json \
  -e local.postman_environment.json
```

## Override variables

```bash
npx newman run DigiPath-Batch-Tracker.postman_collection.json \
  -e local.postman_environment.json \
  --env-var "baseURL=http://127.0.0.1:8000" \
  --env-var "apiKey=dev-secret-key" \
  --env-var "partnerWebhook=https://postman-echo.com/post"
```

`partnerWebhook` defaults to `https://postman-echo.com/post` so Notify works without webhook.site.

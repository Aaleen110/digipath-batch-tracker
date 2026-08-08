# DigiPath Batch Tracker — Frontend

React + Vite + TypeScript + Tailwind CSS console for the batch tracking API.

## Setup

```bash
cp .env.example .env
# Set VITE_API_KEY to the same value as backend API_KEY
```

Leave `VITE_API_BASE_URL` empty so Vite proxies `/batches` to `http://127.0.0.1:8000`.

## Run

```bash
# Terminal 1
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload

# Terminal 2
cd frontend && npm install && npm run dev
```

Open http://localhost:5173

# AI-Powered Ecological Restoration Intelligence Platform (Nepal)

Production-ready full stack application for terrain-aware restoration planning in Nepal.

## Stack

- Frontend: React, Vite, Tailwind CSS, React Router, Axios, React Leaflet
- Backend: FastAPI, httpx, Pydantic
- AI: Claude API

## Structure

- `backend/` FastAPI app with soil, elevation, environment, and analysis routers
- `frontend/` Vite app with dashboard and dedicated analysis pages

## Run Backend

```bash
cd backend
py -3.13 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload --port 8000
```

If you prefer to avoid the Rust compatibility path entirely, use Python 3.13 for the backend virtual environment.

## Run Frontend

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

## Environment Variables

- `ANTHROPIC_API_KEY` for Claude responses
- `ANTHROPIC_MODEL` for the Claude model name
- `CORS_ORIGINS` for frontend origins
- `API_TIMEOUT_SECONDS` for backend timeouts

## API Endpoints

- `GET /soil?lat=&lng=`
- `GET /elevation?lat=&lng=`
- `GET /environment?lat=&lng=`
- `POST /analyze`

## Notes

- If `ANTHROPIC_API_KEY` is not configured, the backend returns a deterministic fallback analysis so the app still runs end to end.
- The legacy `frontend/model.html` file is preserved in the repo, but the production app is the Vite frontend in `frontend/src/`.

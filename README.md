# AI-Powered Ecological Restoration Intelligence Platform (Nepal)

Production-ready full stack application for terrain-aware restoration planning in Nepal.

## Stack

- Frontend: React, Vite, Tailwind CSS, React Router, Axios, React Leaflet
- Backend: FastAPI, httpx, Pydantic, NARC soil API
- AI: Claude API

## Structure

- `backend/` FastAPI app with soil, elevation, environment, and analysis routers
- `frontend/` Vite app with dashboard and dedicated analysis pages

## Run Backend

```bash
cd backend
py -3.13 -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -m uvicorn main:app --reload --port 8000
```

Or from the repository root, you can now run:

```bash
python -m uvicorn main:app --reload --port 8000
```

Run the first set of commands from inside `backend/` so the virtual environment lives at `backend/.venv`.

If you are using PowerShell or Command Prompt instead of Git Bash, activate the venv with `.venv\Scripts\activate`.
In PowerShell, copy the env file with `Copy-Item .env.example .env`.

If you prefer to avoid the Rust compatibility path entirely, use Python 3.13 for the backend virtual environment.

## Run Frontend

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

## Verify ML Pipeline

From the repository root, run the verification script to build or synthesize a dataset, train the model, and execute a sample inference:

```bash
python -m ml_pipeline.verify_pipeline
```

If you prefer to run the script directly, use:

```bash
python ml_pipeline\verify_pipeline.py
```

### Enable real NARC feature data

To train and predict with real NARC soil/environ data instead of the mock provider, set:

```bash
set USE_NARC_PROVIDER=true
set NARC_API_URL=https://your-narc-api.example.com/soil
set NARC_API_KEY=your_api_key_here
```

If `USE_NARC_PROVIDER` is not enabled, the pipeline will fall back to `MockFeatureProvider`.

## Environment Variables

- `ANTHROPIC_API_KEY` for Claude responses
- `ANTHROPIC_MODEL` for the Claude model name
- `CORS_ORIGINS` for frontend origins
- `API_TIMEOUT_SECONDS` for backend timeouts
- `NARC_SOIL_API_URL` for the NARC soil and elevation endpoint

## API Endpoints

- `GET /soil?lat=&lng=`
- `GET /elevation?lat=&lng=`
- `GET /environment?lat=&lng=`
- `POST /analyze`

## Notes

- The backend now uses the NARC soil API for soil properties and elevation only; if the live API is unavailable, the request fails instead of fabricating values.
- The legacy `frontend/model.html` file is preserved in the repo, but the production app is the Vite frontend in `frontend/src/`.

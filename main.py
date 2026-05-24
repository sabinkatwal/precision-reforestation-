"""Root ASGI entrypoint for the project.

This module exposes the FastAPI `app` from `backend.main` so the app can be
started with `uvicorn main:app` from the repository root.
"""

from backend.main import app

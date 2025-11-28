"""Top-level FastAPI entrypoint for deployment and tooling discovery.

Provides a stable module path (`app`) that loads the Guardian compliance API
application for ASGI servers or execution via ``python app.py``.
"""
from src.compliance_api import app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8010, log_level="info")

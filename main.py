"""
FastAPI Application Entrypoint
Main entry point for the MT5 REST API server
"""
from src.mt5_api import app

# This is the FastAPI app instance that deployment platforms look for
# Usage: uvicorn main:app --host 0.0.0.0 --port 8000

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

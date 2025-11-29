"""
FastAPI Application - Alternative Entrypoint
Alias for main.py - imports the MT5 REST API app
"""
from src.mt5_api import app

# FastAPI app instance
__all__ = ['app']

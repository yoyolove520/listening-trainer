"""
Listening Trainer — Desktop Application
Entry point for the PySide6 frontend.
"""
import sys
import os

# Ensure app package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set SSL cert path for Windows (used by urllib, httpx, aiohttp, etc.)
if not os.environ.get("SSL_CERT_FILE"):
    try:
        import certifi
        os.environ["SSL_CERT_FILE"] = certifi.where()
    except Exception:
        pass

from app.main_window import run

if __name__ == "__main__":
    run()

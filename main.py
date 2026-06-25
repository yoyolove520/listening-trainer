"""
Listening Trainer — Desktop Application
Entry point for the PySide6 frontend.
"""
import sys
import os

# Ensure app package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main_window import run

if __name__ == "__main__":
    run()

#!/usr/bin/env python
"""Environment validation script for the invoice‑processing project.
Checks:
- Python >= 3.11
- Running inside the backend/.venv virtual environment
- All required packages import successfully
- Tesseract binary is callable
- Language data for 'eng' and 'osd' are available
On failure the script prints a concise OS‑specific install hint and exits with non‑zero.
"""
import sys
import subprocess
import importlib
import os

def error(msg: str, hint: str | None = None) -> None:
    print(f"ERROR: {msg}")
    if hint:
        print(f"HINT: {hint}")
    sys.exit(1)

# 1. Python version
if sys.version_info < (3, 11):
    error("Python version is too old", "Install Python >=3.11 and activate the virtual environment.")

# 2. Virtual environment
if getattr(sys, "base_prefix", sys.prefix) == sys.prefix:
    error("Not running inside a virtual environment", "Activate backend/.venv before running scripts.")

# 3. Required packages
required_packages = [
    "fastapi",
    "uvicorn",
    "sqlalchemy",
    "pydantic",
    "pydantic_settings",
    "python_multipart",
    "argon2",  # import name for argon2-cffi
    "jwt",
    "pytesseract",
    "cv2",  # opencv-python-headless provides cv2
    "numpy",
    "PIL",  # Pillow
    "fitz",  # PyMuPDF
    "pdfplumber",
    "rapidfuzz",
    "reportlab",
]
for pkg in required_packages:
    try:
        importlib.import_module(pkg)
    except Exception as exc:
        error(f"Package '{pkg}' cannot be imported: {exc}")

# 4. Tesseract binary
tesseract_cmd = os.getenv("TESSERACT_CMD", "tesseract")
try:
    subprocess.run([tesseract_cmd, "--version"], capture_output=True, check=True, text=True)
except Exception as exc:
    error(
        f"Tesseract binary not found or not executable ({tesseract_cmd})",
        "Install Tesseract (e.g., Windows UB‑Mannheim installer) and set TESSERACT_CMD if not on PATH.",
    )

# Helper to check language data availability
def check_lang(lang: str) -> bool:
    try:
        result = subprocess.run([tesseract_cmd, "--list-langs"], capture_output=True, check=True, text=True)
        return lang in result.stdout.split()
    except Exception:
        return False

for lang in ("eng", "osd"):
    if not check_lang(lang):
        error(
            f"Tesseract language data '{lang}' missing",
            "Install the language pack (e.g., for Windows run the UB‑Mannheim installer and select the language).",
        )

print("ENV OK")
sys.exit(0)

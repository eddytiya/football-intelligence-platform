from pathlib import Path

# ==========================================================
# Project Root
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ==========================================================
# Data Directories
# ==========================================================

DATA_DIR = PROJECT_ROOT / "data"

RAW_DATA_DIR = DATA_DIR / "raw"

PROCESSED_DATA_DIR = DATA_DIR / "processed"

# ==========================================================
# Models
# ==========================================================

MODELS_DIR = PROJECT_ROOT / "models"

TRAINED_MODELS_DIR = MODELS_DIR / "trained_models"

# ==========================================================
# Reports
# ==========================================================

REPORTS_DIR = PROJECT_ROOT / "reports"

# ==========================================================
# Logs
# ==========================================================

LOGS_DIR = PROJECT_ROOT / "logs"

# ==========================================================
# Create directories automatically
# ==========================================================

TRAINED_MODELS_DIR.mkdir(parents=True, exist_ok=True)

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

LOGS_DIR.mkdir(parents=True, exist_ok=True)
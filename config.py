"""Application Configuration"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Reconfigure stdout/stderr to use UTF-8 encoding on Windows to prevent UnicodeEncodeError
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

# Load environment variables
load_dotenv()

# Try to load from Streamlit secrets if available
try:
    import streamlit as st
    if hasattr(st, 'secrets'):
        # Streamlit Cloud deployment
        GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
    else:
        GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
except:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Detect Streamlit Cloud environment
IS_STREAMLIT_CLOUD = os.getenv("STREAMLIT_RUNTIME_ENV") == "cloud" or os.path.exists("/mount/src")

# Set data directory based on environment
if IS_STREAMLIT_CLOUD:
    # Use /tmp for writable storage on Streamlit Cloud
    DATA_DIR = Path("/tmp/knowledgeguard_data")
else:
    DATA_DIR = BASE_DIR

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# API Configuration
GROQ_MODEL = "llama-3.3-70b-versatile"  # Updated to current model

# Database Configuration
if IS_STREAMLIT_CLOUD:
    DATABASE_URL = f"sqlite:///{DATA_DIR}/knowledgeguard.db"
else:
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/knowledgeguard.db")

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Application Settings
APP_NAME = os.getenv("APP_NAME", "KnowledgeGuard AI")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Upload Settings
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".pdf", ".docx", ".txt", ".md"}

# Backup Settings
BACKUP_DIR = DATA_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True, parents=True)
BACKUP_ENABLED = os.getenv("BACKUP_ENABLED", "true").lower() == "true"
BACKUP_INTERVAL_HOURS = int(os.getenv("BACKUP_INTERVAL_HOURS", "24"))

# FAISS Settings
FAISS_INDEX_DIR = DATA_DIR / "faiss_index"
FAISS_INDEX_DIR.mkdir(exist_ok=True, parents=True)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Risk Scoring Thresholds
RISK_THRESHOLDS = {
    "critical": 80,
    "high": 60,
    "medium": 40,
    "low": 0
}

# Logging
LOG_DIR = DATA_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True, parents=True)
LOG_FILE = LOG_DIR / "app.log"

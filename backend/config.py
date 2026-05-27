from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOTENV_PATH = PROJECT_ROOT / ".env"


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue

        key, value = stripped.split("=", 1)
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value


_load_env_file(DOTENV_PATH)


# Project base and companies file
BASE_DIR = Path(__file__).parent  # = D:\FitBot\backend
COMPANIES_FILE = str(BASE_DIR / "companies.json")


@dataclass(frozen=True)
class Settings:
    BASE_DIR: Path = Path(__file__).parent
    COMPANIES_FILE: str = str(Path(__file__).parent / "companies.json")
    BASE_UPLOAD_DIR: str = str(BASE_DIR / "data" / "uploads")
    CHROMA_BASE_DIR: str = str(BASE_DIR / "chroma_store")
    OLLAMA_MODEL: str = "llama3.1:8b"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    TMP_DIR: str = os.getenv("TMP_DIR", "")
    EMBEDDING_MODEL: str = "BAAI/bge-large-en-v1.5"
    EMBEDDING_DEVICE: str = "cuda"
    TOP_K_CHUNKS: int = 12
    EXCEL_CHROMA_DIR: str = str(BASE_DIR / "chroma_store" / "excel")
    EXCEL_FILE_PATH: str = str(BASE_DIR / "data" / "uploads")
    EXCEL_COLLECTION_NAME: str = "excel"
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150


settings = Settings()


def get_settings():
    return settings

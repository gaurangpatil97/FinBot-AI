from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


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
    ENABLE_IMAGE_EMBEDDING: bool = False
    EMBEDDING_MODEL: str = "BAAI/bge-large-en-v1.5"
    EMBEDDING_DEVICE: str = "cuda"
    TOP_K_CHUNKS: int = 12
    EXCEL_FILE_PATH: str = str(BASE_DIR / "data" / "uploads")
    TOP_K_CHUNKS_MULTI: int = 8
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    TOP_K_PDF: int = 8
    TOP_K_CONCALL: int = 8
    MIN_BUDGET_PER_SOURCE: int = 4
    TOP_K_IMAGES: int = 5


settings = Settings()


def get_settings():
    return settings

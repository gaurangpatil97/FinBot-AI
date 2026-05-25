from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    BASE_UPLOAD_DIR: str = str(Path(__file__).parent / "data" / "uploads")
    CHROMA_BASE_DIR: str = str(Path(__file__).parent / "chroma_store")
    OLLAMA_MODEL: str = "llama3.1:8b"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OPENAI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "BAAI/bge-large-en-v1.5"
    EMBEDDING_DEVICE: str = "cuda"
    TOP_K_CHUNKS: int = 6
    EXCEL_CHROMA_DIR: str = "./chroma_store/excel"
    EXCEL_FILE_PATH: str = "./data/uploads"
    EXCEL_COLLECTION_NAME: str = "excel"
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150


settings = Settings()


def get_settings():
    return settings

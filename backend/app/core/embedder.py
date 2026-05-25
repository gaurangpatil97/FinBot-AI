from sentence_transformers import SentenceTransformer
from loguru import logger
from config import settings

logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
model = SentenceTransformer(
    settings.EMBEDDING_MODEL,
    device=settings.EMBEDDING_DEVICE
)
logger.success("Embedding model loaded!")

def generate_embeddings(chunks: list[dict]) -> list[dict]:
    texts = [chunk["content"] for chunk in chunks]
    
    logger.info(f"Generating embeddings for {len(texts)} chunks...")
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True
    )

    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding.tolist()

    logger.success(f"Generated {len(embeddings)} embeddings")
    return chunks

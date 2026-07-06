import gc

import chromadb
from chromadb.config import Settings as ChromaSettings
from loguru import logger
from config import settings

import time
from prometheus_client import Histogram

CHROMA_QUERY_LATENCY = Histogram(
    "chroma_query_latency_seconds",
    "Time spent querying ChromaDB",
    ["collection_type"]
)

def get_persistent_client(path: str):
    client_settings = ChromaSettings(anonymized_telemetry=False)
    last_exc = None
    for attempt in range(3):
        try:
            return chromadb.PersistentClient(
                path=path,
                settings=client_settings,
            )
        except Exception as exc:
            last_exc = exc
            logger.warning(f"Chroma client creation failed for {path} (attempt {attempt+1}/3): {exc}. Retrying in 0.5s.")
            time.sleep(0.5)
    logger.error(f"Chroma client creation failed for {path} after 3 attempts: {last_exc}")
    raise last_exc
def get_or_create_collection(collection_name: str, chroma_path: str = None):
    path = chroma_path or settings.CHROMA_BASE_DIR
    local_client = get_persistent_client(path)
    collection = local_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    logger.info(f"Collection ready: {collection_name}")
    return collection

def store_chunks(chunks: list[dict], collection_name: str, chroma_path: str = None):
    # Use provided chroma_path if given, otherwise fall back to configured path
    path = chroma_path or settings.CHROMA_BASE_DIR
    client_local = get_persistent_client(path)

    collection = client_local.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        chunk_type = chunk["metadata"].get("chunk_type", "text")
        if "page" in chunk["metadata"]:
            chunk_id = (
                f"{chunk['metadata']['filename']}_p{chunk['metadata']['page']}_"
                f"c{chunk['metadata']['chunk_index']}_{chunk_type}"
            )
        else:
            chunk_id = (
                f"{chunk['metadata']['filename']}_{chunk['metadata'].get('sheet', 'unknown')}_"
                f"{chunk['metadata'].get('year', 'unknown')}_c{chunk['metadata'].get('chunk_index', 0)}_"
                f"{chunk['metadata'].get('chunk_type', 'text')}"
            )

        ids.append(chunk_id)
        embeddings.append(chunk["embedding"])
        documents.append(chunk["content"])

        meta = chunk["metadata"].copy()
        meta["collection"] = collection_name
        metadatas.append(meta)

    batch_size = 5000
    for i in range(0, len(ids), batch_size):
        collection.upsert(
            ids=ids[i:i+batch_size],
            embeddings=embeddings[i:i+batch_size],
            documents=documents[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size]
        )
        logger.info(f"Stored batch {i//batch_size + 1}")

    logger.success(f"Stored {len(chunks)} chunks in '{collection_name}'")

def query_collection(
    query_embedding: list[float],
    collection_name: str,
    top_k: int = None,
    year: str = None,
    sheet: str = None,
    filename: str = None,
    quarter: str = None,
    chroma_path: str = None
) -> list[dict]:
    top_k = top_k or settings.TOP_K_CHUNKS
    collection = get_or_create_collection(collection_name, chroma_path=chroma_path)

    if isinstance(year, list):
        year = year[0] if year else None

    where_clauses = []
    if year:
        where_clauses.append({"year": year})
    if sheet:
        where_clauses.append({"sheet": sheet})
    if filename:
        where_clauses.append({"filename": filename})
    if quarter:
        where_clauses.append({"quarter": quarter})

    if len(where_clauses) == 0:
        where = None
    elif len(where_clauses) == 1:
        where = where_clauses[0]
    else:
        where = {"$and": where_clauses}

    # determine basic type for metrics
    c_type = collection_name.split('_')[-1] if '_' in collection_name else collection_name
    
    with CHROMA_QUERY_LATENCY.labels(collection_type=c_type).time():
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"]
        )

    if year and len(results["documents"][0]) == 0:
        # Wrong year data is worse than no data — let caller handle missing year
        logger.warning(f"Year filter '{year}' returned 0 results; returning empty list")
        return []

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        chunks.append({
            "content": doc,
            "metadata": meta,
            "score": 1 - dist
        })

    logger.info(f"Retrieved {len(chunks)} chunks from '{collection_name}'")
    return chunks

def query_collection_by_type(
    query_embedding: list[float],
    collection_name: str,
    chunk_type: str,
    top_k: int = 3,
    year: str = None,
    chroma_path: str = None
) -> list[dict]:
    # Allow querying a different ChromaDB instance by path
    path = chroma_path or settings.CHROMA_BASE_DIR
    client_local = get_persistent_client(path)
    collection = client_local.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

    where = {"chunk_type": chunk_type}
    if year:
        where = {"$and": [{"chunk_type": chunk_type}, {"year": year}]}

    try:
        c_type = collection_name.split('_')[-1] if '_' in collection_name else collection_name
        with CHROMA_QUERY_LATENCY.labels(collection_type=c_type).time():
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where,
                include=["documents", "metadatas", "distances"]
            )

        chunks = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            chunks.append({
                "content": doc,
                "metadata": meta,
                "score": 1 - dist
            })

        logger.info(f"Retrieved {len(chunks)} image chunks from '{collection_name}'")
        return chunks

    except Exception as e:
        logger.error(f"Image chunk query failed: {e}")
        return []

"""Qdrant collection setup and product catalogue ingestion."""

import json
from pathlib import Path

from qdrant_client import QdrantClient, models

from lodestar.config import settings
from lodestar.rag.embeddings import embed_texts

COLLECTION_NAME = "products"
CATALOGUE_PATH = Path(__file__).parent.parent / "data" / "products_catalogue.json"


def get_qdrant_client() -> QdrantClient:
    """Get a Qdrant client in embedded (local) mode.

    Returns:
        QdrantClient pointing at the configured path.
    """
    settings.ensure_dirs()
    return QdrantClient(path=settings.qdrant_path)


def create_collection(client: QdrantClient) -> None:
    """Create the products collection with dense vector config.

    Args:
        client: Qdrant client instance.
    """
    if client.collection_exists(COLLECTION_NAME):
        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE),
    )

    client.create_payload_index(COLLECTION_NAME, "product_type", models.PayloadSchemaType.KEYWORD)
    client.create_payload_index(COLLECTION_NAME, "entity", models.PayloadSchemaType.KEYWORD)
    client.create_payload_index(COLLECTION_NAME, "min_income", models.PayloadSchemaType.FLOAT)
    client.create_payload_index(COLLECTION_NAME, "interest_rate", models.PayloadSchemaType.FLOAT)


def ingest_products(client: QdrantClient) -> int:
    """Ingest the product catalogue into Qdrant with embeddings.

    Args:
        client: Qdrant client instance.

    Returns:
        Number of products indexed.
    """
    with open(CATALOGUE_PATH) as f:
        products = json.load(f)

    # Embed all three locales in a single document so bge-m3 anchors each
    # product across Vi/En/Ko vocabulary. Previously Vietnamese-only, which
    # made English or Korean queries rely on bge-m3's cross-lingual
    # generalisation alone and degraded precision.
    texts = [
        " — ".join(
            part
            for part in (
                p.get("name_vi", ""),
                p.get("name_en", ""),
                p.get("name_ko", ""),
                p.get("description_vi", ""),
                p.get("description_en", ""),
                p.get("description_ko", ""),
                p.get("product_type", ""),
            )
            if part
        )
        for p in products
    ]

    dense_vecs = embed_texts(texts)

    points = []
    for i, product in enumerate(products):
        points.append(
            models.PointStruct(
                id=i + 1,
                vector=dense_vecs[i],
                payload={
                    "product_id": product["product_id"],
                    "entity": product["entity"],
                    "product_type": product["product_type"],
                    "name_vi": product["name_vi"],
                    "name_en": product.get("name_en", ""),
                    "name_ko": product.get("name_ko", ""),
                    "description_vi": product.get("description_vi", ""),
                    "description_en": product.get("description_en", ""),
                    "description_ko": product.get("description_ko", ""),
                    "interest_rate": product.get("interest_rate"),
                    "min_income": product.get("min_income", 0),
                    "eligibility_criteria": product.get("eligibility_criteria", {}),
                },
            )
        )

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)


PAYLOAD_SCHEMA_VERSION = 3  # bump whenever the stored payload shape OR embedding recipe changes
_SCHEMA_MARKER_KEY = "_schema_version"


def init_rag() -> int:
    """Initialise the RAG pipeline: create collection and ingest products.

    Re-ingests whenever the stored schema version is missing or older than
    PAYLOAD_SCHEMA_VERSION. Bumping the constant above forces a wipe so
    callers don't have to remember to clear the Qdrant cache when the
    embedding recipe changes.

    Returns:
        Number of products indexed.
    """
    client = get_qdrant_client()
    create_collection(client)

    info = client.get_collection(COLLECTION_NAME)
    points_count = info.points_count or 0
    if points_count > 0 and _stored_schema_version(client) >= PAYLOAD_SCHEMA_VERSION:
        return points_count

    if points_count > 0:
        client.delete_collection(COLLECTION_NAME)
        create_collection(client)
    count = ingest_products(client)
    _write_schema_marker(client)
    return count


def _stored_schema_version(client: QdrantClient) -> int:
    """Return the schema version recorded on the first stored point, or 0
    when the marker is missing (pre-versioned ingests)."""
    try:
        points, _ = client.scroll(collection_name=COLLECTION_NAME, limit=1, with_payload=True)
    except Exception:
        return 0
    if not points:
        return 0
    payload = points[0].payload or {}
    return int(payload.get(_SCHEMA_MARKER_KEY, 0))


def _write_schema_marker(client: QdrantClient) -> None:
    """Stamp every stored point with the current schema version so the next
    boot can tell whether to re-ingest."""
    try:
        points, _ = client.scroll(collection_name=COLLECTION_NAME, limit=1000, with_payload=False)
    except Exception:
        return
    ids = [p.id for p in points]
    if not ids:
        return
    client.set_payload(
        collection_name=COLLECTION_NAME,
        payload={_SCHEMA_MARKER_KEY: PAYLOAD_SCHEMA_VERSION},
        points=ids,
    )

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

    texts = [
        f"{p['name_vi']} — {p.get('description_vi', '')} — {p['product_type']}"
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


PAYLOAD_SCHEMA_VERSION = 2  # bump whenever the stored payload shape changes


def init_rag() -> int:
    """Initialise the RAG pipeline: create collection and ingest products.

    Re-ingests when the existing collection lacks the current payload
    schema (missing name_ko / description_ko). This keeps Qdrant in sync
    with the Vi/En/Ko catalogue without manual cache wipes.

    Returns:
        Number of products indexed.
    """
    client = get_qdrant_client()
    create_collection(client)

    info = client.get_collection(COLLECTION_NAME)
    points_count = info.points_count or 0
    if points_count > 0 and _payload_has_korean(client):
        return points_count

    # Stale schema or empty — wipe and re-ingest.
    if points_count > 0:
        client.delete_collection(COLLECTION_NAME)
        create_collection(client)
    return ingest_products(client)


def _payload_has_korean(client: QdrantClient) -> bool:
    """Return True if the first stored point already carries a name_ko
    field. Cheap probe used to decide whether to re-ingest on startup."""
    try:
        points, _ = client.scroll(collection_name=COLLECTION_NAME, limit=1, with_payload=True)
    except Exception:
        return False
    if not points:
        return False
    payload = points[0].payload or {}
    return "name_ko" in payload

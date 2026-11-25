
import json
from pathlib import Path

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct
)

ROOT = Path(__file__).resolve().parents[1]

COLLECTION = "novaskill_knowledge"
MODEL_NAME = "all-MiniLM-L6-v2"


def main():

    print("Loading business knowledge...")

    path = ROOT / "knowledge_base" / "courses.json"

    with open(path, encoding="utf-8") as file:
        documents = json.load(file)

    print("Loading embedding model...")

    model = SentenceTransformer(MODEL_NAME)

    client = QdrantClient(
        path=str(ROOT / "qdrant_storage")
    )

    try:

        if client.collection_exists(COLLECTION):
            client.delete_collection(COLLECTION)

        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE
            )
        )

        texts = [
            f"{doc['title']}: {doc['content']}"
            for doc in documents
        ]

        embeddings = model.encode(
            texts,
            normalize_embeddings=True
        )

        points = [
            PointStruct(
                id=doc["id"],
                vector=embedding.tolist(),
                payload=doc
            )
            for doc, embedding in zip(
                documents, embeddings
            )
        ]

        client.upsert(
            collection_name=COLLECTION,
            points=points,
            wait=True
        )

        print(
            f"Successfully ingested "
            f"{len(points)} knowledge records."
        )

    finally:
        client.close()


if __name__ == "__main__":
    main()

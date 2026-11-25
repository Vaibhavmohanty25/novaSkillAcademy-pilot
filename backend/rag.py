
from pathlib import Path
from threading import Lock

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

ROOT = Path(__file__).resolve().parents[1]

COLLECTION = "novaskill_knowledge"
MODEL_NAME = "all-MiniLM-L6-v2"


class KnowledgeEngine:

    def __init__(self):

        print("Initializing RAG engine...")

        self.model = SentenceTransformer(
            MODEL_NAME
        )

        self.client = QdrantClient(
            path=str(ROOT / "qdrant_storage")
        )

        self.lock = Lock()

        if not self.client.collection_exists(
            COLLECTION
        ):
            self.client.close()
            raise RuntimeError(
                "Knowledge collection missing. "
                "Run python -m scripts.ingest first."
            )

        print("RAG engine initialized.")

    def search(self, query: str):

        query = query.strip()

        if not query:
            return {
                "found": False,
                "documents": []
            }

        with self.lock:

            embedding = self.model.encode(
                query,
                normalize_embeddings=True
            ).tolist()

            results = self.client.query_points(
                collection_name=COLLECTION,
                query=embedding,
                limit=3,
                score_threshold=0.35
            ).points

        documents = [
            {
                "source": result.payload["title"],
                "content": result.payload["content"],
                "score": round(result.score, 3)
            }
            for result in results
        ]

        return {
            "found": bool(documents),
            "documents": documents
        }

    def close(self):
        self.client.close()


knowledge_engine = KnowledgeEngine()

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from core.datastore.protocol import DataStore
from core.embedding.openai_embedding_model import EMBED_DIM

class QdrantDataStore(DataStore):
    
    def __init__(
        self,
        url="http://localhost:6333",
        api_key=None,
        collection="docs",
        dim=EMBED_DIM):

        self.client = QdrantClient(url=url, api_key=api_key, timeout=30)
        self.collection = collection
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE)
            )

    def upsert(
        self,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict[str, str]],
    ) -> None:

        points = [PointStruct(id=ids[i], vector=vectors[i], payload=payloads[i]) for i in range(len(ids))]
        self.client.upsert(self.collection, points=points)

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5
    ) -> dict[str, list[str]]:

        results = self.client.query_points(
            collection_name=self.collection,
            query=query_vector,
            with_payload=True,
            limit=top_k
        ).points
        contexts = []
        sources = set()

        for r in results:
            payload = getattr(r, "payload", None) or {}
            text = payload.get("text", "")
            source = payload.get("source", "")
            if text:
                contexts.append(text)
                sources.add(source)

        return {"contexts": contexts, "sources": list(sources)}
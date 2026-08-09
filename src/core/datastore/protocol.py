from typing import Protocol, Any

class DataStore(Protocol):
    def upsert(
        self, 
        ids: list[str], 
        vectors: list[list[float]], 
        payloads: list[dict[str, str]]) -> None:
        ...

    def search(
        self,
        query_vector,
        top_k: int = 5) -> dict[str, list[str]]:
        ...
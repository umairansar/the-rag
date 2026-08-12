from typing import Protocol

class EmbeddingModel(Protocol):
    def generate(
        self,
        texts: list[str],
        model: str,
        dimensions: int
    ) -> list[list[float]]:
        ...
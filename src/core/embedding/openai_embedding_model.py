from openai import OpenAI
from core.embedding.protocol import EmbeddingModel

EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 768

class OpenAIEmbeddingModel(EmbeddingModel):
    def __init__(
        self, 
        api_key: str):

        self.model = OpenAI(api_key=api_key)

    def generate(
        self,
        texts: list[str],
        model: str = EMBED_MODEL,
        dimensions: int = EMBED_DIM
    ) -> list[list[float]]:

        response = self.model.embeddings.create(
            input=texts, model=model, dimensions=dimensions
        )
        return [data.embedding for data in sorted(response.data, key=lambda x: x.index)]

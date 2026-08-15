from dotenv import load_dotenv
import os
from core.inngest.client import create_inngest_client
from core.embedding.openai_embedding_model import OpenAIEmbeddingModel
from core.datastore.qdrant_datastore import QdrantDataStore
from core.llm.anthropic import AnthropicLlM

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

inngest_client = create_inngest_client()
vector_store = QdrantDataStore(url=QDRANT_URL, api_key=QDRANT_API_KEY)
embedding_model = OpenAIEmbeddingModel(api_key=OPENAI_API_KEY)
llm = AnthropicLlM(api_key=ANTHROPIC_API_KEY)

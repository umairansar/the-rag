import os

from dotenv import load_dotenv

from core.datastore.qdrant_datastore import QdrantDataStore
from core.embedding.openai_embedding_model import OpenAIEmbeddingModel
from core.inngest.client import create_inngest_client
from core.llm.anthropic import AnthropicLlM
from core.objectstore.r2_objectstore import R2ObjectStore

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CLOUDFLARE_S3_API = os.getenv("CLOUDFLARE_S3_API")
CLOUDFLARE_ACCESS_KEY_ID = os.getenv("CLOUDFLARE_ACCESS_KEY_ID")
CLOUDFLARE_SECRET_ACCESS_KEY = os.getenv("CLOUDFLARE_SECRET_ACCESS_KEY")

inngest_client = create_inngest_client()
vector_store = QdrantDataStore(url=QDRANT_URL, api_key=QDRANT_API_KEY)
embedding_model = OpenAIEmbeddingModel(api_key=OPENAI_API_KEY)
llm = AnthropicLlM(api_key=ANTHROPIC_API_KEY)
object_store = R2ObjectStore(
    endpoint_url=CLOUDFLARE_S3_API,
    aws_access_key_id=CLOUDFLARE_ACCESS_KEY_ID,
    aws_secret_access_key=CLOUDFLARE_SECRET_ACCESS_KEY
    )
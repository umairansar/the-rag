import os
from dotenv import load_dotenv
from openai import OpenAI
from llama_index.readers.file import PDFReader
from llama_index.core.node_parser import SentenceSplitter

load_dotenv()

EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 768

splitter = SentenceSplitter(chunk_size=1000, chunk_overlap=200)
_model = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_and_chunk_pdf(path: str):
    docs = PDFReader().load_data(file=path)
    texts = [d.text for d in docs if getattr(d, "text", None)]
    chunks = []
    for t in texts:
        chunks.extend(splitter.split_text(t))
    return chunks

def embed_texts(texts: list[str]) -> list[list[float]]:
    response = _model.embeddings.create(
          input=texts, model=EMBED_MODEL, dimensions=EMBED_DIM
    )
    return [data.embedding for data in sorted(response.data, key=lambda x: x.index) ]

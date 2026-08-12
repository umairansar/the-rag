from fastapi import FastAPI
import inngest
import inngest.fast_api
from inngest.experimental import ai, realtime
from dotenv import load_dotenv
import uuid
import os
import datetime
from rag.data_loader import load_and_chunk_pdf
from rag.schemas import RAGChunkAndSrc, RAGUpsertResult, RAGSearchResult, RAGQueryResult
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

'''
{
  "data": {
    "pdf_path":"C:\\Users\\umair\\Downloads\\Umair Resume _ Temu.pdf"
  }
}
'''
@inngest_client.create_function(
    fn_id="RAG: Ingest PDF",
    trigger=inngest.TriggerEvent(event="rag/ingest_pdf")
)
async def rag_ingest_pdf(ctx: inngest.Context):
    def _load(ctx: inngest.Context) -> RAGChunkAndSrc:
        pdf_path = ctx.event.data["pdf_path"]
        source_id = ctx.event.data.get("source_id", pdf_path)
        chunks = load_and_chunk_pdf(pdf_path)
        return RAGChunkAndSrc(chunks=chunks, source_id=source_id)

    def _upsert(chunk_and_src: RAGChunkAndSrc) -> RAGUpsertResult:
        chunks = chunk_and_src.chunks
        source_id = chunk_and_src.source_id
        vecs = embedding_model.generate(chunks)
        ids = [str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source_id}:{i}")) for i in range(len(chunks))]
        payloads = [{"source": source_id, "text": chunks[i]} for i in range(len(chunks))]
        vector_store.upsert(ids, vecs, payloads)
        return RAGUpsertResult(ingested=len(chunks))

    chunks_and_src = await ctx.step.run("load-and-chunk", lambda: _load(ctx), output_type=RAGChunkAndSrc)
    ingested = await ctx.step.run("embed-and-upsert", lambda: _upsert(chunks_and_src), output_type=RAGUpsertResult)
    return ingested.model_dump()

'''
{
  "data": {
    "question":"Does umair have any work experience? Give 2 liner."
  }
}
'''
@inngest_client.create_function(
    fn_id="RAG: Query PDF",
    trigger=inngest.TriggerEvent(event="rag/query_pdf")
)
async def rag_query_pdf_ai(ctx: inngest.Context):
    def _search(question: str, top_k: int = 5) -> RAGSearchResult:
        query_vec = embedding_model.generate([question])[0]
        found = vector_store.search(query_vec, top_k)
        return RAGSearchResult(contexts=found["contexts"], sources=found["sources"])

    async def _generate(prompt: str) -> str:
        # answer = []
        # with llm.messages.stream(
        #     model="claude-haiku-4-5-20251001",
        #     max_tokens=1024,
        #     messages=[{"role": "user", "content": prompt}]
        # ) as stream:
        #     for text in stream.text_stream:
        #         await realtime.publish(
        #             client=inngest_client,
        #             channel="user:anonymous",
        #             topic="messages",
        #             data={"text": text},
        #         )
        #         answer.append(text)
        # return "".join(answer)
        return llm.generate_answer(prompt)

    question = ctx.event.data["question"]
    top_k = ctx.event.data.get("top_k", 5)

    found = await ctx.step.run("embed-and-search", lambda: _search(question, top_k), output_type=RAGSearchResult)
    
    context_block = "\n\n".join(f"- {c}" for c in found.contexts)
    user_content = (
        "Use the following context to answer the questions.\n\n"
        f"Context:\n{context_block}\n\n"
        f"Question: {question}\n"
        "Answer concisely using the context above."
    )

    answer = await ctx.step.run("generate", lambda: _generate(user_content), output_type=str)
    return RAGQueryResult(answer=answer, sources=found.sources, num_contexts=len(found.contexts)).model_dump()

app = FastAPI()

inngest.fast_api.serve(app, inngest_client, [rag_ingest_pdf, rag_query_pdf_ai], serve_origin=os.getenv("SERVE_ORIGIN", "http://127.0.0.1:8001"))
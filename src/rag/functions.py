import datetime
import uuid
from pathlib import Path

import inngest

from core.deps import embedding_model, inngest_client, llm, object_store, vector_store
from core.objectstore.enums import PresignedUrlMode
from rag.data_loader import load_and_chunk_pdf
from rag.schemas import (
    IngestStatus,
    RAGChunkAndSrc,
    RAGIngestResult,
    RAGQueryResult,
    RAGSearchResult,
    RAGUpsertResult,
)

'''
{
  "data": {
    "pdf_path":"C:\\Users\\umair\\Downloads\\Umair Resume _ Temu.pdf"
  }
}
'''
@inngest_client.create_function(
    fn_id="RAG: Ingest PDF [deprecated]",
    trigger=inngest.TriggerEvent(event="rag/v1/ingest_pdf")
)
async def rag_ingest_pdf_deprecated(ctx: inngest.Context):
    def _load(ctx: inngest.Context) -> RAGChunkAndSrc:
        pdf_path = ctx.event.data["pdf_path"]
        source_id = ctx.event.data.get("source_id", pdf_path)
        data = Path(pdf_path).read_bytes()
        chunks = load_and_chunk_pdf(data)
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
    return RAGIngestResult(status=IngestStatus.COMPLETED).model_dump(mode="json")

@inngest_client.create_function(
    fn_id="RAG: Upload PDF",
    trigger=inngest.TriggerEvent(event="rag/v2/upload_pdf")
)
async def rag_upload_pdf(ctx: inngest.Context):
    def _presign(ctx: inngest.Context) -> RAGIngestResult:
        file_name = ctx.event.data["file_name"]
        object_key = f"pdf/{uuid.uuid4()}-{file_name}"
        url = object_store.generate_presigned_url(
            mode=PresignedUrlMode.PUT,
            bucket="rag-parking",
            key=object_key,
            expires_in=300,
        )
        return RAGIngestResult(status=IngestStatus.STARTED, file_url=url, file_key=object_key)

    result = await ctx.step.run("generate-presigned-url", lambda: _presign(ctx), output_type=RAGIngestResult)
    return result.model_dump(mode="json")

@inngest_client.create_function(
    fn_id="RAG: Ingest PDF",
    throttle=inngest.Throttle(
        limit=5,
        period=datetime.timedelta(seconds=60),
        burst=2
    ),
    trigger=inngest.TriggerEvent(event="rag/v2/ingest_pdf")
)
async def rag_ingest_pdf(ctx: inngest.Context):
    def _load(ctx: inngest.Context) -> RAGChunkAndSrc:
        file_key = ctx.event.data["file_key"]
        presigned_url = object_store.generate_presigned_url(
            mode=PresignedUrlMode.GET,
            bucket="rag-parking",
            key=file_key,
            expires_in=300,
        )
        data = object_store.get_file(presigned_url=presigned_url)
        chunks = load_and_chunk_pdf(data)
        return RAGChunkAndSrc(chunks=chunks, source_id=file_key)

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
    return RAGIngestResult(status=IngestStatus.COMPLETED if ingested.ingested > 0 else IngestStatus.FAILED).model_dump(mode="json")
    

'''
{
  "data": {
    "question":"Does umair have any work experience? Give 2 liner."
  }
}
'''
@inngest_client.create_function(
    fn_id="RAG: Query PDF",
    trigger=inngest.TriggerEvent(event="rag/v1/query_pdf")
)
async def rag_query_pdf(ctx: inngest.Context):
    def _search(question: str, top_k: int = 5) -> RAGSearchResult:
        query_vec = embedding_model.generate([question])[0]
        found = vector_store.search(query_vec, top_k)
        return RAGSearchResult(contexts=found["contexts"], sources=found["sources"])

    question = ctx.event.data["question"]
    top_k = ctx.event.data.get("top_k", 5)

    found = await ctx.step.run("embed-and-search", lambda: _search(question, top_k), output_type=RAGSearchResult)

    context_block = "\n\n".join(f"- {c}" for c in found.contexts)
    prompt = (
        "Use the following context to answer the questions.\n\n"
        f"Context:\n{context_block}\n\n"
        f"Question: {question}\n"
        "Answer concisely using the context above."
    )

    answer = await ctx.step.run("generate", lambda: llm.generate_answer(prompt), output_type=str)
    return RAGQueryResult(answer=answer, sources=found.sources, num_contexts=len(found.contexts)).model_dump()

from fastapi import FastAPI
import inngest.fast_api
import os
from rag.functions import inngest_client, rag_ingest_pdf, rag_query_pdf_ai

app = FastAPI()

inngest.fast_api.serve(
    app,
    inngest_client,
    [rag_ingest_pdf, rag_query_pdf_ai],
    serve_origin=os.getenv("SERVE_ORIGIN", "http://127.0.0.1:8001"))

import os

import inngest.fast_api
from fastapi import FastAPI

from rag.functions import (
    inngest_client,
    rag_ingest_pdf,
    rag_ingest_pdf_deprecated,
    rag_query_pdf,
    rag_upload_pdf,
)

app = FastAPI()

inngest.fast_api.serve(
    app,
    inngest_client,
    [rag_ingest_pdf_deprecated, rag_upload_pdf, rag_ingest_pdf, rag_query_pdf],
    serve_origin=os.getenv("SERVE_ORIGIN", "http://127.0.0.1:8001"))

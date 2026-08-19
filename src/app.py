import asyncio
import nest_asyncio
from pathlib import Path
import time

import streamlit as st

nest_asyncio.apply()
import inngest
from dotenv import load_dotenv
import os
import requests

load_dotenv()

st.set_page_config(page_title="RAG Ingest PDF", page_icon="📄", layout="centered")


@st.cache_resource
def get_inngest_client() -> inngest.Inngest:
    return inngest.Inngest(app_id="rag_app", is_production=False)


def save_uploaded_pdf(file) -> Path:
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    file_path = uploads_dir / file.name
    file_bytes = file.getbuffer()
    file_path.write_bytes(file_bytes)
    return file_path


async def send_rag_ingest_event(pdf_path: Path) -> None:
    client = get_inngest_client()
    await client.send(
        inngest.Event(
            name="rag/v1/ingest_pdf",
            data={
                "pdf_path": str(pdf_path.resolve()),
                "source_id": pdf_path.name,
            },
        )
    )


def _inngest_api_base() -> str:
    # Local dev server default; configurable via env
    return os.getenv("INNGEST_API_BASE", "http://127.0.0.1:8288/v1")


def fetch_runs(event_id: str) -> list[dict]:
    url = f"{_inngest_api_base()}/events/{event_id}/runs"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    return data.get("data", [])


def wait_for_run_output(event_id: str, timeout_s: float = 120.0, poll_interval_s: float = 0.5) -> dict:
    start = time.time()
    last_status = None
    while True:
        runs = fetch_runs(event_id)
        if runs:
            run = runs[0]
            status = run.get("status")
            last_status = status or last_status
            if status in ("Completed", "Succeeded", "Success", "Finished"):
                return run.get("output") or {}
            if status in ("Failed", "Cancelled"):
                raise RuntimeError(f"Function run {status}")
        if time.time() - start > timeout_s:
            raise TimeoutError(f"Timed out waiting for run output (last status: {last_status})")
        time.sleep(poll_interval_s)


async def send_rag_upload_event(file_name: str) -> str:
    client = get_inngest_client()
    result = await client.send(
        inngest.Event(name="rag/v2/upload_pdf", data={"file_name": file_name})
    )
    return result[0]


async def send_rag_ingest_v2_event(file_key: str) -> str:
    client = get_inngest_client()
    result = await client.send(
        inngest.Event(name="rag/v2/ingest_pdf", data={"file_key": file_key})
    )
    return result[0]


title_col, flow_col = st.columns([3, 1])
with title_col:
    st.title("Upload a PDF to Ingest")
with flow_col:
    ingest_flow = st.segmented_control(
        "Ingest flow",
        ["Deprecated", "New"],
        default="Deprecated",
        required=True,
        label_visibility="collapsed",
        help="Deprecated: local upload. New: R2 presigned upload.",
    )

uploaded = st.file_uploader("Choose a PDF", type=["pdf"], accept_multiple_files=False)

if uploaded is not None:
    if ingest_flow == "Deprecated":
        with st.spinner("Uploading and triggering ingestion..."):
            path = save_uploaded_pdf(uploaded)
            # Kick off the event and block until the send completes
            asyncio.run(send_rag_ingest_event(path))
            # Small pause for user feedback continuity
            time.sleep(0.3)
        st.success(f"Triggered ingestion for: {path.name}")
    else:
        with st.spinner("Requesting presigned upload URL..."):
            upload_event_id = asyncio.run(send_rag_upload_event(uploaded.name))
            upload_output = wait_for_run_output(upload_event_id)
            file_url = upload_output.get("file_url")
            file_key = upload_output.get("file_key")

        if not file_url or not file_key:
            st.error(f"Failed to get presigned URL: {upload_output}")
        else:
            with st.spinner("Uploading file to R2..."):
                # Content-Type must match what the presigned URL was signed with,
                # or R2 rejects the upload with 403 SignatureDoesNotMatch
                put_resp = requests.put(
                    file_url,
                    data=uploaded.getvalue(),
                    headers={"Content-Type": "application/pdf"},
                )
                put_resp.raise_for_status()

            with st.spinner("Triggering ingestion..."):
                ingest_event_id = asyncio.run(send_rag_ingest_v2_event(file_key))
                ingest_output = wait_for_run_output(ingest_event_id)

            st.success(f"Ingestion status: {ingest_output.get('status')}")
    st.caption("You can upload another PDF if you like.")

st.divider()
st.title("Ask a question about your PDFs")


async def send_rag_query_event(question: str, top_k: int) -> None:
    client = get_inngest_client()
    result = await client.send(
        inngest.Event(
            name="rag/v1/query_pdf",
            data={
                "question": question,
                "top_k": top_k,
            },
        )
    )

    return result[0]


with st.form("rag_query_form"):
    question = st.text_input("Your question")
    top_k = st.number_input("How many chunks to retrieve", min_value=1, max_value=20, value=5, step=1)
    submitted = st.form_submit_button("Ask")

    if submitted and question.strip():
        with st.spinner("Sending event and generating answer..."):
            # Fire-and-forget event to Inngest for observability/workflow
            event_id = asyncio.run(send_rag_query_event(question.strip(), int(top_k)))
            # Poll the local Inngest API for the run's output
            output = wait_for_run_output(event_id)
            answer = output.get("answer", "")
            sources = output.get("sources", [])

        st.subheader("Answer")
        st.write(answer or "(No answer)")
        if sources:
            st.caption("Sources")
            for s in sources:
                st.write(f"- {s}")
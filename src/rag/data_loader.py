import fitz
from llama_index.core.node_parser import SentenceSplitter

splitter = SentenceSplitter(chunk_size=1000, chunk_overlap=200)

def load_and_chunk_pdf(data: bytes):
    document = fitz.open(stream=data, filetype="pdf")
    full_text = "\n".join(page.get_text() for page in document)
    return splitter.split_text(full_text)
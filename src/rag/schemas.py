from pydantic import AnyUrl, BaseModel, field_serializer

from rag.enums import IngestStatus

'''
pydantic.BaseModel provides runtime typesafety
'''

class RAGChunkAndSrc(BaseModel):
    chunks: list[str]
    source_id: str = None

class RAGUpsertResult(BaseModel):
    ingested: int

class RAGIngestResult(BaseModel):
    status: IngestStatus
    file_url: AnyUrl | None = None
    file_key: str | None = None

    @field_serializer("status")
    def serialize(self, status: IngestStatus, _info) -> str:
        return status.name

class RAGSearchResult(BaseModel):
    contexts: list[str]
    sources: list[str]

class RAGQueryResult(BaseModel):
    answer: str
    sources: list[str]
    num_contexts: int
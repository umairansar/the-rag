import logging
import inngest

def create_inngest_client(
    app_id: str = "rag_app",
    is_production: bool = False
) -> inngest.Inngest:
    return inngest.Inngest(
        app_id=app_id,
        logger=logging.getLogger("uvicorn"),
        is_production=is_production,
        serializer=inngest.PydanticSerializer(),
    )

from typing import Protocol

from pydantic import AnyUrl

from core.objectstore.enums import PresignedUrlMode


class ObjectStore(Protocol):
    def generate_presigned_url(
        self,
        mode: PresignedUrlMode,
        bucket: str,
        key: str,
        expires_in: int
    ) -> str:
        ...

    def get_file(
        self,
        presigned_url: AnyUrl
    ) -> bytes:
        ...
import boto3
import requests
from pydantic import AnyUrl

from core.objectstore.enums import PresignedUrlMode
from core.objectstore.protocol import ObjectStore


class R2ObjectStore(ObjectStore):

    def __init__(
        self,
        endpoint_url,
        aws_access_key_id,
        aws_secret_access_key
    ):
        self.s3 = boto3.client(
            service_name="s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name="auto",
        )

    def generate_presigned_url(
        self,
        mode: PresignedUrlMode,
        bucket: str,
        key: str,
        expires_in: int
    ) -> str:
        params = {'Bucket': bucket, 'Key': key}
        if mode == PresignedUrlMode.PUT:
            params['ContentType'] = 'application/pdf'

        return self.s3.generate_presigned_url(
            mode.value,
            Params=params,
            ExpiresIn=3600
        )

    def get_file(
        self,
        presigned_url: AnyUrl
    ) -> bytes:
        response = requests.get(presigned_url)
        response.raise_for_status()
        return response.content
from enum import Enum


class PresignedUrlMode(str, Enum):
    GET = "get_object"
    PUT = "put_object"
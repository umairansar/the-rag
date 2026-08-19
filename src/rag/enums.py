from enum import Enum


class IngestStatus(int, Enum):
    STARTED = 1
    PROCESSING = 2
    COMPLETED = 3
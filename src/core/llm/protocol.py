from typing import Protocol, Iterable

class Llm(Protocol):
    def generate_answer(
        self, 
        prompt: str
    ) -> str:
        ...

    def stream_answer(
        self,
        prompt: str
    ) -> Iterable[str]:
        ...

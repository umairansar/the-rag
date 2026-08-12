import anthropic
from typing import Iterable
from core.llm.protocol import Llm

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 1024

class AnthropicLlM(Llm):
    def __init__(
        self,
        api_key: str):

        self.model = anthropic.Anthropic(api_key=api_key)

    def generate_answer(
        self, 
        prompt: str
    ) -> str:
        
        response = self.model.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    def stream_answer(
        self,
        prompt: str
    ) -> Iterable[str]:
        
        with self.model.messages.stream(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for text in stream.text_stream:
                yield text

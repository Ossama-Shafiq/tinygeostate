from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass
class ModelResponse:
    text: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None


class ModelClient(Protocol):
    name: str

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
    ) -> ModelResponse:
        ...

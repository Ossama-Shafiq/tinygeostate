from dataclasses import dataclass
from typing import Any, Optional, Protocol


@dataclass
class ModelResponse:
    text: str
    thinking: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    done_reason: Optional[str] = None


class ModelClient(Protocol):
    name: str

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        response_format: Optional[Any] = None,
    ) -> ModelResponse:
        ...
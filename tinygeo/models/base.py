from dataclasses import dataclass, field
from typing import Any, Optional, Protocol


@dataclass
class ModelResponse:
    text: str
    thinking: Optional[str] = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
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
        num_predict: Optional[int] = None,
    ) -> ModelResponse:
        ...

    def chat(
        self,
        messages: list[dict[str, Any]],
        response_format: Optional[Any] = None,
        num_predict: Optional[int] = None,
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> ModelResponse:
        ...
import json
import urllib.error
import urllib.request
from typing import Any, Optional

from tinygeo.models.base import ModelResponse


class OllamaClient:
    def __init__(
        self,
        model: str,
        host: str = "http://localhost:11434",
        think: bool = True,
        num_predict: int = 4096,
    ):
        self.model = model
        self.host = host.rstrip("/")
        self.think = think
        self.num_predict = num_predict

        self.name = f"ollama/{model}"

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        response_format: Optional[Any] = None,
    ) -> ModelResponse:

        messages = []

        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "think": self.think,
            "options": {
                "temperature": 0,
                "num_predict": self.num_predict,
            },
        }

        if response_format is not None:
            payload["format"] = response_format

        data = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            f"{self.host}/api/chat",
            data=data,
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=300,
            ) as response:

                body = json.loads(
                    response.read().decode("utf-8")
                )

        except urllib.error.URLError as exc:
            raise RuntimeError(
                "Could not connect to Ollama. "
                "Make sure Ollama is running."
            ) from exc

        message = body["message"]

        return ModelResponse(
            text=message.get("content", ""),
            thinking=message.get("thinking"),
            prompt_tokens=body.get("prompt_eval_count"),
            completion_tokens=body.get("eval_count"),
            done_reason=body.get("done_reason"),
        )
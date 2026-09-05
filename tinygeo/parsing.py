import re
from typing import Optional


def extract_final_answer(text: str) -> Optional[str]:
    """
    Extract the final answer from:

        FINAL: answer

    We use the last occurrence in case a model
    accidentally produces the marker more than once.
    """

    matches = re.findall(
        r"FINAL:\s*(.+)",
        text,
        flags=re.IGNORECASE,
    )

    if not matches:
        return None

    answer = matches[-1].strip()

    # Only use the first line after FINAL.
    answer = answer.splitlines()[0].strip()

    return answer

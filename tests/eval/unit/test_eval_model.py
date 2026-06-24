from __future__ import annotations

from unittest.mock import MagicMock, patch

from pydantic import BaseModel

from eval.domain.judge.model_factory import CompatibleGPTModel


class _ScoreReason(BaseModel):
    score: int
    reason: str


def test_compatible_gpt_model_uses_string_content_and_json_mode() -> None:
    model = CompatibleGPTModel(
        model="glm-4-flash",
        api_key="test-key",
        base_url="https://example.com/v1",
    )
    client = MagicMock()
    completion = MagicMock()
    completion.choices = [MagicMock(message=MagicMock(content='{"score": 8, "reason": "ok"}'))]
    completion.usage.prompt_tokens = 10
    completion.usage.completion_tokens = 5
    client.chat.completions.create.return_value = completion

    with patch.object(model, "load_model", return_value=client):
        result, _cost = model.generate("judge prompt", schema=_ScoreReason)

    assert isinstance(result, _ScoreReason)
    assert result.score == 8
    assert result.reason == "ok"

    call_kwargs = client.chat.completions.create.call_args.kwargs
    assert call_kwargs["messages"] == [{"role": "user", "content": "judge prompt"}]
    assert call_kwargs["response_format"] == {"type": "json_object"}

from __future__ import annotations

from typing import Optional, Tuple, Union

from deepeval.models import GPTModel
from deepeval.models.llms.openai_model import retry_openai
from deepeval.models.llms.utils import trim_and_load_json
from pydantic import BaseModel

from agent.configs.settings import Config


class CompatibleGPTModel(GPTModel):
    """OpenAI-compatible eval model that sends plain string message content.

    DeepEval's ``GPTModel`` wraps prompts as ``[{"type": "text", "text": prompt}]``.
    Several compatible providers (e.g. Zhipu GLM) mishandle that format and return
    non-JSON replies, which breaks ``ConversationalGEval`` parsing.
    """

    @retry_openai
    def generate(
        self, prompt: str, schema: Optional[BaseModel] = None
    ) -> Tuple[Union[str, BaseModel], float]:
        """Generate a response using string ``content`` for provider compatibility."""

        client = self.load_model(async_mode=False)
        messages = [{"role": "user", "content": prompt}]
        request_kwargs: dict[str, object] = {
            "model": self.name,
            "messages": messages,
            "temperature": self.temperature,
            **self.generation_kwargs,
        }
        if schema is not None:
            request_kwargs["response_format"] = {"type": "json_object"}

        completion = client.chat.completions.create(**request_kwargs)
        output = completion.choices[0].message.content
        cost = self.calculate_cost(
            completion.usage.prompt_tokens,
            completion.usage.completion_tokens,
        )
        self._update_llm_span_from_completion(completion, messages)
        if schema is not None:
            json_output = trim_and_load_json(output)
            return schema.model_validate(json_output), cost
        return output, cost

    @retry_openai
    async def a_generate(
        self, prompt: str, schema: Optional[BaseModel] = None
    ) -> Tuple[Union[str, BaseModel], float]:
        """Async variant of :meth:`generate`."""

        client = self.load_model(async_mode=True)
        messages = [{"role": "user", "content": prompt}]
        request_kwargs: dict[str, object] = {
            "model": self.name,
            "messages": messages,
            "temperature": self.temperature,
            **self.generation_kwargs,
        }
        if schema is not None:
            request_kwargs["response_format"] = {"type": "json_object"}

        completion = await client.chat.completions.create(**request_kwargs)
        output = completion.choices[0].message.content
        cost = self.calculate_cost(
            completion.usage.prompt_tokens,
            completion.usage.completion_tokens,
        )
        self._update_llm_span_from_completion(completion, messages)
        if schema is not None:
            json_output = trim_and_load_json(output)
            return schema.model_validate(json_output), cost
        return output, cost


def build_eval_model(config: Config) -> CompatibleGPTModel:
    """Build the DeepEval judge model from resolved runtime config."""

    api_key = config.eval_llm_api_key
    base_url = config.eval_llm_base_url
    model_name = config.eval_llm_model
    if not api_key or not base_url or not model_name:
        raise ValueError(
            "eval LLM 配置不完整：请在 .env 配置 EVAL_LLM_API_KEY，"
            "在 .config.yaml 配置 eval_llm_base_url / eval_llm_model"
        )
    return CompatibleGPTModel(model=model_name, api_key=api_key, base_url=base_url)

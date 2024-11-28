#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : self-host open llm model with ollama which isn't openai-api-compatible

import json

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.const import USE_CONFIG_TIMEOUT
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.general_api_requestor import GeneralAPIRequestor
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.utils.cost_manager import TokenCostManager
from metagpt.logs import log_llm_stream


@register_provider(LLMType.P1_LLM)
class P1LLM(BaseLLM):

    def __init__(self, config: LLMConfig):
        self.__init_ollama(config)
        self.client = GeneralAPIRequestor(base_url=config.base_url)
        self.config = config
        self.suffix_url = f"/nexchat/api/{config.serviceName}/api/{config.model}"
        self.http_method = "post"
        self.use_system_prompt = False
        self.cost_manager = TokenCostManager()
        self.headers = {"Authorization":config.authorization}

    def __init_ollama(self, config: LLMConfig):
        assert config.base_url, "p1_llm base url is required!"
        self.model = config.model
        self.pricing_plan = self.model

    def _const_kwargs(self, messages: list[dict], stream: bool = False) -> dict:
        kwargs = {"model": self.model, "messages": messages, "options": {"temperature": 0.3}, "stream": stream}
        return kwargs

    def get_choice_text(self, resp: dict) -> str:
        """get the resp content from llm response"""
        assist_msg = resp.get("message", {})
        assert assist_msg.get("role", None) == "assistant"
        return assist_msg.get("content")

    def get_usage(self, resp: dict) -> dict:
        return {"prompt_tokens": resp.get("prompt_eval_count", 0), "completion_tokens": resp.get("eval_count", 0)}

    def _decode_and_load(self, chunk: bytes, encoding: str = "utf-8") -> dict:
        chunk = chunk.decode(encoding)
        return json.loads(chunk)

    async def _achat_completion(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> dict:
        resp, _, _ = await self.client.arequest(
            method=self.http_method,
            url=self.suffix_url,
            headers=self.headers,
            params=self._const_kwargs(messages),
            request_timeout=self.get_timeout(timeout),
        )
        resp = self._decode_and_load(resp)

        if resp['status'] != 200:
            raise RuntimeError(f"call P1 LLM failed, error:{resp['error']}, msg:{resp['message']}")

        resp_data = json.loads(resp['data'])
        content = resp_data['output']['answer']
        log_llm_stream(content+"/n")

        prompt_eval_count = resp_data['tokens']['input_tokens']
        eval_count = resp_data['tokens']['output_tokens']

        transfer_resp = {
            'model':'p1 llm',
            # 'created_at':datetime.now(),
            'message':{
                'role':'assistant',
                'content':content,
            },
            'done_reason': 'stop',
            'done': True,
            'prompt_eval_count': prompt_eval_count,
            'eval_count': eval_count,
        }

        usage = self.get_usage(transfer_resp)
        self._update_costs(usage)
        return transfer_resp

    async def acompletion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT) -> dict:
        return await self._achat_completion(messages, timeout=self.get_timeout(timeout))

    '''FYI ollama'''
    async def _achat_completion_stream(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> str:

        # logger.warning("P1 LLM not support stream http,In fact not use stream http")

        resp, _, _ = await self.client.arequest(
            method=self.http_method,
            url=self.suffix_url,
            headers=self.headers,
            params=self._const_kwargs(messages),
            request_timeout=self.get_timeout(timeout),
        )
        resp = self._decode_and_load(resp)

        if resp['status'] != 200:
            raise RuntimeError(f"call P1 LLM failed, error:{resp['error']}, msg:{resp['message']}")

        resp_data = json.loads(resp['data'])
        log_llm_stream(resp_data['output']['answer']+"/n")
        return resp_data['output']['answer']



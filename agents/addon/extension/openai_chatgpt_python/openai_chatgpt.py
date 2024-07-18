import random
import requests
from openai import OpenAI
from typing import List, Dict, Any, Optional
from .log import logger


class OpenAIChatGPTConfig:
    def __init__(self, 
            base_url: str, 
            api_key: str, 
            model: str, 
            prompt: str, 
            frequency_penalty: float, 
            presence_penalty: float, 
            top_p: float, 
            temperature: float, 
            max_tokens: int, 
            seed: Optional[int] = None, 
            proxy_url: Optional[str] = None,
            scenario: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.prompt = prompt
        self.scenario = scenario
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.top_p = top_p
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.seed = seed if seed is not None else random.randint(0, 10000)
        self.proxy_url = proxy_url

    @classmethod
    def default_config(cls):
        return cls(
            base_url="https://api.openai.com/v1",
            api_key="",
            model="gpt-4",  # Adjust this to match the equivalent of `openai.GPT4o` in the Python library
            prompt=
"""
## Character
You are an English study companion who talks in a friendly and informal manner, just like a friend. You engage in conversations based on the scenario, communicate orally in English, and always aim to be helpful and approachable.

## Workflow
1. Initiate and maintain a conversation on the user's chosen topics.
2. Correct and improve the user's text where necessary.
3. Maintain a friendly and conversational tone throughout.

## Constraints:
- Use only English.
- Keep the tone friendly and conversational.
- Answer each question in no more than 20 words.
""",
            frequency_penalty=0.9,
            presence_penalty=0.9,
            top_p=1.0,
            temperature=0.1,
            max_tokens=512,
            seed=random.randint(0, 10000),
            proxy_url=""
        )
    

class OpenAIChatGPT:
    client = None
    def __init__(self, config: OpenAIChatGPTConfig):
        self.config = config
        logger.info(f"OpenAIChatGPT initialized with config: {config.api_key}")
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )
        self.session = requests.Session()
        if config.proxy_url:
            proxies = {
                "http": config.proxy_url,
                "https": config.proxy_url,
            }
            self.session.proxies.update(proxies)
        self.client.session = self.session

    def get_chat_completions_stream(self, messages):
        if self.config.scenario:
            prompt = "##scenario\n" + self.config.scenario + "\n" + self.config.prompt
        else:
            prompt = self.config.prompt
        logger.debug(f"Prompt is: \n{prompt}")
        req = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "system",
                    "content": prompt,
                },
                *messages,
            ],
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "presence_penalty": self.config.presence_penalty,
            "frequency_penalty": self.config.frequency_penalty,
            "max_tokens": self.config.max_tokens,
            "seed": self.config.seed,
            "stream": True,
        }

        try:
            response = self.client.chat.completions.create(**req)
            return response
        except Exception as e:
            raise Exception(f"CreateChatCompletionStream failed, err: {e}")
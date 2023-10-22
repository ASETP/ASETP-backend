from typing import Optional, List, Dict

import openai
from retry import retry


class OpenAIChat:
    def __init__(self, model: str = "gpt-3.5-turbo"):
        self._model = model

    @retry(tries=3, delay=1)
    def query(
        self,
        prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.0,
    ) -> str:
        if messages is None:
            assert prompt is not None, "Messages or prompt must be provided."
            messages = [{"role": "user", "content": prompt}]
        try:
            response = openai.ChatCompletion.create(
                model=self._model,
                temperature=temperature,
                messages=messages,
            )
            return response.choices[0].message.content
        # catch context length / do not retry
        except openai.error.InvalidRequestError as e:
            return str(f"Error: {e}")
        # catch authorization errors / do not retry
        except openai.error.AuthenticationError as e:
            return "Error: The provided OpenAI API key is invalid"
        except Exception as e:
            print(f"Retrying LLM call {e}")
            raise e

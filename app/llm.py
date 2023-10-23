import logging
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
        logging.info(f"Waiting for response from {self._model}")
        try:
            response = openai.ChatCompletion.create(
                model=self._model,
                temperature=temperature,
                messages=messages,
            )
            logging.info(f"Succeed to receive response from {self._model}")
            return response.choices[0].message.content
        # catch context length / do not retry
        except openai.error.InvalidRequestError as e:
            logging.error(f"Error: {e}")
            return str(f"Error: {e}")
        # catch authorization errors / do not retry
        except openai.error.AuthenticationError:
            logging.error("Invalid OPENAI_API_KEY!")
            return "Error: The provided OpenAI API key is invalid"
        except Exception as e:
            logging.error(f"Retrying LLM call {e}")
            raise e

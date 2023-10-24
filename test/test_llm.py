import unittest

from openai.embeddings_utils import get_embedding

from app.llm import OpenAIChat


class TestLLM(unittest.TestCase):
    def test_chat_api(self):
        llm = OpenAIChat()
        try:
            response = llm.query(prompt="Hello!")
        except:
            response = "Error: "

        self.assertFalse(response.startswith("Error: "))

    def test_embedding_api(self):
        try:
            embedding = get_embedding(
                text="test embedding", engine="text-embedding-ada-002"
            )
        except:
            embedding = None

        self.assertIsInstance(embedding, list)
        self.assertIsInstance(embedding[0], float)

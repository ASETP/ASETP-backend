import os

from fastapi import FastAPI

from core import answer

app = FastAPI()

os.environ["OPENAI_API_BASE"] = "https://api.openai-proxy.com/v1"


@app.get("/")
async def test_connection():
    return {"message": "Hello World"}


@app.get("/query/{query}")
async def ask_kg(query: str):
    ans = answer(query=query)
    return {"answer": ans}

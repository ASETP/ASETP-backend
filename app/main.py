import logging

from fastapi import FastAPI

from app.core import answer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

app = FastAPI()


@app.get("/")
async def test_connection():
    return {"message": "Hello World"}


@app.get("/query/{query}")
async def ask_kg(query: str):
    ans = answer(query=query)
    return {"answer": ans}

import logging
from typing import Any, Dict, List, Optional

from openai.embeddings_utils import get_embedding, cosine_similarity

from app.graph import Neo4jGraph
from app.llm import OpenAIChat


def search_titles(
    query: str,
    graph: Neo4jGraph,
    top: int = 2,
    sim_thresholds: float = 0.9,
    limit: Optional[int] = None,
) -> List[str]:
    def get_titles(
        graph_db: Neo4jGraph, max_limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:  # {"text": "", "embedding": []}
        result = []
        cypher_query = "MATCH (n:Question) RETURN n"
        if max_limit is not None:
            cypher_query += f" LIMIT {max_limit}"
        questions = graph_db.query(query=cypher_query)
        for q in questions:
            result.append({"text": q["n"]["title"], "embedding": q["n"]["embedding"]})
        return result

    def sort_titles(title_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        def custom_key(e: Dict[str, Any]):
            return e.get("similarity") or 0.0

        return sorted(title_list, key=custom_key, reverse=True)

    embedding = get_embedding(text=query, engine="text-embedding-ada-002")
    logging.info(f"Generate embedding for query: {query}")

    titles = get_titles(graph_db=graph, max_limit=limit)
    logging.info("Get question entities from graph database.")

    for title in titles:
        title["similarity"] = cosine_similarity(title["embedding"], embedding)

    logging.info("Finish calculating similarity for all question titles.")
    logging.info(f"Select at most {top} similar question(s) as reference.")

    if len(titles) > top:
        sorted_titles = sort_titles(title_list=titles)
        return [
            t["text"] for t in sorted_titles[:top] if t["similarity"] > sim_thresholds
        ]

    return [t["text"] for t in titles if t["similarity"] > sim_thresholds]


def get_knowledge_from_titles(
    graph: Neo4jGraph, titles: List[str]
) -> List[Dict[str, Any]]:  # {"title": "", "tags": "", "answer": ["", "", ...]}
    result = {}
    cypher_query = (
        "MATCH p=(q:Question)-[r:SolvedBy]->(a:Answer)"
        " WHERE q.title IN $titles "
        "RETURN p"
    )

    paths = graph.query(query=cypher_query, param_map={"titles": titles})
    logging.info("Get all answers of reference question(s).")

    for path in paths:
        q, r, a = path["p"][:3]
        if result.get(q["title"]) is None:
            result[q["title"]] = {
                "title": q["title"],
                "tags": q["tags"],
                "view_count": q["view_count"],
                "date": q["date"],
                "answer": [a["content"]],
            }
        else:
            result[q["title"]]["answer"].append(a["content"])

    return list(result.values())


def synthesize_answer(
    query: str, knowledge: List[Dict[str, Any]],
    need_ans: bool = True, model_name: str = "gpt-3.5-turbo",
) -> str:
    def construct_prompt(query_str: str, knowledge_list: List[Dict[str, Any]]) -> str:
        context_str = ""
        for line in knowledge_list:
            title_str = f"Title: {line['title']}\n"
            tags_str = f"Tags: {line['tags']}\n"
            view_str = f"View count: {line['view_count']}\n"
            date_str = f"Date: {line['date']}"
            answer_str = "\n".join(
                f"Answer{i+1}: {ans}" for i, ans in enumerate(line["answer"])
            )
            if need_ans:
                context_str += title_str + tags_str + answer_str + "\n"
            else:
                context_str += title_str + tags_str + view_str + date_str + "\n"

        return (
            "Context information is below.\n"
            "---------------------\n"
            "{context_str}\n"
            "---------------------\n"
            "Given the context information and not prior knowledge, answer the query.\n"
            "Query: {query_str}\n"
            "Answer: "
        ).format(query_str=query_str, context_str=context_str)

    llm = OpenAIChat(model=model_name)
    logging.info("Construct prompt with context from graph database.")
    prompt = construct_prompt(query_str=query, knowledge_list=knowledge)
    response = llm.query(prompt=prompt)
    return response.replace("\n\n", "\n")


def answer(query: str, **kwargs) -> str:
    logging.info(f"Receive query: {query}")
    graph = Neo4jGraph(**kwargs)
    is_trend = is_trend_query(query=query)
    top, sim_threshold = (50, 0.3) if is_trend else (2, 0.9)
    titles = search_titles(query=query, graph=graph, top=top, sim_thresholds=sim_threshold)
    if len(titles) == 0:
        return "Fail to get related information in knowledge graph."
    logging.info(f"Get {len(titles)} related question(s) from knowledge graph.")
    knowledge = get_knowledge_from_titles(graph=graph, titles=titles)
    ans = synthesize_answer(query=query, knowledge=knowledge, need_ans=not is_trend)
    ans4log = ans.replace("\n", " ")
    logging.info(f"Get answer: {ans4log}")
    return ans


def is_trend_query(query: str) -> bool:
    llm = OpenAIChat()
    response = llm.query(
        prompt=(
            f"Here is a query from user: {query}.\n"
            "If it queries about technology trend, answer YES. "
            "Otherwise, answer NO.\n"
            "Don't give any extra answer."
        )
    )
    return "YES" in response

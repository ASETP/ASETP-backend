import unittest

from app.core import search_titles, get_knowledge_from_titles
from app.graph import Neo4jGraph


class TestCore(unittest.TestCase):
    def test_search_titles_1(self):
        graph = Neo4jGraph()
        titles = search_titles(
            query="How do I add Google Application Credentials or Secret to Vercel Deployment",
            graph=graph,
        )
        self.assertEqual(len(titles), 1)
        self.assertEqual(
            titles[0],
            "How do I add Google Application Credentials/Secret to Vercel Deployment?",
        )
        graph.client.close()

    def test_search_titles_2(self):
        graph = Neo4jGraph()
        titles = search_titles(
            query="Tell me about java.",
            graph=graph,
            sim_thresholds=0.5,
        )
        self.assertEqual(len(titles), 3)
        result = set(titles).intersection(
            {
                "How is gdb used to debug Java programs?",
                "Why should the interface for a Java class be preferred?",
                "What are the fundamental differences between garbage collection in C# and Java?",
            }
        )
        self.assertEqual(len(result), 3)
        graph.client.close()

    def test_search_titles_3(self):
        graph = Neo4jGraph()
        titles = search_titles(
            query="111",
            graph=graph,
        )
        self.assertEqual(len(titles), 0)
        graph.client.close()

    def test_get_knowledge_from_titles_1(self):
        graph = Neo4jGraph()
        result = get_knowledge_from_titles(
            graph=graph,
            titles=[
                "How do I add Google Application Credentials/Secret to Vercel Deployment?"
            ],
        )
        self.assertEqual(len(result), 1)
        result = result[0]
        self.assertEqual(
            result["title"],
            "How do I add Google Application Credentials/Secret to Vercel Deployment?",
        )
        self.assertEqual(result["tags"], "vercel")
        self.assertEqual(len(result["answer"]), 3)
        graph.client.close()

    def test_get_knowledge_from_titles_2(self):
        graph = Neo4jGraph()
        titles = [
            "How is gdb used to debug Java programs?",
            "Why should the interface for a Java class be preferred?",
            "What are the fundamental differences between garbage collection in C# and Java?",
        ]
        result = get_knowledge_from_titles(graph=graph, titles=titles)
        self.assertEqual(len(result), 3)
        res1, res2, res3 = result[:3]
        self.assertTrue(res1["title"] in titles)
        self.assertTrue(res2["title"] in titles)
        self.assertTrue(res3["title"] in titles)
        tags = [
            "java;collections;interface",
            "c#;java;garbage-collection",
            "java;debugging;gdb",
        ]
        self.assertTrue(res1["tags"] in tags)
        self.assertTrue(res2["tags"] in tags)
        self.assertTrue(res3["tags"] in tags)
        self.assertEqual(len(res1["answer"]), 3)
        self.assertEqual(len(res2["answer"]), 3)
        self.assertEqual(len(res3["answer"]), 3)
        graph.client.close()

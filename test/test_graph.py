import unittest

from app.graph import Neo4jGraph


class TestGraph(unittest.TestCase):
    def test_graph_connection(self):
        try:
            graph = Neo4jGraph()
        except ValueError or ImportError:
            graph = None

        self.assertIsNotNone(graph)
        graph.client.close()

    def test_graph_query(self):
        try:
            g = Neo4jGraph()
        except ValueError or ImportError:
            g = None
        self.assertIsNotNone(g)

        data = g.query("MATCH (n:Question) RETURN COUNT(n)")
        q_cnt = data[0].get("COUNT(n)")
        self.assertEqual(q_cnt, 3228)

        data = g.query("MATCH (n) WHERE n.embedding IS NOT NULL RETURN COUNT(n)")
        q_cnt = data[0].get("COUNT(n)")
        self.assertEqual(q_cnt, 3228)

        data = g.query("MATCH p=(q:Question)-[r:SolvedBy]->(a:Answer) RETURN COUNT(p)")
        p_cnt = data[0].get("COUNT(p)")
        self.assertEqual(p_cnt, 9684)

        g.client.close()

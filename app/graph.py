import logging
from typing import Any, Dict, Optional

from func_timeout import func_set_timeout
from openai.embeddings_utils import get_embedding


node_properties_query = (
    "CALL apoc.meta.data() "
    "YIELD label, other, elementType, type, property "
    'WHERE NOT type = "RELATIONSHIP" AND elementType = "node" '
    "WITH label AS nodeLabels, collect({property:property, type:type}) AS properties "
    "RETURN {labels: nodeLabels, properties: properties} AS output"
)

rel_properties_query = (
    "CALL apoc.meta.data() "
    "YIELD label, other, elementType, type, property "
    'WHERE NOT type = "RELATIONSHIP" AND elementType = "relationship" '
    "WITH label AS nodeLabels, collect({property:property, type:type}) AS properties "
    "RETURN {type: nodeLabels, properties: properties} AS output "
)

rel_query = (
    "CALL apoc.meta.data() "
    "YIELD label, other, elementType, type, property "
    'WHERE type = "RELATIONSHIP" AND elementType = "node" '
    "UNWIND other AS other_node "
    'RETURN "(:" + label + ")-[:" + property + "]->(:" + toString(other_node) + ")" AS output'
)


class Neo4jGraph:
    def __init__(
        self,
        username: str = "neo4j",
        password: str = "cV1HM2kz3eG3t4F8WgACtyduISFFzybwVz_nAkc0LlU",
        url: str = "neo4j+s://7faed8a0.databases.neo4j.io",
        database: str = "neo4j",
        **kwargs: Any,
    ) -> None:
        try:
            import neo4j
        except ImportError as e:
            raise ImportError("Please install neo4j: pip install neo4j") from e
        logging.info(f"Connecting to Neo4j graph database: {url}")
        self._driver = neo4j.GraphDatabase.driver(url, auth=(username, password))
        self._database = database
        self._property_label = None
        self.schema = ""
        # Verify connection
        try:
            self._driver.verify_connectivity()
        except neo4j.exceptions.ServiceUnavailable:
            raise ValueError(
                "Could not connect to Neo4j database. "
                "Please ensure that the url is correct"
            )
        except neo4j.exceptions.AuthError:
            raise ValueError(
                "Could not connect to Neo4j database. "
                "Please ensure that the username and password are correct"
            )
        # Set schema
        try:
            self.refresh_schema()
        except neo4j.exceptions.ClientError:
            raise ValueError(
                "Could not use APOC procedures. "
                "Please ensure the APOC plugin is installed in Neo4j and that "
                "'apoc.meta.data()' is allowed in Neo4j configuration "
            )
        logging.info(f"Succeed to connect to Neo4j: {url}")

    @property
    def client(self) -> Any:
        return self._driver

    def refresh_schema(self) -> None:
        """
        Refreshes the Neo4j graph schema information.
        """
        logging.info("Refreshing graph database schema.")

        node_properties = self.query(node_properties_query, verbose=False)
        relationships_properties = self.query(rel_properties_query, verbose=False)
        relationships = self.query(rel_query, verbose=False)

        self.schema = f"""
        Node properties are the following:
        {[el['output'] for el in node_properties]}
        Relationship properties are the following:
        {[el['output'] for el in relationships_properties]}
        The relationships are the following:
        {[el['output'] for el in relationships]}
        """

    def get_schema(self, refresh: bool = False) -> str:
        """Get the schema of the Neo4jGraph store."""
        if self.schema and not refresh:
            return self.schema
        self.refresh_schema()
        return self.schema

    @func_set_timeout(5)
    def query(
        self,
        query: str,
        param_map: Optional[Dict[str, Any]] = None,
        verbose: bool = True,
    ) -> Any:
        if param_map is None:
            param_map = {}
        if verbose:
            logging.info(f"Querying Neo4j graph database: {query} % {param_map}")
        with self._driver.session(database=self._database) as session:
            result = session.run(query, param_map)
            return [d.data() for d in result]

    def inject_data(self, data_file: str):
        with open(data_file, encoding="utf-8", mode="r") as f:
            lines = f.readlines()
        f.close()
        for i, query in enumerate(lines):
            self.query(query=query)
            if i % 50 == 0 and i > 0:
                print(f"Query executed: {i}.")

    def create_embeddings(self, data_file: str):
        with open(data_file, encoding="utf-8", mode="r") as f:
            lines = f.readlines()
        f.close()
        for i, title in enumerate(lines):
            embedding = get_embedding(text=title, model="text-embedding-ada-002")
            print(f"Embedding created: title-{i}")
            query = (
                f"MATCH (n:Question) WHERE n.title=$title SET n.embedding=$embedding"
            )
            self.query(query=query, param_map={"title": title, "embedding": embedding})
            print(f"Embedding injected: title-{i}")

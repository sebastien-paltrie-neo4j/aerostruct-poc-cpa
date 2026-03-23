import os
from contextlib import contextmanager

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()


class Neo4jClient:
    _driver = None

    @classmethod
    def get_driver(cls):
        if cls._driver is None:
            cls._driver = GraphDatabase.driver(
                os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "")),
            )
        return cls._driver

    @classmethod
    def close(cls):
        if cls._driver:
            cls._driver.close()
            cls._driver = None

    @classmethod
    @contextmanager
    def session(cls):
        session = cls.get_driver().session()
        try:
            yield session
        finally:
            session.close()

    @classmethod
    def run(cls, query: str, params: dict = None) -> list[dict]:
        with cls.session() as session:
            return [r.data() for r in session.run(query, params or {})]

from neo4j import GraphDatabase

class Neo4jDatabase:
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="p02022020@"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def add_paper(self, title, year):
       
        with self.driver.session(database="researchpapers") as session:
            session.write_transaction(self._create_and_return_paper, title, year)

    @staticmethod
    def _create_and_return_paper(tx, title, year):
        query = (
            "CREATE (p:Paper {title: $title, year: $year}) "
            "RETURN p"
        )
        result = tx.run(query, title=title, year=year)
        return result.single()

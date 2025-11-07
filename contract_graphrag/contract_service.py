"""
Contract Search Service for Neo4j GraphRAG queries.

Provides data retrieval functions for contract analysis including:
- Cypher-based queries for specific contracts and organizations
- Vector search for semantic similarity
- Text-to-Cypher for natural language queries
"""

from typing import Any

from neo4j import GraphDatabase
from neo4j_graphrag.embeddings import AzureOpenAIEmbeddings
from neo4j_graphrag.llm import AzureOpenAILLM
from neo4j_graphrag.retrievers import Text2CypherRetriever, VectorCypherRetriever
from neo4j_graphrag.types import RetrieverResultItem

from .settings import settings


def format_vector_search_result(record: Any) -> RetrieverResultItem:
    """Format vector search results from Neo4j records."""
    metadata = {
        "contract_id": record.get("contract_id"),
        "nodeLabels": ["Excerpt", "Agreement", "ContractClause"],
    }

    result_dict = {
        "agreement_name": record.get("agreement_name"),
        "contract_id": record.get("contract_id"),
        "clause_type": record.get("clause_type"),
        "excerpt": record.get("excerpt"),
    }

    return RetrieverResultItem(content=result_dict, metadata=metadata)


class ContractSearchService:
    """Service for searching and retrieving contract information from Neo4j.

    Use as a context manager to ensure proper resource cleanup:
        with ContractSearchService() as service:
            result = service.get_contract(1)
    """

    def __init__(self):
        """Initialize the contract search service with Neo4j connection."""
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider

        self.driver = GraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_username, settings.neo4j_password)
        )

        # Get Azure AD token for authentication
        credential = DefaultAzureCredential()
        token_provider = get_bearer_token_provider(credential, settings.azure_openai_scope)

        # Initialize Azure OpenAI embedder using AzureOpenAIEmbeddings class
        self.embedder = AzureOpenAIEmbeddings(
            model=settings.azure_openai_embedding_model,
            azure_endpoint=settings.azure_openai_endpoint,
            azure_ad_token_provider=token_provider,
            api_version="2024-10-21",
        )

        # Initialize Azure OpenAI LLM using AzureOpenAILLM class
        self.llm = AzureOpenAILLM(
            model_name=settings.azure_openai_responses_deployment_name,
            model_params={"temperature": 0},
            azure_endpoint=settings.azure_openai_endpoint,
            azure_ad_token_provider=token_provider,
            api_version="2024-10-21",
        )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures driver is closed."""
        self.close()
        return False

    def get_contract(self, contract_id: int) -> dict:
        """
        Get detailed information about a specific contract.

        Args:
            contract_id: The ID of the contract to retrieve

        Returns:
            Dictionary with full contract details including parties and clauses
        """
        if contract_id <= 0:
            return {"error": "Contract ID must be positive"}

        query = """
            MATCH (a:Agreement {contract_id: $contract_id})-[:HAS_CLAUSE]->(clause:ContractClause)
            WITH a, collect(clause) as clauses
            MATCH (country:Country)-[i:INCORPORATED_IN]-(p:Organization)-[r:IS_PARTY_TO]-(a)
            WITH a, clauses, collect(p) as parties, collect(country) as countries,
                 collect(r) as roles, collect(i) as states
            RETURN a as agreement, clauses, parties, countries, roles, states
        """

        records, _, _ = self.driver.execute_query(query, {"contract_id": contract_id})

        if not records:
            return {"error": f"Contract {contract_id} not found"}

        record = records[0]
        agreement_node = record["agreement"]

        # Build parties list
        parties = []
        for i, party in enumerate(record["parties"]):
            parties.append(
                {
                    "name": party.get("name"),
                    "role": record["roles"][i].get("role"),
                    "incorporation_country": record["countries"][i].get("name"),
                    "incorporation_state": record["states"][i].get("state"),
                }
            )

        # Build clauses list
        clauses = []
        for clause in record["clauses"]:
            clauses.append({"clause_type": clause.get("type")})

        return {
            "contract_id": agreement_node.get("contract_id"),
            "name": agreement_node.get("name"),
            "agreement_type": agreement_node.get("agreement_type"),
            "effective_date": agreement_node.get("effective_date"),
            "expiration_date": agreement_node.get("expiration_date"),
            "renewal_term": agreement_node.get("renewal_term"),
            "parties": parties,
            "clauses": clauses,
        }

    def get_contracts_by_organization(self, organization_name: str) -> list[dict]:
        """
        Get all contracts involving a specific organization.

        Args:
            organization_name: Name of the organization to search for

        Returns:
            List of contracts with basic details
        """
        if not organization_name or not organization_name.strip():
            return []

        query = """
            CALL db.index.fulltext.queryNodes('organization_name_index', $organization_name)
            YIELD node AS o, score
            WITH o, score
            ORDER BY score DESC
            LIMIT 1
            WITH o
            MATCH (o)-[:IS_PARTY_TO]->(a:Agreement)
            WITH a
            MATCH (country:Country)-[i:INCORPORATED_IN]-(p:Organization)-[r:IS_PARTY_TO]-(a)
            RETURN a as agreement, collect(p) as parties, collect(r) as roles,
                   collect(country) as countries, collect(i) as states
        """

        records, _, _ = self.driver.execute_query(query, {"organization_name": organization_name})

        results = []
        for record in records:
            agreement_node = record["agreement"]

            parties = []
            for i, party in enumerate(record["parties"]):
                parties.append(
                    {
                        "name": party.get("name"),
                        "role": record["roles"][i].get("role"),
                        "incorporation_country": record["countries"][i].get("name"),
                        "incorporation_state": record["states"][i].get("state"),
                    }
                )

            results.append(
                {
                    "contract_id": agreement_node.get("contract_id"),
                    "name": agreement_node.get("name"),
                    "agreement_type": agreement_node.get("agreement_type"),
                    "parties": parties,
                }
            )

        return results

    def get_contracts_with_clause_type(self, clause_type: str) -> list[dict]:
        """
        Get contracts that contain a specific clause type.

        Args:
            clause_type: The type of clause to search for

        Returns:
            List of contracts containing the specified clause type
        """
        query = """
            MATCH (a:Agreement)-[:HAS_CLAUSE]->(cc:ContractClause {type: $clause_type})
            WITH a
            MATCH (country:Country)-[i:INCORPORATED_IN]-(p:Organization)-[r:IS_PARTY_TO]-(a)
            RETURN a as agreement, collect(p) as parties, collect(r) as roles,
                   collect(country) as countries, collect(i) as states
        """

        records, _, _ = self.driver.execute_query(query, {"clause_type": clause_type})

        results = []
        for record in records:
            agreement_node = record["agreement"]

            parties = []
            for i, party in enumerate(record["parties"]):
                parties.append(
                    {
                        "name": party.get("name"),
                        "role": record["roles"][i].get("role"),
                        "incorporation_country": record["countries"][i].get("name"),
                        "incorporation_state": record["states"][i].get("state"),
                    }
                )

            results.append(
                {
                    "contract_id": agreement_node.get("contract_id"),
                    "name": agreement_node.get("name"),
                    "agreement_type": agreement_node.get("agreement_type"),
                    "parties": parties,
                }
            )

        return results

    def get_contracts_without_clause(self, clause_type: str) -> list[dict]:
        """
        Get contracts that do NOT contain a specific clause type.

        Args:
            clause_type: The type of clause to exclude

        Returns:
            List of contracts without the specified clause type
        """
        query = """
            MATCH (a:Agreement)
            OPTIONAL MATCH (a)-[:HAS_CLAUSE]->(cc:ContractClause {type: $clause_type})
            WITH a, cc
            WHERE cc IS NULL
            WITH a
            MATCH (country:Country)-[i:INCORPORATED_IN]-(p:Organization)-[r:IS_PARTY_TO]-(a)
            RETURN a as agreement, collect(p) as parties, collect(r) as roles,
                   collect(country) as countries, collect(i) as states
        """

        records, _, _ = self.driver.execute_query(query, {"clause_type": clause_type})

        results = []
        for record in records:
            agreement_node = record["agreement"]

            parties = []
            for i, party in enumerate(record["parties"]):
                parties.append(
                    {
                        "name": party.get("name"),
                        "role": record["roles"][i].get("role"),
                        "incorporation_country": record["countries"][i].get("name"),
                        "incorporation_state": record["states"][i].get("state"),
                    }
                )

            results.append(
                {
                    "contract_id": agreement_node.get("contract_id"),
                    "name": agreement_node.get("name"),
                    "agreement_type": agreement_node.get("agreement_type"),
                    "parties": parties,
                }
            )

        return results

    def get_contracts_similar_text(self, clause_text: str) -> list[dict]:
        """
        Find contracts with clauses semantically similar to the given text.

        Uses vector search on excerpt embeddings to find relevant contracts.

        Args:
            clause_text: Text to search for semantic similarity

        Returns:
            List of contracts with similar clause text and excerpts
        """
        # Cypher query to traverse from excerpts back to agreements
        traversal_query = """
            MATCH (a:Agreement)-[:HAS_CLAUSE]->(cc:ContractClause)-[:HAS_EXCERPT]-(node)
            RETURN a.name as agreement_name, a.contract_id as contract_id,
                   cc.type as clause_type, node.text as excerpt
        """

        # Set up vector retriever
        retriever = VectorCypherRetriever(
            driver=self.driver,
            index_name="excerpt_vector_index",
            embedder=self.embedder,
            retrieval_query=traversal_query,
            result_formatter=format_vector_search_result,
        )

        # Run vector search
        retriever_result = retriever.search(query_text=clause_text, top_k=3)

        # Format results
        results = []
        for item in retriever_result.items:
            content = item.content
            results.append(
                {
                    "contract_id": content["contract_id"],
                    "agreement_name": content["agreement_name"],
                    "clause_type": content["clause_type"],
                    "excerpt": content["excerpt"],
                }
            )

        return results

    def answer_aggregation_question(self, user_question: str) -> str:
        """
        Answer questions using text-to-Cypher conversion.

        Converts natural language questions to Cypher queries and executes them.

        Args:
            user_question: Natural language question about contracts

        Returns:
            Answer based on query results
        """
        neo4j_schema = """
            Node properties:
            Agreement {agreement_type: STRING, contract_id: INTEGER, effective_date: STRING,
                      renewal_term: STRING, name: STRING}
            ContractClause {type: STRING}
            ClauseType {name: STRING}
            Country {name: STRING}
            Excerpt {text: STRING}
            Organization {name: STRING}

            Relationship properties:
            IS_PARTY_TO {role: STRING}
            GOVERNED_BY_LAW {state: STRING}
            HAS_CLAUSE {type: STRING}
            INCORPORATED_IN {state: STRING}

            The relationships:
            (:Agreement)-[:HAS_CLAUSE]->(:ContractClause)
            (:ContractClause)-[:HAS_EXCERPT]->(:Excerpt)
            (:ContractClause)-[:HAS_TYPE]->(:ClauseType)
            (:Agreement)-[:GOVERNED_BY_LAW]->(:Country)
            (:Organization)-[:IS_PARTY_TO]->(:Agreement)
            (:Organization)-[:INCORPORATED_IN]->(:Country)
        """

        # Initialize text-to-Cypher retriever
        retriever = Text2CypherRetriever(
            driver=self.driver, llm=self.llm, neo4j_schema=neo4j_schema
        )

        # Generate and execute Cypher query
        retriever_result = retriever.search(query_text=user_question)

        # Format answer
        answer = ""
        for item in retriever_result.items:
            content = str(item.content)
            if content:
                answer += content + "\n\n"

        return answer if answer else "No results found."

    def get_contract_excerpts(self, contract_id: int) -> dict:
        """
        Get contract details with all clause excerpts.

        Args:
            contract_id: The ID of the contract

        Returns:
            Contract details with clause excerpts
        """
        if contract_id <= 0:
            return {"error": "Contract ID must be positive"}

        query = """
            MATCH (a:Agreement {contract_id: $contract_id})-[:HAS_CLAUSE]->(cc:ContractClause)
                  -[:HAS_EXCERPT]->(e:Excerpt)
            RETURN a as agreement, cc.type as contract_clause_type, collect(e.text) as excerpts
        """

        records, _, _ = self.driver.execute_query(query, {"contract_id": contract_id})

        if not records:
            return {"error": f"Contract {contract_id} not found"}

        agreement_node = records[0]["agreement"]

        # Build clause dict with excerpts
        clause_dict = {}
        for record in records:
            clause_type = record["contract_clause_type"]
            excerpts = record["excerpts"]
            clause_dict[clause_type] = excerpts

        # Build clauses list with excerpts
        clauses = []
        for clause_type, excerpts in clause_dict.items():
            clauses.append({"clause_type": clause_type, "excerpts": excerpts})

        return {
            "contract_id": agreement_node.get("contract_id"),
            "name": agreement_node.get("name"),
            "agreement_type": agreement_node.get("agreement_type"),
            "effective_date": agreement_node.get("effective_date"),
            "expiration_date": agreement_node.get("expiration_date"),
            "renewal_term": agreement_node.get("renewal_term"),
            "clauses": clauses,
        }

    def close(self):
        """Close the Neo4j driver connection."""
        self.driver.close()

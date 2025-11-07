"""
STEP 2: Build Knowledge Graph from Extracted Contracts (JSON → Neo4j)

This script loads the extracted contract JSON files and builds a knowledge graph
in Neo4j with embeddings for semantic search.

The Agent Framework makes it easy to:
- Generate embeddings using any LLM provider
- Switch between Azure OpenAI, OpenAI, Anthropic, etc.
- Process data efficiently with async operations

The knowledge graph enables:
- Graph traversal across contracts and clauses
- Semantic search using vector embeddings
- Full-text search across excerpts
- Relationship queries between entities

Input: JSON files in ./data/output/
Output: Neo4j knowledge graph with embeddings
"""

import asyncio
import json
from pathlib import Path

from azure.identity import DefaultAzureCredential
from neo4j import Driver, GraphDatabase

from contract_graphrag.settings import settings

# Cypher query to create the complete graph structure
CREATE_GRAPH_QUERY = """/*cypher*/
WITH $data AS data
WITH data.agreement as a

// Create Agreement node
MERGE (agreement:Agreement {contract_id: a.contract_id})
ON CREATE SET
  agreement.name = a.agreement_name,
  agreement.effective_date = a.effective_date,
  agreement.expiration_date = a.expiration_date,
  agreement.agreement_type = a.agreement_type,
  agreement.renewal_term = a.renewal_term,
  agreement.most_favored_country = a.governing_law.most_favored_country,
  agreement.Notice_period_to_Terminate_Renewal = a.Notice_period_to_Terminate_Renewal

// Create governing law country
MERGE (gl_country:Country {name: a.governing_law.country})
MERGE (agreement)-[gbl:GOVERNED_BY_LAW]->(gl_country)
SET gbl.state = a.governing_law.state

// Create parties and their relationships
FOREACH (party IN a.parties |
  MERGE (p:Organization {name: party.name})
  MERGE (p)-[ipt:IS_PARTY_TO]->(agreement)
  SET ipt.role = party.role
  MERGE (country_of_incorporation:Country {name: party.incorporation_country})
  MERGE (p)-[incorporated:INCORPORATED_IN]->(country_of_incorporation)
  SET incorporated.state = party.incorporation_state
)

// Create clauses and excerpts (only for clauses that exist)
WITH a, agreement, [clause IN a.clauses WHERE clause.exists = true] AS valid_clauses
FOREACH (clause IN valid_clauses |
  CREATE (cl:ContractClause {type: clause.clause_type})
  MERGE (agreement)-[clt:HAS_CLAUSE]->(cl)
  SET clt.type = clause.clause_type

  // Create excerpts
  FOREACH (excerpt IN clause.excerpts |
    MERGE (cl)-[:HAS_EXCERPT]->(e:Excerpt {text: excerpt})
  )

  // Link to ClauseType
  MERGE (clType:ClauseType{name: clause.clause_type})
  MERGE (cl)-[:HAS_TYPE]->(clType)
)
"""

# Database indices for efficient queries
INDICES = [
    (
        "excerpt_vector_index",
        """/*cypher*/
        CREATE VECTOR INDEX excerpt_vector_index IF NOT EXISTS
        FOR (e:Excerpt) ON (e.embedding)
        OPTIONS {
            indexConfig: {
                `vector.dimensions`: 1536,
                `vector.similarity_function`: 'cosine'
            }
        }
    """,
    ),
    (
        "excerpt_text_index",
        """/*cypher*/
        CREATE FULLTEXT INDEX excerpt_text_index IF NOT EXISTS
        FOR (e:Excerpt) ON EACH [e.text]
    """,
    ),
    (
        "agreement_type_index",
        """/*cypher*/
        CREATE FULLTEXT INDEX agreement_type_index IF NOT EXISTS
        FOR (a:Agreement) ON EACH [a.agreement_type]
    """,
    ),
    (
        "clause_type_index",
        """
        CREATE FULLTEXT INDEX clause_type_index IF NOT EXISTS
        FOR (ct:ClauseType) ON EACH [ct.name]
    """,
    ),
    (
        "organization_name_index",
        """/*cypher*/
        CREATE FULLTEXT INDEX organization_name_index IF NOT EXISTS
        FOR (o:Organization) ON EACH [o.name]
    """,
    ),
    (
        "agreement_id_index",
        """/*cypher*/
        CREATE INDEX agreement_id_index IF NOT EXISTS
        FOR (a:Agreement) ON (a.contract_id)
    """,
    ),
]


async def generate_embedding(text: str) -> list[float]:
    """
    Generate an embedding vector for text using Azure OpenAI.

    Uses the configured embedding model (defaults to text-embedding-3-small with 1536 dimensions).
    This follows Microsoft's recommended authentication pattern using
    get_bearer_token_provider with DefaultAzureCredential.

    DefaultAzureCredential automatically tries multiple auth methods:
    - Environment variables (service principal credentials)
    - Managed Identity (for Azure resources)
    - Azure CLI (for local development)
    - And more...

    Args:
        text: Text to embed

    Returns:
        List of floats representing the embedding vector
    """
    from azure.identity import get_bearer_token_provider
    from openai import AzureOpenAI

    # Create token provider using DefaultAzureCredential
    # This handles both local (CLI) and remote (service principal) authentication
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), settings.azure_openai_scope
    )

    # Create OpenAI client with token-based authentication
    client = AzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        azure_ad_token_provider=token_provider,
        api_version="2024-10-21",
    )

    # Generate embedding using configured model
    response = client.embeddings.create(
        input=text,
        model=settings.azure_openai_embedding_model,
        dimensions=settings.azure_openai_embedding_dimensions,
    )

    return response.data[0].embedding


def load_contracts_from_json(json_dir: Path) -> list[dict]:
    """
    Load all contract JSON files from the output directory.

    Args:
        json_dir: Directory containing JSON files

    Returns:
        List of contract data dictionaries with contract_id added
    """
    contracts: list[dict] = []
    json_files = sorted(json_dir.glob("*.json"))

    if not json_files:
        print(f"No JSON files found in {json_dir}")
        return contracts

    for contract_id, json_path in enumerate(json_files, start=1):
        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
                # Validate required structure
                if "agreement" not in data:
                    print(f"  ⚠ Skipping {json_path.name}: Missing 'agreement' key")
                    continue
                # Add contract_id for unique identification
                data["agreement"]["contract_id"] = contract_id
                contracts.append(data)
        except json.JSONDecodeError as e:
            print(f"  ⚠ Skipping {json_path.name}: Invalid JSON - {e}")
        except Exception as e:
            print(f"  ⚠ Skipping {json_path.name}: {e}")

    return contracts


def create_indices(driver: Driver) -> None:
    """
    Create database indices for efficient queries.

    Args:
        driver: Neo4j driver instance
    """
    print("\nCreating database indices...")

    for index_name, index_query in INDICES:
        # Check if index exists
        check_query = "SHOW INDEXES WHERE name = $index_name"
        result = driver.execute_query(check_query, parameters_={"index_name": index_name})

        if result.records:
            print(f"  ✓ {index_name} already exists")
        else:
            driver.execute_query(index_query)  # type: ignore[arg-type]
            print(f"  ✓ Created {index_name}")


async def generate_embeddings_for_excerpts(driver: Driver) -> None:
    """
    Generate embeddings for all Excerpt nodes that don't have embeddings yet.

    Args:
        driver: Neo4j driver instance
    """
    # Get excerpts without embeddings
    query = """
        MATCH (e:Excerpt)
        WHERE e.text IS NOT NULL AND e.embedding IS NULL
        RETURN e.text AS text, elementId(e) AS element_id
    """

    result = driver.execute_query(query)
    excerpts = [(record["text"], record["element_id"]) for record in result.records]

    if not excerpts:
        print("  ✓ All excerpts already have embeddings")
        return

    print(f"  Generating embeddings for {len(excerpts)} excerpts...")

    # Generate embeddings in batches
    for i, (text, element_id) in enumerate(excerpts, 1):
        try:
            # Generate embedding
            embedding = await generate_embedding(text)

            # Update the node with embedding
            update_query = """
                MATCH (e:Excerpt)
                WHERE elementId(e) = $element_id
                SET e.embedding = $embedding
            """
            driver.execute_query(
                update_query, parameters_={"element_id": element_id, "embedding": embedding}
            )

            if i % 10 == 0 or i == len(excerpts):
                print(f"    Processed {i}/{len(excerpts)} excerpts")
        except Exception as e:
            print(f"    ⚠ Failed to generate embedding for excerpt {i}: {e}")

    print(f"  ✓ Generated embeddings for {len(excerpts)} excerpts")


async def main():
    """Main function to build the knowledge graph."""

    print("\n" + "=" * 60)
    print("Building Knowledge Graph from Extracted Contracts")
    print("=" * 60)

    # Setup
    json_dir = Path("./data/output/")

    # Load contracts
    print(f"\nLoading contracts from {json_dir}...")
    contracts = load_contracts_from_json(json_dir)

    if not contracts:
        print("No contracts to process. Please run 01_extract_contracts.py first.")
        return

    print(f"  ✓ Loaded {len(contracts)} contract(s)")

    # Connect to Neo4j using settings
    print(f"\nConnecting to Neo4j at {settings.neo4j_uri}...")
    try:
        driver = GraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_username, settings.neo4j_password)
        )
        # Verify connection
        driver.verify_connectivity()
        print("  ✓ Connected to Neo4j")
    except Exception as e:
        print(f"\n✗ Failed to connect to Neo4j: {e}")
        print("  Please check your Neo4j connection settings in .env")
        print(f"  URI: {settings.neo4j_uri}")
        print(f"  Username: {settings.neo4j_username}")
        return

    try:
        # Create graph structure
        print("\nCreating graph nodes and relationships...")
        for i, contract_data in enumerate(contracts, 1):
            try:
                agreement_name = contract_data["agreement"].get("agreement_name", "Unknown")
                driver.execute_query(CREATE_GRAPH_QUERY, parameters_={"data": contract_data})
                print(f"  ✓ Created graph for contract {i}/{len(contracts)}: {agreement_name}")
            except Exception as e:
                print(f"  ✗ Failed to create graph for contract {i}: {e}")

        # Create indices
        create_indices(driver)

        # Generate embeddings
        print("\nGenerating embeddings for clause excerpts...")
        await generate_embeddings_for_excerpts(driver)

        # Summary
        print("\n" + "=" * 60)
        print("Knowledge Graph Built Successfully!")
        print("=" * 60)
        print("\nGraph Statistics:")

        # Get node counts
        stats_query = """
            RETURN
                COUNT{(a:Agreement)} AS agreements,
                COUNT{(o:Organization)} AS organizations,
                COUNT{(c:ContractClause)} AS clauses,
                COUNT{(e:Excerpt)} AS excerpts,
                COUNT{(ct:ClauseType)} AS clause_types
        """
        result = driver.execute_query(stats_query)
        stats = result.records[0]

        print(f"  - Agreements: {stats['agreements']}")
        print(f"  - Organizations: {stats['organizations']}")
        print(f"  - Contract Clauses: {stats['clauses']}")
        print(f"  - Clause Excerpts: {stats['excerpts']}")
        print(f"  - Clause Types: {stats['clause_types']}")
        print("\n" + "=" * 60)

    finally:
        driver.close()


if __name__ == "__main__":
    asyncio.run(main())

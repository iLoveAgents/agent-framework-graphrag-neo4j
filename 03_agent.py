"""
DEMO 03: Contract Review Agent with Neo4j GraphRAG

Modern AI agent using Microsoft Agent Framework and Azure OpenAI Responses API.
Queries contract knowledge graph with natural language using GraphRAG.

The agent can:
- Answer questions about specific contracts
- Find contracts by organization, clause type, or semantic similarity
- Provide aggregation insights across all contracts
- Support streaming responses for better UX

Run with: uv run 03_agent.py

Compatible with Agent Framework Dev UI for interactive testing.
"""

import asyncio
import sys

from azure.identity import DefaultAzureCredential

from contract_graphrag.agent_config import create_agent_with_tools
from contract_graphrag.contract_tools import ContractTools


async def interactive_mode() -> None:
    """
    Run the agent in interactive mode for testing.

    This mode allows you to chat with the agent directly from the terminal.
    Type 'exit' to quit.
    """
    print("\n" + "=" * 60)
    print("Contract Review Agent - Interactive Mode")
    print("=" * 60)
    print("\nInitializing agent...")

    # Create contract tools and verify connection
    try:
        credential = DefaultAzureCredential()
    except Exception as e:
        print(f"\n✗ Failed to authenticate with Azure: {e}")
        print("  Please run 'az login' or check your Azure credentials")
        return

    # Use context managers for proper resource cleanup
    try:
        with ContractTools() as tools:
            async with create_agent_with_tools(credential, tools) as agent:
                print("✓ Agent ready!\n")
                print("Example questions:")
                print("  - Tell me about contract 1")
                print("  - Find contracts for AT&T")
                print("  - Get contracts with Price Restrictions but without Insurance")
                print("  - Show me contracts mentioning product delivery")
                print("  - How many contracts are in the database?")
                print("\nType 'exit' to quit\n")
                print("=" * 60 + "\n")

                while True:
                    # Get user input
                    try:
                        user_input = input("You: ").strip()
                    except (EOFError, KeyboardInterrupt):
                        print("\nGoodbye!")
                        break

                    if not user_input:
                        continue

                    if user_input.lower() in ["exit", "quit", "bye"]:
                        print("Goodbye!")
                        break

                    # Stream response
                    print("\nAgent: ", end="", flush=True)
                    try:
                        async for chunk in agent.run_stream(user_input):
                            if chunk.text:
                                print(chunk.text, end="", flush=True)
                        print("\n")
                    except KeyboardInterrupt:
                        print("\n\nInterrupted. Type 'exit' to quit.\n")
                    except Exception as e:
                        print(f"\n✗ Error: {e}\n")
                        print("  Check your Azure OpenAI and Neo4j connections\n")
    except Exception as e:
        print(f"\n✗ Failed to initialize contract tools: {e}")
        print("  Please check your Neo4j connection in .env")


async def demo_queries() -> None:
    """
    Run a set of demo queries to showcase the agent's capabilities.

    Demonstrates:
    - Contract retrieval
    - Organization search
    - Clause-based queries
    - Semantic search
    - Aggregation queries
    """
    print("\n" + "=" * 60)
    print("Contract Review Agent - Demo Mode")
    print("=" * 60)
    print("\nInitializing agent...")

    # Create agent
    try:
        credential = DefaultAzureCredential()
    except Exception as e:
        print(f"\n✗ Failed to authenticate with Azure: {e}")
        print("  Please run 'az login' or check your Azure credentials")
        return

    # Use context managers for proper resource cleanup
    try:
        with ContractTools() as tools:
            async with create_agent_with_tools(credential, tools) as agent:
                print("✓ Agent ready!\n")

                # Demo queries
                queries = [
                    "Tell me about contract 1",
                    "Find contracts where AT&T is a party",
                    "Get contracts with Price Restrictions clause",
                    "Show me contracts that don't have Insurance clauses",
                    "Find contracts mentioning product delivery requirements",
                    "How many contracts are in the database?",
                ]

                for i, query in enumerate(queries, 1):
                    print("=" * 60)
                    print(f"\nQuery {i}: {query}\n")
                    print("Agent: ", end="", flush=True)

                    try:
                        async for chunk in agent.run_stream(query):
                            if chunk.text:
                                print(chunk.text, end="", flush=True)
                        print("\n")
                    except Exception as e:
                        print(f"\n✗ Error: {e}\n")

                    # Small delay between queries
                    await asyncio.sleep(1)

                print("=" * 60)
                print("\nDemo complete!")
    except Exception as e:
        print(f"\n✗ Failed to initialize contract tools: {e}")
        print("  Please check your Neo4j connection in .env")


async def main() -> None:
    """Main entry point."""
    # Check if demo mode is requested
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        await demo_queries()
    else:
        await interactive_mode()


if __name__ == "__main__":
    asyncio.run(main())

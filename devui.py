"""
DevUI Launcher for Contract Review Agent

Launch the agent with a visual debugging interface in your browser.
This provides an interactive chat UI with event/trace viewer for testing.

Run with: uv run devui.py

The DevUI will automatically open at http://127.0.0.1:8080
"""

from agent_framework.devui import serve
from azure.identity import DefaultAzureCredential

from contract_graphrag.agent_config import create_agent_with_tools
from contract_graphrag.contract_tools import ContractTools


def main():
    """Launch the agent via DevUI."""
    print("\n" + "=" * 60)
    print("Contract Review Agent - DevUI Mode")
    print("=" * 60)
    print("\nInitializing agent for DevUI...")

    # Create Azure credential
    try:
        credential = DefaultAzureCredential()
    except Exception as e:
        print(f"\n✗ Failed to create Azure credential: {e}")
        print("  Please run 'az login' or check your Azure credentials")
        return

    # Use context manager for proper resource cleanup
    # Note: serve() is blocking, cleanup happens on Ctrl+C shutdown
    try:
        with ContractTools() as tools:
            agent = create_agent_with_tools(credential, tools)

            print("✓ Agent ready!")
            print("\nLaunching DevUI in your browser...")
            print("The UI will open at http://127.0.0.1:8080")
            print("\nExample questions to try:")
            print("  - Tell me about contract 1")
            print("  - Find contracts for AT&T")
            print("  - Get contracts with Price Restrictions but without Insurance")
            print("  - Show me contracts mentioning product delivery")
            print("  - How many contracts are in the database?")
            print("\nPress Ctrl+C to stop the server\n")
            print("=" * 60 + "\n")

            # Serve the agent via DevUI (blocking call)
            serve(entities=[agent], auto_open=True)
    except Exception as e:
        print(f"\n✗ Failed to initialize contract tools: {e}")
        print("  Please check your Neo4j connection in .env")


if __name__ == "__main__":
    main()

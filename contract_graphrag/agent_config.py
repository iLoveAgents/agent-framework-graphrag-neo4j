"""
Shared Agent Configuration for Contract Review.

Provides common agent setup logic used by both the terminal demo
and the DevUI browser interface.
"""

from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import DefaultAzureCredential

from .contract_tools import ContractTools

# System instructions for the contract review agent
AGENT_INSTRUCTIONS = """You are a seasoned legal expert specializing in commercial contract review and analysis.

Your expertise lies in:
- Identifying critical elements within legal documents
- Assessing compliance with legal standards
- Analyzing contractual relationships and obligations
- Providing clear, accurate information about contract terms

You have access to a knowledge graph of contracts with tools to:
- Retrieve specific contract details
- Search contracts by organization, clause type, or content
- Find semantic similarities across contract clauses
- Answer analytical questions about the contract database

Always provide accurate, well-structured responses based on the contract data.
When citing contract information, reference specific contract IDs when available.
"""


def create_agent_with_tools(credential: DefaultAzureCredential, tools: ContractTools):
    """
    Create an agent with contract review tools.

    Args:
        credential: Azure credential for authentication
        tools: ContractTools instance with graph database access

    Returns:
        Agent configured with contract review capabilities
    """
    return AzureOpenAIResponsesClient(credential=credential).create_agent(
        instructions=AGENT_INSTRUCTIONS,
        name="ContractReviewAgent",
        tools=[
            tools.get_contract,
            tools.get_contracts_by_organization,
            tools.get_contracts_with_clause_type,
            tools.get_contracts_without_clause,
            tools.get_contracts_similar_text,
            tools.answer_aggregation_question,
            tools.get_contract_excerpts,
        ],
    )

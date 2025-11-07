"""
Contract Search Tools for Agent Framework.

Provides function tools that wrap Neo4j GraphRAG queries for contract analysis.
These tools can be used by agents to answer questions about contracts.
"""

import json
from typing import Annotated

from .contract_service import ContractSearchService


class ContractTools:
    """
    Function tools for contract search and analysis.

    Use as a context manager to ensure proper resource cleanup:
        with ContractTools() as tools:
            result = tools.get_contract(1)
    """

    def __init__(self):
        """Initialize contract tools with service."""
        self.service = ContractSearchService()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures service connection is closed."""
        self.close()
        return False

    def close(self):
        """Close the service connection."""
        self.service.close()

    def get_contract(
        self, contract_id: int
    ) -> Annotated[str, "Detailed information about a specific contract"]:
        """
        Get detailed information about a contract by its ID.

        Args:
            contract_id: The ID of the contract to retrieve (e.g., 1, 2, 3)

        Returns:
            JSON string with full contract details including parties, clauses, and dates
        """
        result = self.service.get_contract(contract_id)
        return json.dumps(result, indent=2)

    def get_contracts_by_organization(
        self, organization_name: str
    ) -> Annotated[str, "List of contracts involving the specified organization"]:
        """
        Find all contracts where a specific organization is a party.

        Args:
            organization_name: Name of the organization to search for (partial matches allowed)

        Returns:
            JSON string with list of contracts and basic details
        """
        result = self.service.get_contracts_by_organization(organization_name)
        return json.dumps(result, indent=2)

    def get_contracts_with_clause_type(
        self, clause_type: str
    ) -> Annotated[str, "List of contracts containing the specified clause type"]:
        """
        Get contracts that contain a specific type of clause.

        Valid clause types include: 'Non-Compete', 'Exclusivity', 'IP Ownership Assignment',
        'License grant', 'Price Restrictions', 'Insurance', etc.

        Args:
            clause_type: The type of clause to search for (must match exactly)

        Returns:
            JSON string with list of contracts containing that clause type
        """
        result = self.service.get_contracts_with_clause_type(clause_type)
        return json.dumps(result, indent=2)

    def get_contracts_without_clause(
        self, clause_type: str
    ) -> Annotated[str, "List of contracts that do NOT contain the specified clause type"]:
        """
        Get contracts that do NOT contain a specific type of clause.

        Useful for finding gaps in contract coverage.

        Args:
            clause_type: The type of clause to exclude

        Returns:
            JSON string with list of contracts without that clause type
        """
        result = self.service.get_contracts_without_clause(clause_type)
        return json.dumps(result, indent=2)

    def get_contracts_similar_text(
        self, clause_text: str
    ) -> Annotated[str, "List of contracts with clauses semantically similar to the given text"]:
        """
        Find contracts with clauses semantically similar to the provided text.

        Uses AI-powered vector search to find relevant contract excerpts.
        Great for finding contracts that mention specific topics or concepts.

        Args:
            clause_text: Text to search for (e.g., "product delivery requirements")

        Returns:
            JSON string with relevant contracts, clause types, and matching excerpts
        """
        result = self.service.get_contracts_similar_text(clause_text)
        return json.dumps(result, indent=2)

    def answer_aggregation_question(
        self, user_question: str
    ) -> Annotated[str, "Answer to aggregation or analytical questions about contracts"]:
        """
        Answer analytical questions about the contract database.

        Uses AI to convert natural language questions to database queries.
        Best for counting, averaging, or finding patterns across contracts.

        Examples:
        - "How many contracts are there?"
        - "What's the average number of clauses per contract?"
        - "Which organizations have the most contracts?"

        Args:
            user_question: Natural language question about contracts

        Returns:
            Answer based on database analysis
        """
        result = self.service.answer_aggregation_question(user_question)
        return result

    def get_contract_excerpts(
        self, contract_id: int
    ) -> Annotated[str, "Contract details with all clause excerpts"]:
        """
        Get contract details including full text excerpts from all clauses.

        Useful for detailed contract review and analysis.

        Args:
            contract_id: The ID of the contract

        Returns:
            JSON string with contract details and all clause excerpts
        """
        result = self.service.get_contract_excerpts(contract_id)
        return json.dumps(result, indent=2)

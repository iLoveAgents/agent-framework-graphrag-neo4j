"""
GraphRAG Contract Analysis - Core Library

Shared modules for contract analysis using Microsoft Agent Framework,
Azure AI Foundry, and Neo4j.
"""

__version__ = "0.1.0"

from .agent_config import AGENT_INSTRUCTIONS, create_agent_with_tools
from .contract_service import ContractSearchService
from .contract_tools import ContractTools
from .schema import Agreement
from .settings import settings

__all__ = [
    "AGENT_INSTRUCTIONS",
    "create_agent_with_tools",
    "ContractSearchService",
    "ContractTools",
    "Agreement",
    "settings",
]

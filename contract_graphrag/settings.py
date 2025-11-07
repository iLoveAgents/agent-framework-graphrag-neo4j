"""
Application settings for the contract analysis system.

Loads configuration from environment variables and .env file.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings for Neo4j and Azure OpenAI connection."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Neo4j settings
    neo4j_uri: str = "neo4j://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = Field(..., description="Neo4j password")

    # Azure OpenAI settings
    azure_openai_endpoint: str = Field(..., description="Azure OpenAI endpoint URL")
    azure_openai_embedding_model: str = "text-embedding-3-small"
    azure_openai_embedding_dimensions: int = 1536
    azure_openai_responses_deployment_name: str = Field(
        default="gpt-5", description="Azure OpenAI Responses deployment name"
    )
    azure_openai_scope: str = "https://cognitiveservices.azure.com/.default"


# Load settings from .env file
settings = Settings()  # type: ignore[call-arg]

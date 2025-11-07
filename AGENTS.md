# Agent Development Guidelines

Development guide for AI coding agents working on this GraphRAG contract analysis demo.

## Quick Start

```bash
uv sync                # Install dependencies
cp .env.example .env   # Configure environment
az login               # Authenticate with Azure

# Run the pipeline
uv run 01_extract_contracts.py  # Extract PDFs to JSON
uv run 02_build_graph.py         # Build Neo4j graph
uv run 03_agent.py               # Run agent (terminal)
uv run devui.py                  # Run agent (browser UI)
```

## Code Standards

- **Style**: PEP 8, type hints, proper error handling
- **Imports**: stdlib → third-party → local modules
- **Authentication**: DefaultAzureCredential (Azure CLI, Managed Identity, etc.)
- **Linting**: `uv run ruff check . --fix && uv run ruff format .`

## Key Patterns

**Agent Creation (Azure OpenAI Responses API):**

```python
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()

agent = AzureOpenAIResponsesClient(credential=credential).create_agent(
    instructions="Clear, specific instructions",
    name="DescriptiveAgentName",
    tools=[...]  # Function tools
)
```

**Neo4j Connection:**

```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    settings.neo4j_uri,
    auth=(settings.neo4j_username, settings.neo4j_password)
)
```

**Context Managers for Resource Cleanup:**

```python
class Service:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
```

## Testing & Linting

```bash
# Python linting
uv run ruff check . --fix
uv run ruff format .

# Markdown linting
npx markdownlint-cli2 "*.md" --fix

# Run demo mode
uv run 03_agent.py --demo
```

## Project Structure

```text
├── 01_extract_contracts.py  # PDF → JSON extraction
├── 02_build_graph.py        # JSON → Neo4j graph with embeddings
├── 03_agent.py              # Agent demo (terminal)
├── devui.py                 # Agent demo (browser UI)
├── contract_graphrag/                     # Core library package
│   ├── __init__.py
│   ├── agent_config.py      # Shared agent configuration
│   ├── contract_service.py  # Neo4j GraphRAG data layer
│   ├── contract_tools.py    # Agent function tools
│   ├── schema.py            # Pydantic data models
│   ├── settings.py          # Configuration from .env
│   └── utils.py             # File handling utilities
├── prompts/                 # Prompt templates
├── data/                    # Input/output/debug files
├── README.md                # User documentation
├── AGENTS.md                # Developer guidelines (this file)
└── LICENSE                  # MIT License
```

## Important Notes

**Security:**

- Never commit `.env` (use `.env.example` template)
- Use DefaultAzureCredential for authentication
- Validate inputs before passing to agents/database

**Resource Management:**

- Always use context managers for Neo4j connections
- Close drivers and connections properly
- Use `try`/`except` for error handling with actionable messages

**Git Commits:**

- Write clear, descriptive messages
- Run linting before committing
- Keep commit scope focused and atomic

## Common Commands

```bash
uv sync                              # Install dependencies
uv run 03_agent.py                   # Run terminal agent
uv run 03_agent.py --demo            # Run demo queries
uv run devui.py                      # Run browser UI agent
uv add package-name                  # Add dependency
uv run ruff check . --fix            # Lint Python
npx markdownlint-cli2 "*.md" --fix   # Lint Markdown
az login                             # Azure auth
```

## Troubleshooting

- **Import Error**: Run `uv sync`
- **Azure Auth Failed**: Run `az login`
- **Neo4j Connection Error**: Check Neo4j is running, verify `.env` credentials
- **Environment Variables Not Found**: Ensure `.env` exists with all required variables

## Resources

- [Microsoft Agent Framework](https://learn.microsoft.com/en-us/agent-framework/)
- [Azure AI Foundry](https://learn.microsoft.com/en-us/azure/ai-studio/)
- [Azure OpenAI Service](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [uv Documentation](https://github.com/astral-sh/uv)

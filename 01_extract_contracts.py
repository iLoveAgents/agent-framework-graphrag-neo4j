"""
STEP 1: Extract Relevant Information from Contracts (LLM + Contract)

This script demonstrates how to use the Agent Framework's abstraction layer
to extract structured information from PDF contracts using different LLM providers.

The Agent abstraction makes it easy to:
- Switch between Azure OpenAI, OpenAI, Anthropic, etc.
- Use structured outputs with Pydantic models
- Process multimodal inputs (PDF + text)

The extracted information includes:
- Contract parties and their roles
- Key dates (effective, expiration, renewal terms)
- Governing law and jurisdiction
- Clause types and relevant excerpts

Input: PDF files in ./data/input/
Output: JSON files in ./data/output/
"""

import asyncio
import json
from pathlib import Path

from agent_framework import ChatMessage, DataContent, Role, TextContent
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import DefaultAzureCredential

from contract_graphrag.schema import Agreement
from contract_graphrag.utils import read_text_file, save_json_string_to_file


async def extract_contract_from_pdf(
    agent,  # Agent from AzureOpenAIResponsesClient.create_agent()
    pdf_path: Path,
    extraction_prompt: str,
) -> Agreement:
    """
    Extract contract information from a PDF file using an Agent.

    Args:
        agent: Agent configured with system prompt and model
        pdf_path: Path to the PDF file
        extraction_prompt: User prompt for contract extraction

    Returns:
        Agreement: Extracted contract information as a structured Agreement object
    """
    # Read PDF as bytes
    with open(pdf_path, "rb") as pdf_file:
        pdf_bytes = pdf_file.read()

    if not pdf_bytes:
        raise ValueError(f"PDF file is empty: {pdf_path}")

    # Create message with text prompt and PDF data
    text_content = TextContent(text=extraction_prompt)
    pdf_content = DataContent(
        data=pdf_bytes,
        media_type="application/pdf",
        additional_properties={"filename": pdf_path.name},
    )
    message = ChatMessage(role=Role.USER, contents=[text_content, pdf_content])
    # Get structured response from agent
    response = await agent.run(message, response_format=Agreement)

    return response.value


def create_extraction_agent(system_prompt: str):
    """
    Create an agent for contract extraction.

    Uses DefaultAzureCredential which automatically tries multiple auth methods:
    - Environment variables (service principal credentials)
    - Managed Identity (for Azure resources)
    - Azure CLI (for local development)
    - Visual Studio Code
    - And more...
    """
    # Using Azure OpenAI Responses Client with DefaultAzureCredential
    # This handles both local (CLI) and remote (service principal) authentication
    client = AzureOpenAIResponsesClient(
        credential=DefaultAzureCredential(),
    )

    # Create agent with system instructions
    agent = client.create_agent(
        name="contract-extractor",
        instructions=system_prompt,
        model_kwargs={
            "max_tokens": 4000,  # Ensure enough tokens for full extraction
            "temperature": 0.1,  # Low temperature for consistent extraction
        },
    )

    return agent


async def main():
    """Main function to process all PDF contracts in the input directory."""

    # Load prompts
    system_prompt = read_text_file("./prompts/system_prompt.txt")
    extraction_prompt = read_text_file("./prompts/contract_extraction_prompt.txt")

    # Create extraction agent
    # This abstraction makes it easy to swap LLM providers!
    agent = create_extraction_agent(system_prompt)

    # Setup directories
    input_dir = Path("./data/input/")
    output_dir = Path("./data/output/")

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all PDF files in the input directory
    pdf_files = list(input_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {input_dir}")
        print("Please add PDF contract files to the ingestion/data/input/ directory.")
        return

    print(f"\nFound {len(pdf_files)} PDF file(s) to process:")
    for pdf_file in pdf_files:
        print(f"  - {pdf_file.name}")

    # Process each PDF file
    print("\n" + "=" * 60)
    for pdf_path in pdf_files:
        print(f"\nProcessing {pdf_path.name}...")

        try:
            # Extract contract information using the agent
            agreement = await extract_contract_from_pdf(
                agent=agent,
                pdf_path=pdf_path,
                extraction_prompt=extraction_prompt,
            )

            # Save as JSON
            output_path = output_dir / f"{pdf_path.stem}.json"
            contract_json = json.dumps({"agreement": agreement.model_dump()}, indent=2)
            save_json_string_to_file(contract_json, str(output_path))

            print(f"  ✓ Saved to {output_path}")

        except ValueError as e:
            print(f"  ✗ Validation Error: {e}")
        except Exception as e:
            print(f"  ✗ Error processing {pdf_path.name}: {e}")
            print("     Check that the PDF is valid and readable")

    print("\n" + "=" * 60)
    print("Extraction complete!")
    print(f"Results saved to: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

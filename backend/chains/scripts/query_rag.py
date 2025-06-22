import os
import sys
import asyncio
import argparse
import json
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add the project root to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, project_root)

# Import the RAG agent
from backend.scripts.agents.chat_rag_agent import get_rag_agent

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Query the RAG system")
    parser.add_argument("query", type=str, help="The query to process")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--verbose", action="store_true", help="Show verbose output with more source details")
    return parser.parse_args()

def extract_sources_from_metadata(sources: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Extract and format source information from metadata.
    
    Args:
        sources: List of source metadata dictionaries
        
    Returns:
        List of formatted source dictionaries with title and URL
    """
    formatted_sources = []
    
    for source in sources:
        # Get basic metadata
        title = source.get("title", "Unknown Source")
        url = source.get("url", "")
        file_path = source.get("source", "")
        
        # Create a source entry
        source_entry = {
            "title": title if title != "Unknown" else os.path.basename(file_path),
            "url": url,
            "file": file_path
        }
        
        formatted_sources.append(source_entry)
    
    return formatted_sources

async def main():
    """Main function to query the RAG system."""
    # Parse arguments
    args = parse_arguments()
    
    # Load environment variables
    load_dotenv()
    
    # Get the RAG agent
    agent = get_rag_agent()
    
    # Process the query
    print(f"\nProcessing query: {args.query}\n")
    response = await agent.process_query(args.query)
    
    # Extract sources
    sources = extract_sources_from_metadata(response["sources"])
    
    # Output the response
    if args.json:
        # Add formatted sources to the response
        response["formatted_sources"] = sources
        print(json.dumps(response, indent=2))
    else:
        # Output as text with sources
        print("\n" + response["text"] + "\n")
        
        if sources:
            print("Sources:")
            for idx, source in enumerate(sources, 1):
                print(f"{idx}. {source['title']}")
                if source['url']:
                    print(f"   URL: {source['url']}")
                if args.verbose and source['file']:
                    print(f"   File: {source['file']}")
                print()
        
        # Print timing information
        print(f"Processing time: {response['duration_ms']:.2f}ms")

if __name__ == "__main__":
    asyncio.run(main()) 
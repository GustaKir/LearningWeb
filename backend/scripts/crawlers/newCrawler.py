import os
import sys
import json
import asyncio
import requests
from xml.etree import ElementTree
from typing import List, Dict, Any, Set
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse, quote
from dotenv import load_dotenv
import pathlib
import re

# Add the project root to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, project_root)

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from openai import AsyncOpenAI

load_dotenv()

# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define corpus directory
CORPUS_DIR = os.path.join(project_root, "data/corpus")
# Ensure the corpus directory exists
os.makedirs(CORPUS_DIR, exist_ok=True)

@dataclass
class ProcessedChunk:
    url: str
    chunk_number: int
    title: str
    summary: str
    content: str
    metadata: Dict[str, Any]

def sanitize_filename(url: str) -> str:
    """Convert URL to a safe filename."""
    parsed_url = urlparse(url)
    # Use domain as directory and path as filename
    domain = parsed_url.netloc
    path = parsed_url.path.strip('/')
    if not path:
        path = 'index'
    # Replace problematic characters
    path = path.replace('/', '_')
    return f"{domain}/{path}"

def chunk_text(text: str, chunk_size: int = 5000) -> List[str]:
    """Split text into chunks, respecting code blocks and paragraphs."""
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        # Calculate end position
        end = start + chunk_size

        # If we're at the end of the text, just take what's left
        if end >= text_length:
            chunks.append(text[start:].strip())
            break

        # Try to find a code block boundary first (```)
        chunk = text[start:end]
        code_block = chunk.rfind('```')
        if code_block != -1 and code_block > chunk_size * 0.3:
            end = start + code_block

        # If no code block, try to break at a paragraph
        elif '\n\n' in chunk:
            # Find the last paragraph break
            last_break = chunk.rfind('\n\n')
            if last_break > chunk_size * 0.3:  # Only break if we're past 30% of chunk_size
                end = start + last_break

        # If no paragraph break, try to break at a sentence
        elif '. ' in chunk:
            # Find the last sentence break
            last_period = chunk.rfind('. ')
            if last_period > chunk_size * 0.3:  # Only break if we're past 30% of chunk_size
                end = start + last_period + 1

        # Extract chunk and clean it up
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move start position for next chunk
        start = max(start + 1, end)

    return chunks

async def get_title_and_summary(chunk: str, url: str) -> Dict[str, str]:
    """Extract title and summary using GPT-4."""
    system_prompt = """You are an AI that extracts titles and summaries from documentation chunks.
    Return a JSON object with 'title' and 'summary' keys.
    For the title: If this seems like the start of a document, extract its title. If it's a middle chunk, derive a descriptive title.
    For the summary: Create a concise summary of the main points in this chunk.
    Keep both title and summary concise but informative."""
    
    try:
        response = await openai_client.chat.completions.create(
            model=os.getenv("CHAT_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"URL: {url}\n\nContent:\n{chunk[:1000]}..."}  # Send first 1000 chars for context
            ],
            response_format={ "type": "json_object" }
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error getting title and summary: {e}")
        return {"title": "Error processing title", "summary": "Error processing summary"}

async def process_chunk(chunk: str, chunk_number: int, url: str) -> ProcessedChunk:
    """Process a single chunk of text."""
    # Get title and summary
    extracted = await get_title_and_summary(chunk, url)
    
    # Create metadata
    metadata = {
        "source": url,
        "chunk_size": len(chunk),
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "url_path": urlparse(url).path
    }
    
    return ProcessedChunk(
        url=url,
        chunk_number=chunk_number,
        title=extracted['title'],
        summary=extracted['summary'],
        content=chunk,  # Store the original chunk content
        metadata=metadata
    )

async def save_chunk_to_file(chunk: ProcessedChunk):
    """Save a processed chunk to a file in the corpus directory."""
    try:
        # Create directory structure
        safe_filename = sanitize_filename(chunk.url)
        dir_path = os.path.join(CORPUS_DIR, os.path.dirname(safe_filename))
        os.makedirs(dir_path, exist_ok=True)
        
        # Create the full filepath with chunk number suffix
        filepath = os.path.join(CORPUS_DIR, f"{safe_filename}.txt")
        
        # If there are multiple chunks, append the chunk number
        if chunk.chunk_number > 0:
            filepath = os.path.join(CORPUS_DIR, f"{safe_filename}_{chunk.chunk_number}.txt")
        
        # Create the content with metadata
        content = f"Title: {chunk.title}\n"
        content += f"URL: {chunk.url}\n"
        content += f"Summary: {chunk.summary}\n"
        content += "---\n\n"
        content += chunk.content
        
        # Save the file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Saved chunk {chunk.chunk_number} to {filepath}")
        return filepath
    except Exception as e:
        print(f"Error saving chunk to file: {e}")
        return None

async def process_and_store_document(url: str, markdown: str):
    """Process a document and store its chunks as files."""
    # Split into chunks
    chunks = chunk_text(markdown)
    
    # Process chunks in parallel
    tasks = [
        process_chunk(chunk, i, url) 
        for i, chunk in enumerate(chunks)
    ]
    processed_chunks = await asyncio.gather(*tasks)
    
    # Store chunks as files in parallel
    save_tasks = [
        save_chunk_to_file(chunk) 
        for chunk in processed_chunks
    ]
    saved_files = await asyncio.gather(*save_tasks)
    
    print(f"Processed document: {url} - Saved {len(saved_files)} chunks")
    return saved_files

async def crawl_url(url: str):
    """Crawl a single URL and process the result."""
    try:
        browser_config = BrowserConfig(
            headless=True,
            verbose=False,
            extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
        )
        # Only set parameters that are supported by CrawlerRunConfig
        crawl_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS
            # We ensure we're not following links by only processing
            # the direct content from the URL itself
        )

        # Create a new crawler instance for each URL
        crawler = AsyncWebCrawler(config=browser_config)
        await crawler.start()

        try:
            # Use a unique session_id to avoid any contamination between crawls
            session_id = f"session_{url.replace('://', '_').replace('/', '_').replace('.', '_')}"
            
            result = await crawler.arun(
                url=url,
                config=crawl_config,
                session_id=session_id
            )
            
            if result.success:
                print(f"Successfully crawled: {url}")
                # Only process the markdown from this specific URL
                await process_and_store_document(url, result.markdown.raw_markdown)
            else:
                print(f"Failed: {url} - Error: {result.error_message}")
        finally:
            await crawler.close()
    except Exception as e:
        print(f"Error crawling {url}: {e}")

async def crawl_parallel(urls: List[str], max_concurrent: int = 3):
    """Crawl multiple URLs in parallel with a concurrency limit."""
    # Use a semaphore to limit concurrency
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_url(url: str):
        async with semaphore:
            await crawl_url(url)
    
    # Process URLs in batches
    tasks = []
    for url in urls:
        task = asyncio.create_task(process_url(url))
        tasks.append(task)
        # Small delay between creating tasks to prevent overloading
        await asyncio.sleep(0.5)
    
    # Wait for all tasks to complete
    await asyncio.gather(*tasks)

def parse_sitemap(sitemap_url: str) -> List[str]:
    """Parse a sitemap XML and extract all URLs."""
    try:
        print(f"Parsing sitemap: {sitemap_url}")
        
        # Check if it's a local file path
        if sitemap_url.startswith("./") or sitemap_url.startswith("/"):
            try:
                with open(sitemap_url, 'r', encoding='utf-8') as f:
                    content = f.read()
                root = ElementTree.fromstring(content)
            except FileNotFoundError:
                print(f"Local sitemap file not found: {sitemap_url}")
                return []
        else:
            # Fetch the sitemap from URL
            response = requests.get(sitemap_url, timeout=30)
            response.raise_for_status()
            root = ElementTree.fromstring(response.content)
        
        # Find namespace
        ns = ''
        if '}' in root.tag:
            ns = root.tag.split('}')[0] + '}'
        
        # Extract URLs - handle both standard sitemaps and sitemapindex
        urls = []
        
        # Check if this is a sitemap index (contains other sitemaps)
        sitemap_tags = root.findall(f".//{ns}sitemap")
        if sitemap_tags:
            # This is a sitemap index, recursively parse each sitemap
            print(f"Found sitemap index with {len(sitemap_tags)} child sitemaps")
            for sitemap_tag in sitemap_tags:
                loc_tag = sitemap_tag.find(f"{ns}loc")
                if loc_tag is not None and loc_tag.text:
                    # Recursively fetch this sitemap
                    sub_urls = parse_sitemap(loc_tag.text)
                    urls.extend(sub_urls)
        else:
            # This is a regular sitemap, extract URLs directly
            url_tags = root.findall(f".//{ns}url")
            for url_tag in url_tags:
                loc_tag = url_tag.find(f"{ns}loc")
                if loc_tag is not None and loc_tag.text:
                    urls.append(loc_tag.text)
            print(f"Found {len(url_tags)} URLs in standard sitemap")
        
        print(f"Total: {len(urls)} URLs extracted from sitemap: {sitemap_url}")
        return urls
    except Exception as e:
        print(f"Error parsing sitemap {sitemap_url}: {e}")
        return []

def filter_streamlit_urls(urls: List[str]) -> List[str]:
    """Filter out Streamlit URLs that contain version numbers."""
    filtered_urls = []
    version_pattern = re.compile(r'docs\.streamlit\.io/\d+\.\d+\.\d+/')
    
    for url in urls:
        # Keep the URL if it's not a Streamlit URL or doesn't contain a version pattern
        if 'docs.streamlit.io' not in url or not version_pattern.search(url):
            filtered_urls.append(url)
    
    if len(urls) != len(filtered_urls):
        print(f"Filtered out {len(urls) - len(filtered_urls)} versioned Streamlit URLs")
    
    return filtered_urls

def get_urls_from_sitemaps() -> List[str]:
    """Get URLs from all specified sitemaps."""
    sitemaps = [
        "https://docs.streamlit.io/sitemap-0.xml", 
        "https://docs.python.org/sitemap.xml", 
        "https://fastapi.tiangolo.com/sitemap.xml",
        "./python_docs.xml"
    ]
    
    # Parse each sitemap and collect all URLs
    all_urls = []
    for sitemap in sitemaps:
        urls = parse_sitemap(sitemap)
        # Filter out versioned Streamlit URLs
        if 'streamlit' in sitemap:
            urls = filter_streamlit_urls(urls)
        all_urls.extend(urls)
        print(f"Added {len(urls)} URLs from {sitemap}")
    
    print(f"Total URLs from all sitemaps (before deduplication): {len(all_urls)}")
    return all_urls

async def main():
    """Main function to crawl all documentation from sitemaps."""
    # Get URLs from sitemaps
    urls = get_urls_from_sitemaps()
    
    if not urls:
        print("No URLs found to crawl")
        return
    
    # Filter to unique URLs and sort them for consistent processing
    unique_urls = sorted(set(urls))
    
    print(f"Found {len(unique_urls)} unique URLs to crawl from sitemaps")
    print(f"Documents will be saved to: {CORPUS_DIR}")
    
    # Crawl all URLs
    await crawl_parallel(unique_urls, max_concurrent=2)
    
    print("Crawling complete. Now you can run backend.chains.scripts.build_rag to build the RAG index.")

if __name__ == "__main__":
    asyncio.run(main())
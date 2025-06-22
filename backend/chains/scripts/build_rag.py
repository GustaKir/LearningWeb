import os
import sys
import glob
import json
import logging
import time
import re
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders.html import UnstructuredHTMLLoader as HTMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, project_root)

# Load environment variables
load_dotenv()

# Check if API key is set
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    logger.error("OPENAI_API_KEY environment variable is not set. Make sure it's in your .env file.")
    sys.exit(1)

# Constants
DATA_DIR = os.path.join(project_root, "data/corpus")
OUTPUT_DIR = os.path.join(project_root, "data/index")

def load_structured_text_file(file_path: str) -> List[Document]:
    """
    Load a text file with structured metadata (Title, URL, Summary) followed by content.
    Returns a Document with proper metadata.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract metadata using regex
        title_match = re.search(r'Title:\s*(.*?)(?:\n|$)', content)
        url_match = re.search(r'URL:\s*(.*?)(?:\n|$)', content)
        summary_match = re.search(r'Summary:\s*(.*?)(?:\n|$)', content)
        
        # Find the separator
        separator_index = content.find('---\n\n')
        
        if separator_index != -1:
            # Extract main content after the separator
            main_content = content[separator_index + 5:].strip()
            
            # Create metadata dictionary
            metadata = {
                "source": file_path,
                "title": title_match.group(1).strip() if title_match else None,
                "url": url_match.group(1).strip() if url_match else None,
                "summary": summary_match.group(1).strip() if summary_match else None,
            }
            
            # Create and return the document
            return [Document(page_content=main_content, metadata=metadata)]
        else:
            # Fallback: treat the whole content as a document
            logger.warning(f"No structured metadata found in {file_path}, treating as plain text")
            return [Document(page_content=content, metadata={"source": file_path})]
    
    except Exception as e:
        logger.error(f"Error loading structured file {file_path}: {e}")
        return []

def load_documents(directory: str = DATA_DIR) -> List[Document]:
    """
    Load all HTML and text documents from the specified directory.
    Returns a list of Documents.
    """
    logger.info(f"Loading documents from {directory}...")
    documents = []
    
    # Use recursive glob to find all HTML and text files
    html_files = glob.glob(f"{directory}/**/*.html", recursive=True)
    text_files = glob.glob(f"{directory}/**/*.txt", recursive=True)
    
    # Load HTML files
    for file_path in html_files:
        try:
            loader = HTMLLoader(file_path)
            docs = loader.load()
            # Add source information to metadata
            for doc in docs:
                doc.metadata["source"] = file_path
            documents.extend(docs)
            logger.debug(f"Loaded HTML document: {file_path}")
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
    
    # Load text files using our custom structured loader
    for file_path in text_files:
        try:
            docs = load_structured_text_file(file_path)
            documents.extend(docs)
            logger.debug(f"Loaded text document: {file_path}")
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
    
    logger.info(f"Loaded {len(documents)} documents.")
    return documents

def split_documents(documents: List[Document], chunk_size: int = 1000, chunk_overlap: int = 100) -> List[Document]:
    """
    Split documents into chunks of specified size with overlap.
    Returns a list of document chunks.
    """
    logger.info(f"Splitting documents into chunks (size={chunk_size}, overlap={chunk_overlap})...")
    
    # Initialize the text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    # Split the documents
    splits = text_splitter.split_documents(documents)
    
    # Preserve metadata during splitting
    for split in splits:
        # If this split came from a document with title/url/summary metadata, 
        # make sure it's still there
        if "title" in split.metadata:
            # Metadata is already preserved
            pass
        elif len(documents) > 0 and "title" in documents[0].metadata:
            # Copy metadata from original document if needed
            parent_doc = next((doc for doc in documents if doc.page_content in split.page_content), None)
            if parent_doc and "title" in parent_doc.metadata:
                split.metadata["title"] = parent_doc.metadata.get("title")
                split.metadata["url"] = parent_doc.metadata.get("url")
                split.metadata["summary"] = parent_doc.metadata.get("summary")
    
    logger.info(f"Created {len(splits)} document splits.")
    return splits

def create_index(document_splits: List[Document], output_dir: str = OUTPUT_DIR) -> None:
    """
    Create a FAISS index from the document splits and save it to the output directory.
    """
    logger.info("Creating FAISS index...")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Initialize embeddings model
        embeddings_model = os.getenv("EMBEDDINGS_MODEL", "text-embedding-3-small")
        logger.info(f"Using embedding model: {embeddings_model}")
        
        embeddings = OpenAIEmbeddings(
            model=embeddings_model
        )
        
        # Create and save the FAISS index
        start_time = time.time()
        
        # Generate embeddings and create the vector store
        vectorstore = FAISS.from_documents(
            document_splits, 
            embeddings
        )
        
        # Save the index locally
        vectorstore.save_local(output_dir)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Index created and saved to {output_dir} in {elapsed_time:.2f} seconds.")
        
    except Exception as e:
        logger.error(f"Error creating index: {e}")
        raise

def main():
    """Main function to build the RAG index."""
    try:
        # Load documents
        documents = load_documents()
        if not documents:
            logger.error("No documents found. Aborting.")
            return
        
        # Split documents
        document_splits = split_documents(documents)
        
        # Create and save the index
        create_index(document_splits)
        
        logger.info("RAG index built successfully!")
        
    except Exception as e:
        logger.error(f"Error building RAG index: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
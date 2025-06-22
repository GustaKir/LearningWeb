# Chains package initialization 

from backend.chains.rag_chain import RagChain

# Initialize the RAG chain as a singleton
rag_chain = None

def get_rag_chain():
    """Get the RAG chain instance (singleton)."""
    global rag_chain
    if rag_chain is None:
        rag_chain = RagChain()
    return rag_chain 
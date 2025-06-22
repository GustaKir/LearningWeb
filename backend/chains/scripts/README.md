# RAG Scripts

Este diretório contém scripts para construir e testar o sistema de RAG (Retrieval-Augmented Generation).

## Estrutura

- `build_rag.py`: Script para construir o índice FAISS a partir dos documentos no diretório `data/corpus`.
- `query_rag.py`: Script para testar o índice FAISS com consultas interativas.

## Como usar

### Construir o índice

Para construir o índice FAISS a partir dos documentos:

```bash
python -m backend.chains.scripts.build_rag
```

Isso processará todos os documentos no diretório `data/corpus`, os dividirá em chunks e criará um índice FAISS no diretório `data/index`.

### Testar o índice

Para testar o índice com consultas interativas:

```bash
python -m backend.chains.scripts.query_rag
```

Este script iniciará um prompt interativo onde você pode fazer perguntas sobre Python, FastAPI e Streamlit. As respostas serão geradas utilizando o índice FAISS para recuperar contexto relevante dos documentos.

## Integração com a API

O sistema de RAG é integrado com a API através do módulo `backend.chains.rag_chain`, que fornece uma classe `RagChain` para responder perguntas e recuperar contexto relevante dos documentos indexados. 
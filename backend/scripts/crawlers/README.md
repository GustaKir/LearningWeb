# Crawler Scripts

Este diretório contém scripts para coletar e processar documentação de várias fontes para construir o corpus do RAG.

## Estrutura

- `python_tutorial_crawler.py`: Script para coletar e processar a documentação do Python Tutorial.
- `crawl4AI_all.py`: Script para coletar e processar documentação de várias fontes (Streamlit, FastAPI) usando sitemaps.

## Como usar

### Coletar documentação do Python Tutorial

Para coletar a documentação do Python Tutorial:

```bash
python -m backend.scripts.crawlers.python_tutorial_crawler
```

Este script coletará as páginas do tutorial Python e salvará o conteúdo no diretório `data/corpus/docs.python.org/tutorial`.

### Coletar documentação de várias fontes

Para coletar a documentação de várias fontes usando sitemaps:

```bash
python -m backend.scripts.crawlers.crawl4AI_all
```

Este script coletará a documentação das fontes configuradas (Streamlit, FastAPI) usando seus respectivos sitemaps e salvará o conteúdo no diretório `data/corpus/[domain]`. 
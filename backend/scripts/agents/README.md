# Agent Scripts

Este diretório contém scripts relacionados a agentes de IA utilizados no projeto.

## Estrutura

- `agent_ai.py`: Um agente especializado em documentação Pydantic AI que utiliza RAG para responder perguntas.

## Como usar

Estes scripts são principalmente utilitários que podem ser importados e utilizados por outros componentes do sistema.

### Pydantic AI Expert

O agente Pydantic AI Expert está implementado no arquivo `agent_ai.py` e pode ser usado da seguinte maneira:

```python
from backend.scripts.agents.agent_ai import pydantic_ai_expert
from supabase import create_client
from openai import AsyncOpenAI

# Inicializar dependências
supabase = create_client(supabase_url, supabase_key)
openai_client = AsyncOpenAI(api_key=openai_api_key)

# Usar o agente
response = await pydantic_ai_expert.achat(
    "Como usar o RAG no Pydantic AI?",
    deps={"supabase": supabase, "openai_client": openai_client}
)
print(response)
``` 
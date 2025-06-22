import os
import time
from datetime import datetime
from typing import Dict, Any, Optional

import tiktoken
from openai import OpenAI
from sqlalchemy.orm import Session

from backend.models.logging import APILog

class OpenAIClient:
    """Cliente para interagir com a API da OpenAI com logging."""
    
    def __init__(self, db: Session = None):
        """Inicializa o cliente OpenAI.
        
        Args:
            db: Sessão do banco de dados para logging
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY não encontrada nas variáveis de ambiente")
        
        self.client = OpenAI(api_key=self.api_key)
        self.db = db
        self.model = os.getenv("CHAT_MODEL", "gpt-4.1-mini")
        
    def count_tokens(self, text: str) -> int:
        """Conta o número de tokens em um texto.
        
        Args:
            text: Texto para contar tokens
            
        Returns:
            Número de tokens
        """
        encoding = tiktoken.encoding_for_model(self.model)
        return len(encoding.encode(text))
    
    def chat_completion(
        self, 
        messages: list, 
        endpoint: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Envia uma solicitação para o endpoint de chat completion.
        
        Args:
            messages: Lista de mensagens no formato esperado pela API
            endpoint: Nome do endpoint para logging (chat, faq, quiz)
            temperature: Temperatura para a geração de texto
            max_tokens: Número máximo de tokens na resposta
            
        Returns:
            Resposta da API
        """
        start_time = time.time()
        
        # Calcular tokens no prompt
        prompt_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        tokens_prompt = self.count_tokens(prompt_text)
        
        # Chamar a API
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Extrair texto da resposta
            response_text = response.choices[0].message.content
            
            # Calcular tokens na resposta
            tokens_completion = response.usage.completion_tokens
            tokens_total = response.usage.total_tokens
            
            # Calcular duração
            duration_ms = (time.time() - start_time) * 1000
            
            # Logging no banco de dados
            if self.db:
                log = APILog(
                    endpoint=endpoint,
                    prompt=prompt_text,
                    response=response_text,
                    tokens_prompt=tokens_prompt,
                    tokens_completion=tokens_completion,
                    tokens_total=tokens_total,
                    model=self.model,
                    duration_ms=duration_ms
                )
                self.db.add(log)
                self.db.commit()
            
            return {
                "text": response_text,
                "tokens_prompt": tokens_prompt,
                "tokens_completion": tokens_completion,
                "tokens_total": tokens_total,
                "duration_ms": duration_ms
            }
            
        except Exception as e:
            # Log de erro também
            if self.db:
                log = APILog(
                    endpoint=endpoint,
                    prompt=prompt_text,
                    response=str(e),
                    tokens_prompt=tokens_prompt,
                    tokens_completion=0,
                    tokens_total=tokens_prompt,
                    model=self.model,
                    duration_ms=(time.time() - start_time) * 1000
                )
                self.db.add(log)
                self.db.commit()
            
            raise e 
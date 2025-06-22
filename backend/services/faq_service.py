from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.models.faq import FAQEntry
from backend.utils.openai_client import OpenAIClient
from backend.services.rag_agent_service import RagAgentService

class FAQService:
    """Serviço para gerenciar entradas de FAQ."""
    
    def __init__(self, db: Session):
        """Inicializa o serviço de FAQ.
        
        Args:
            db: Sessão do banco de dados
        """
        self.db = db
        self.openai_client = OpenAIClient(db)
        self.rag_agent = RagAgentService(db)
    
    def get_all_entries(self, category: Optional[str] = None) -> List[FAQEntry]:
        """Obtém todas as entradas de FAQ.
        
        Args:
            category: Filtro opcional por categoria
            
        Returns:
            Lista de entradas de FAQ
        """
        query = self.db.query(FAQEntry).filter(FAQEntry.is_published == True)
        
        if category:
            query = query.filter(FAQEntry.category == category)
        
        return query.order_by(FAQEntry.created_at.desc()).all()
    
    def get_entry(self, entry_id: int) -> Optional[FAQEntry]:
        """Obtém uma entrada de FAQ pelo ID.
        
        Args:
            entry_id: ID da entrada
            
        Returns:
            Entrada de FAQ ou None se não existir
        """
        return self.db.query(FAQEntry).filter(FAQEntry.id == entry_id).first()
    
    def create_entry(self, question: str, answer: str, source: Optional[str] = None, category: Optional[str] = None) -> FAQEntry:
        """Cria uma nova entrada de FAQ.
        
        Args:
            question: Pergunta
            answer: Resposta
            source: Fonte da documentação
            category: Categoria (Python, FastAPI, Streamlit)
            
        Returns:
            Entrada de FAQ criada
        """
        entry = FAQEntry(
            question=question,
            answer=answer,
            source=source,
            category=category
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry
    
    def update_entry(self, entry_id: int, question: Optional[str] = None, answer: Optional[str] = None, 
                    source: Optional[str] = None, category: Optional[str] = None, 
                    is_published: Optional[bool] = None) -> Optional[FAQEntry]:
        """Atualiza uma entrada de FAQ.
        
        Args:
            entry_id: ID da entrada
            question: Nova pergunta
            answer: Nova resposta
            source: Nova fonte
            category: Nova categoria
            is_published: Novo status de publicação
            
        Returns:
            Entrada atualizada ou None se não existir
        """
        entry = self.get_entry(entry_id)
        if not entry:
            return None
        
        if question is not None:
            entry.question = question
        if answer is not None:
            entry.answer = answer
        if source is not None:
            entry.source = source
        if category is not None:
            entry.category = category
        if is_published is not None:
            entry.is_published = is_published
        
        self.db.commit()
        self.db.refresh(entry)
        return entry
    
    def delete_entry(self, entry_id: int) -> bool:
        """Remove uma entrada de FAQ.
        
        Args:
            entry_id: ID da entrada
            
        Returns:
            True se removido com sucesso, False caso contrário
        """
        entry = self.get_entry(entry_id)
        if not entry:
            return False
        
        self.db.delete(entry)
        self.db.commit()
        return True
    
    def generate_faq_from_emails(self, emails: List[str], num_entries: int = 5) -> List[FAQEntry]:
        """Gera entradas de FAQ a partir de emails de suporte.
        
        Args:
            emails: Lista de emails com dúvidas
            num_entries: Número de entradas a serem geradas
            
        Returns:
            Lista de entradas de FAQ geradas
        """
        # Extrair tópicos principais dos emails
        topics = self._extract_topics_from_emails(emails, num_entries)
        
        # Criar entradas no banco de dados
        created_entries = []
        
        for topic in topics:
            # Obter contexto relevante da documentação
            context = self.rag_agent.get_context_for_faq(topic)
            
            # Gerar resposta com RAG
            question, answer, category, source = self._generate_faq_entry(topic, context)
            
            # Criar entrada
            if question and answer:
                entry = self.create_entry(question, answer, source, category)
                created_entries.append(entry)
        
        return created_entries
    
    def _extract_topics_from_emails(self, emails: List[str], num_topics: int) -> List[str]:
        """Extrai tópicos principais dos emails.
        
        Args:
            emails: Lista de emails
            num_topics: Número de tópicos a extrair
            
        Returns:
            Lista de tópicos extraídos
        """
        # Preparar o prompt para a API
        prompt = f"""
        Analise os seguintes emails de suporte e extraia os {num_topics} tópicos/dúvidas mais comuns e relevantes.
        Formate cada tópico como uma pergunta clara e concisa.
        
        Emails:
        {"\n".join(emails)}
        
        Responda APENAS com a lista numerada de perguntas, uma por linha:
        1. [Pergunta 1]
        2. [Pergunta 2]
        ...
        """
        
        # Enviar para a API
        response = self.openai_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            endpoint="faq_topics",
            temperature=0.2
        )
        
        # Processar a resposta
        topics_text = response["text"]
        
        # Extrair tópicos
        topics = []
        for line in topics_text.strip().split("\n"):
            if not line.strip():
                continue
                
            # Remover numeração e espaços extras
            parts = line.strip().split(".", 1)
            if len(parts) > 1 and parts[0].isdigit():
                topic = parts[1].strip()
                topics.append(topic)
            else:
                topics.append(line.strip())
        
        return topics[:num_topics]  # Garantir que não exceda o número solicitado
    
    def _generate_faq_entry(self, topic: str, context: List[Dict[str, str]]) -> tuple:
        """Gera uma entrada de FAQ para um tópico com contexto.
        
        Args:
            topic: Tópico/pergunta
            context: Lista de documentos de contexto
            
        Returns:
            Tupla (pergunta, resposta, categoria, fonte)
        """
        # Formatar o contexto
        context_text = "\n\n".join([f"Documento {i+1}:\nConteúdo: {doc['content']}\nFonte: {doc['source']}" 
                                for i, doc in enumerate(context)])
        
        # Preparar o prompt para a API
        prompt = f"""
        Com base no seguinte tópico e contexto da documentação, crie uma entrada de FAQ completa.
        
        Tópico: {topic}
        
        Contexto da documentação:
        {context_text if context else "Sem contexto disponível. Use seu conhecimento sobre Python, FastAPI e Streamlit."}
        
        Forneça:
        1. A pergunta reformulada de maneira clara e útil
        2. Uma resposta completa e precisa baseada estritamente na documentação fornecida
        3. A categoria (Python, FastAPI ou Streamlit)
        4. A fonte específica da documentação
        
        Responda NO FORMATO EXATO:
        PERGUNTA: [Pergunta reformulada]
        RESPOSTA: [Resposta completa]
        CATEGORIA: [Python/FastAPI/Streamlit]
        FONTE: [Fonte específica]
        """
        
        # Enviar para a API
        response = self.openai_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            endpoint="faq_entry",
            temperature=0.3
        )
        
        # Processar a resposta
        faq_text = response["text"]
        
        # Extrair campos
        question = ""
        answer = ""
        category = ""
        source = ""
        
        for line in faq_text.strip().split("\n"):
            line = line.strip()
            if line.startswith("PERGUNTA:"):
                question = line[len("PERGUNTA:"):].strip()
            elif line.startswith("RESPOSTA:"):
                answer = line[len("RESPOSTA:"):].strip()
            elif line.startswith("CATEGORIA:"):
                category = line[len("CATEGORIA:"):].strip()
            elif line.startswith("FONTE:"):
                source = line[len("FONTE:"):].strip()
        
        return question, answer, category, source 
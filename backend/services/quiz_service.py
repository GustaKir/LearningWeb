from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.models.quiz import Quiz, QuizQuestion, QuizAlternative
from backend.utils.openai_client import OpenAIClient
from backend.services.new_rag_service import NewRagService

class QuizService:
    """Serviço para gerenciar quizzes."""
    
    def __init__(self, db: Session):
        """Inicializa o serviço de quiz.
        
        Args:
            db: Sessão do banco de dados
        """
        self.db = db
        self.openai_client = OpenAIClient(db)
        self.rag_agent = NewRagService(db)
    
    def get_all_quizzes(self) -> List[Quiz]:
        """Obtém todos os quizzes.
        
        Returns:
            Lista de quizzes
        """
        return self.db.query(Quiz).order_by(Quiz.created_at.desc()).all()
    
    def get_quiz(self, quiz_id: int) -> Optional[Quiz]:
        """Obtém um quiz pelo ID.
        
        Args:
            quiz_id: ID do quiz
            
        Returns:
            Quiz ou None se não existir
        """
        return self.db.query(Quiz).filter(Quiz.id == quiz_id).first()
    
    def create_quiz(self, title: str, topic: str) -> Quiz:
        """Cria um novo quiz.
        
        Args:
            title: Título do quiz
            topic: Tópico do quiz
            
        Returns:
            Quiz criado
        """
        quiz = Quiz(
            title=title,
            topic=topic
        )
        self.db.add(quiz)
        self.db.commit()
        self.db.refresh(quiz)
        return quiz
    
    def add_question(self, quiz_id: int, question_text: str, explanation: Optional[str] = None) -> Optional[QuizQuestion]:
        """Adiciona uma pergunta a um quiz.
        
        Args:
            quiz_id: ID do quiz
            question_text: Texto da pergunta
            explanation: Explicação da resposta correta
            
        Returns:
            Pergunta criada ou None se o quiz não existir
        """
        quiz = self.get_quiz(quiz_id)
        if not quiz:
            return None
        
        question = QuizQuestion(
            quiz_id=quiz.id,
            question_text=question_text,
            explanation=explanation
        )
        self.db.add(question)
        self.db.commit()
        self.db.refresh(question)
        return question
    
    def add_alternative(self, question_id: int, text: str, is_correct: bool, explanation: Optional[str] = None) -> Optional[QuizAlternative]:
        """Adiciona uma alternativa a uma pergunta.
        
        Args:
            question_id: ID da pergunta
            text: Texto da alternativa
            is_correct: Se é a alternativa correta
            explanation: Explicação do porquê essa alternativa está correta ou incorreta
            
        Returns:
            Alternativa criada ou None se a pergunta não existir
        """
        question = self.db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
        if not question:
            return None
        
        alternative = QuizAlternative(
            question_id=question.id,
            text=text,
            is_correct=is_correct,
            explanation=explanation
        )
        self.db.add(alternative)
        self.db.commit()
        self.db.refresh(alternative)
        return alternative
    
    def delete_quiz(self, quiz_id: int) -> bool:
        """Remove um quiz.
        
        Args:
            quiz_id: ID do quiz
            
        Returns:
            True se removido com sucesso, False caso contrário
        """
        quiz = self.get_quiz(quiz_id)
        if not quiz:
            return False
        
        self.db.delete(quiz)
        self.db.commit()
        return True
    
    def check_answer(self, alternative_id: int) -> Dict[str, Any]:
        """Verifica se uma alternativa está correta.
        
        Args:
            alternative_id: ID da alternativa
            
        Returns:
            Dicionário com o resultado e explicação
        """
        alternative = self.db.query(QuizAlternative).filter(QuizAlternative.id == alternative_id).first()
        if not alternative:
            return {"is_correct": False, "explanation": "Alternativa não encontrada."}
        
        return {
            "is_correct": alternative.is_correct,
            "explanation": alternative.explanation
        }
    
    async def generate_quiz(self, topic: str, num_questions: int = 5, num_alternatives: int = 4) -> Optional[Quiz]:
        """Gera um quiz sobre um tópico específico.
        
        Args:
            topic: Tópico do quiz
            num_questions: Número de perguntas
            num_alternatives: Número de alternativas por pergunta
            
        Returns:
            Quiz gerado ou None em caso de erro
        """
        try:
        # Obter contexto relevante da documentação
            # Fazemos múltiplas consultas com diferentes aspectos do tópico para diversificar as fontes
            context = []
            
            # Primeiro, obtemos o contexto com o tópico original
            main_context = await self.rag_agent.get_relevant_context(topic)
            if main_context:
                context.extend(main_context)
            
            # Depois, tentamos obter mais contexto com variações do tópico
            # Isso ajuda a diversificar as fontes
            related_topics = [
                f"{topic} exemplos",
                f"{topic} conceitos",
                f"{topic} avançado",
                f"{topic} tutorial"
            ]
            
            for related_topic in related_topics:
                try:
                    additional_context = await self.rag_agent.get_relevant_context(related_topic)
                    if additional_context:
                        context.extend(additional_context)
                except Exception as e:
                    print(f"Erro ao buscar contexto adicional para '{related_topic}': {str(e)}")
            
            # Selecionar documentos com origens diferentes para ter maior diversidade
            diverse_context = []
            sources = set()
            
            # Primeiro passo: filtrar para incluir apenas fontes locais (não URLs da internet)
            filtered_context = []
            for doc in context:
                source = doc['source']
                # Verificar se a fonte é uma URL da internet (começa com http:// ou https://)
                import re
                if not re.match(r'^https?://', source):
                    # Esta é uma fonte local, então a incluímos
                    filtered_context.append(doc)
                else:
                    print(f"Excluindo fonte externa: {source}")
            
            # Se não encontramos fontes locais, mantemos todas as fontes para não ficar sem contexto
            if not filtered_context and context:
                print("Nenhuma fonte local encontrada, usando todas as fontes disponíveis")
                filtered_context = context
            
            # Agora coletamos fontes únicas do contexto filtrado
            for doc in filtered_context:
                source = doc['source']
                # Extrair identificador único da fonte (nome do arquivo/caminho)
                if source not in sources:
                    sources.add(source)
                    diverse_context.append(doc)
            
            # Se ainda não temos pelo menos 3 documentos, adicionar mais do contexto filtrado
            for doc in filtered_context:
                if len(diverse_context) >= 5:  # limitar a 5 documentos para não sobrecarregar o prompt
                    break
                if doc not in diverse_context:
                    diverse_context.append(doc)
        
            # Formatar o contexto
            context_text = ""
            if diverse_context:
                context_text = "Contexto da documentação (use TODAS as fontes abaixo distribuídas de forma equilibrada):\n\n"
                for i, doc in enumerate(diverse_context):
                    source_url = doc['source']
                    context_text += f"Documento {i+1} - Fonte: {source_url}\nConteúdo: {doc['content']}\n\n"
            
            # Preparar o prompt para a API
            prompt = f"""
            Crie um quiz de múltipla escolha sobre "{topic}" com {num_questions} perguntas, baseado EXCLUSIVAMENTE no seguinte contexto da documentação.
            
            {context_text if diverse_context else "Não temos contexto suficiente para este tópico, por favor informe ao usuário que não há informações disponíveis no sistema RAG."}
            
            IMPORTANTE: 
            1. As perguntas DEVEM ser baseadas EXCLUSIVAMENTE nas informações fornecidas no contexto acima.
            2. DISTRIBUA EQUILIBRADAMENTE AS PERGUNTAS entre os diferentes documentos - use múltiplas fontes.
            3. Cada documento deve ser usado para pelo menos uma pergunta, para garantir diversidade de conteúdo.
            4. Evite criar perguntas muito semelhantes ou repetitivas.
            5. Para cada pergunta e explicação, SEMPRE cite a fonte COMPLETA usando o URL exato fornecido no documento (ex: "https://docs.streamlit.io/deploy/snowflake").
            
            Cada pergunta deve ter {num_alternatives} alternativas, sendo apenas uma correta.
            
            Para cada pergunta, forneça:
            1. O texto da pergunta
            2. Uma explicação geral sobre a resposta correta, SEMPRE citando o URL completo da fonte (ex: "Conforme explicado em https://docs.python.org/3/tutorial/...")
            3. As alternativas, indicando qual é a correta
            4. Uma explicação para cada alternativa, incluindo o URL da fonte quando relevante
            
            Responda no formato:
            PERGUNTA: [Texto da pergunta]
            EXPLICAÇÃO GERAL: [Explicação sobre a resposta correta, incluindo SEMPRE o URL completo da fonte]
            ALTERNATIVAS:
            A. [Texto da alternativa] [CORRETA se for a correta]
            EXPLICAÇÃO A: [Explicação sobre esta alternativa, incluindo o URL da fonte quando relevante]
            B. [Texto da alternativa] [CORRETA se for a correta]
            EXPLICAÇÃO B: [Explicação sobre esta alternativa, incluindo o URL da fonte quando relevante]
            ...
            ---
            """
        
            # Enviar para a API (sem await, porque não é uma função assíncrona)
            response = self.openai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                endpoint="quiz",
                temperature=0.7
            )
        
            # Debug log
            print(f"API Response: {response}")
        
            # Criar o quiz no banco de dados
            quiz = self.create_quiz(
                title=f"Quiz sobre {topic}",
                topic=topic
            )
            
            # Processar a resposta e criar as questões
            questions_text = response['text'].split('---')
            
            print(f"Found {len(questions_text)} question blocks")
            
            # Contador para verificar se perguntas estão sendo criadas
            questions_created = 0
            
            for question_text in questions_text:
                if not question_text.strip():
                    continue
                
                print(f"Processing question: {question_text[:100]}...")
                    
                # Extrair informações da questão
                lines = question_text.strip().split('\n')
                question = None
                explanation = None
                alternatives = []
                current_alternative = None
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Match both "PERGUNTA:" and "### PERGUNTA X:" formats
                    if line.startswith('PERGUNTA:') or ('PERGUNTA' in line and ':' in line):
                        # Remove any ### prefix and question numbers
                        clean_line = line.replace('###', '').strip()
                        if 'PERGUNTA' in clean_line:
                            parts = clean_line.split(':', 1)
                            if len(parts) > 1:
                                # Extract just the question text after the colon
                                question = parts[1].strip()
                                print(f"Found question: {question[:50]}...")
                    
                    # Match both "EXPLICAÇÃO GERAL:" and other explanation formats
                    elif line.startswith('EXPLICAÇÃO GERAL:') or ('EXPLICAÇÃO GERAL' in line and ':' in line):
                        parts = line.split(':', 1)
                        if len(parts) > 1:
                            explanation = parts[1].strip()
                    
                    # Match alternative formats with letter and dot
                    elif any(line.startswith(f"{letter}.") for letter in ['A', 'B', 'C', 'D', 'E']):
                        # If we already have a current alternative, save it before starting a new one
                        if current_alternative:
                            alternatives.append(current_alternative)
                            
                        # Extract the letter
                        letter = line[0]
                        # Extract the text after the dot
                        text = line[2:].strip()
                        is_correct = '[CORRETA]' in text
                        text = text.replace('[CORRETA]', '').strip()
                        current_alternative = {'text': text, 'is_correct': is_correct, 'explanation': ''}
                        print(f"Found alternative {letter}: {text[:30]}... (correct: {is_correct})")
                    
                    # Match explanation for alternatives
                    elif (line.startswith('EXPLICAÇÃO') and current_alternative) or \
                         (line.startswith('EXPLICAÇÃO ') and any(line.startswith(f'EXPLICAÇÃO {letter}:') for letter in ['A', 'B', 'C', 'D', 'E'])):
                        parts = line.split(':', 1)
                        if len(parts) > 1 and current_alternative:
                            current_alternative['explanation'] = parts[1].strip()
                            # Don't add to alternatives yet, wait for the next alternative or end of question
                        
                # If we still have an unprocessed alternative at the end
                if current_alternative:
                    alternatives.append(current_alternative)
                
                if question and alternatives:
                    print(f"Creating question with {len(alternatives)} alternatives")
                    # Criar a questão
                    quiz_question = self.add_question(
                        quiz_id=quiz.id,
                        question_text=question,
                        explanation=explanation
                    )
                    
                    # Criar as alternativas
                    for alt in alternatives:
                        self.add_alternative(
                            question_id=quiz_question.id,
                            text=alt['text'],
                            is_correct=alt['is_correct'],
                            explanation=alt.get('explanation', '')
                        )
                    
                    questions_created += 1
            
            print(f"Total questions created: {questions_created}")
            
            # Se nenhuma pergunta foi criada, é possível que o formato da resposta esteja errado
            # Vamos tentar processar de forma mais simples
            if questions_created == 0:
                print("No questions created, trying fallback parsing")
                # Processamento de fallback
                import re
                
                # Extrair perguntas com regex que captura tanto "PERGUNTA:" quanto "### PERGUNTA X:"
                questions = re.findall(r'(?:###\s*)?PERGUNTA[^:]*:\s*([^\n]+)', response['text'])
                explanations = re.findall(r'EXPLICAÇÃO GERAL[^:]*:\s*([^\n]+)', response['text'])
                
                print(f"Fallback found {len(questions)} questions")
                
                # Para cada pergunta encontrada, criar uma entrada básica
                for i, q_text in enumerate(questions):
                    explanation = explanations[i] if i < len(explanations) else ""
                    
                    print(f"Creating fallback question: {q_text[:50]}...")
                    
                    # Criar uma questão básica
                    question = self.add_question(
                        quiz_id=quiz.id,
                        question_text=q_text.strip(),
                        explanation=explanation.strip()
                    )
                    
                    # Usar regex para encontrar alternativas para esta pergunta
                    # Tentativa de extrair alternativas para a pergunta atual
                    # Encontrar o bloco de texto entre esta pergunta e a próxima ou o fim
                    start_idx = response['text'].find(q_text)
                    if start_idx > 0:
                        # Encontrar a próxima pergunta ou o fim do texto
                        next_q_idx = response['text'].find("PERGUNTA", start_idx + len(q_text))
                        if next_q_idx == -1:
                            next_q_idx = len(response['text'])
                        
                        question_block = response['text'][start_idx:next_q_idx]
                        
                        # Extrair alternativas com letras
                        all_alternatives = []
                        alt_matches = re.findall(r'([A-E])\.\s*([^[\n]+)(?:\s*\[CORRETA\])?', question_block)
                        
                        if alt_matches:
                            print(f"Found {len(alt_matches)} alternatives for fallback question")
                            # Process all alternatives first
                            for j, (letter, alt_text) in enumerate(alt_matches):
                                is_correct = "[CORRETA]" in question_block[question_block.find(f"{letter}."):]
                                clean_text = alt_text.strip().replace("[CORRETA]", "").strip()
                                
                                # Tentar encontrar explicação para esta alternativa
                                exp_pattern = f"EXPLICAÇÃO {letter}:[\\s]*([^\\n]+)"
                                exp_matches = re.findall(exp_pattern, question_block)
                                exp_text = exp_matches[0] if exp_matches else "Sem explicação disponível"
                                
                                all_alternatives.append({
                                    'letter': letter,
                                    'text': clean_text,
                                    'is_correct': is_correct,
                                    'explanation': exp_text.strip()
                                })
                            
                            # Now create all alternatives at once
                            for alt in all_alternatives:
                                self.add_alternative(
                                    question_id=question.id,
                                    text=alt['text'],
                                    is_correct=alt['is_correct'],
                                    explanation=alt['explanation']
                                )
                            
                            # Se não identificamos nenhuma alternativa correta, marcar a primeira como correta
                            if not any(alt['is_correct'] for alt in all_alternatives) and all_alternatives:
                                # Atualizar a primeira alternativa como correta
                                first_alt = self.db.query(QuizAlternative).filter(
                                    QuizAlternative.question_id == question.id
                                ).first()
                                
                                if first_alt:
                                    first_alt.is_correct = True
                                    self.db.commit()
                        else:
                            # Se não encontrou alternativas, criar algumas genéricas
                            print("No alternatives found, creating generic ones")
                            self.add_alternative(
                                question_id=question.id,
                                text="Alternativa correta",
                                is_correct=True,
                                explanation="Esta é a resposta correta."
                            )
                            
                            for j in range(3):
                                self.add_alternative(
                                    question_id=question.id,
                                    text=f"Alternativa incorreta {j+1}",
                                    is_correct=False,
                                    explanation="Esta alternativa está incorreta."
                                )
                    
                    questions_created += 1
                
                print(f"Created {questions_created} questions with fallback method")
            
            # Atualizar o quiz do banco para ter certeza que está com as perguntas
            self.db.refresh(quiz)
        
            return quiz 
            
        except Exception as e:
            print(f"Erro ao gerar quiz: {str(e)}")
            import traceback
            traceback.print_exc()
            return None 
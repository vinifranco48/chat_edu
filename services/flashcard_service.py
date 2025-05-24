from groq import Groq, APIError
import json
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import settings
from services.vector_store_service import VectorStoreService

load_dotenv()
class FlashcardService:

    def __init__(self, vector_size=1536, api_key: Optional[str] = None):
        self.vector_store = VectorStoreService(vector_size)
        self.client = Groq(api_key=api_key) if api_key else None
        
    def get_course_content(self, id_course: str) -> List[Dict[str, Any]]:
        """ Gerar flashcards a partir dos embeddings gerados a partir do id do curso """ 
        try:
            course_content = self.vector_store.get_all_by_course_id(id_course)
            return course_content
        except Exception as e:
            print(f"Erro ao recuperar conteúdo do curso: {id_course} {e}")
            return []

    def chunk_content(self, course_content: List[Dict[str, Any]], max_chunks: int = 3) -> List[List[Dict[str, Any]]]:
        """Divide o conteúdo do curso em chunks menores para não exceder os limites de token"""
        if not course_content:
            return []
            
        chunk_size = max(1, len(course_content) // max_chunks)
        return [course_content[i:i + chunk_size] for i in range(0, len(course_content), chunk_size)]
    
    def generate_prompt(self, chunk_content: List[Dict[str, Any]], num_flashcards: int = 3) -> str:
        """ Gera um prompt para o modelo de linguagem baseado em um chunk do conteúdo do curso """
        texts = [doc['text'] for doc in chunk_content]
        # Limitando o texto para reduzir o tamanho do prompt
        combined_text = " ".join(texts)
        # Limitar a ~2000 caracteres para manter o prompt pequeno
        if len(combined_text) > 2000:
            combined_text = combined_text[:2000] + "..."
            
        prompt = f"""
                    Você é um educador especializado em criar flashcards eficazes para aprendizado. Baseado no conteúdo abaixo, crie {num_flashcards} flashcards no formato pergunta e resposta.

                    Regras MUITO IMPORTANTES para os flashcards:
                    1. Cada flashcard deve focar em conceitos gerais, definições ou princípios universais da matéria
                    2. Evite COMPLETAMENTE criar flashcards sobre exemplos específicos, exercícios numéricos ou problemas particulares
                    3. As perguntas devem ser autocontidas e compreensíveis sem necessidade de contexto adicional
                    4. As respostas devem ser completas mas sucintas (máximo 3 frases)
                    5. NÃO use referências como "no exemplo 1", "no problema X" ou "na questão Y"
                    6. Foque em conhecimento conceitual que seja útil e compreensível por si só
                    7. Priorize definições, metodologias, teorias e conceitos fundamentais da disciplina
                    8. Se o conteúdo for muito específico sobre exercícios, extraia apenas o conhecimento geral aplicável
                    9. NUNCA mencione variáveis específicas de problemas (como A, B, x, y) a menos que sejam convenções universais da área
                    10. Certifique-se que cada flashcard seria compreensível para alguém que não tenha acesso ao material original e traga de forma aprofundada e tecnica

                    CONTEÚDO DO CURSO:
                    {combined_text}

                    Responda APENAS com um array JSON contendo os flashcards, seguindo exatamente este formato:
                    [
                    {{
                        "pergunta": "Pergunta do flashcard 1?",
                        "resposta": "Resposta do flashcard 1."
                    }},
                    ...
                    ]

                    Não inclua nenhum texto adicional antes ou depois do JSON.
                    """
        return prompt

    def create_flashcards(self, id_course: str, model: str) -> List[Dict[str, Any]]:
        """ Cria flashcards a partir do conteudo do curso"""

        if not self.client:
            raise ValueError("API key não fornecida para o cliente Groq.")
        
        course_content = self.get_course_content(id_course)
        if not course_content:
            print(f"Nenhum conteúdo encontrado para o curso: {id_course}")
            return []
            
        all_flashcards = []
        # Dividir o conteúdo em chunks menores
        content_chunks = self.chunk_content(course_content)
        flashcards_per_chunk = max(1, 10 // len(content_chunks))
        
        print(f"Processando {len(content_chunks)} chunks de conteúdo...")
        
        for i, chunk in enumerate(content_chunks):
            try:
                print(f"Processando chunk {i+1}/{len(content_chunks)} com {len(chunk)} documentos...")
                prompt = self.generate_prompt(chunk, num_flashcards=flashcards_per_chunk)
                
                # Configurando limites de token explícitos para evitar exceder limites
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "Você é um assistente educacional especializado em criar flashcards eficazes para estudo."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.5,
                    max_tokens=2000  
                )
                response_text = response.choices[0].message.content

                json_text = response_text.strip()
                if json_text.startswith("```json"):
                    json_text = json_text.replace("```json", "").replace("```", "")

                chunk_flashcards = json.loads(json_text)
                all_flashcards.extend(chunk_flashcards)
                
                # Pequena pausa para não exceder limites de taxa
                import time
                time.sleep(1)
                
            except APIError as e:
                print(f"Erro na API do modelo para chunk {i+1}: {e}")
                continue  
            except json.JSONDecodeError as e:
                print(f"Erro ao decodificar resposta JSON para chunk {i+1}: {e}")
                print(f"Resposta original: {response_text}")
                continue
            except Exception as e:
                print(f"Erro inesperado ao gerar flashcards para chunk {i+1}: {e}")
                continue
        
        return all_flashcards
    
if __name__ == "__main__": 
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("AVISO: GROQ_API_KEY não encontrada no ambiente.")
    
    flashcard_service = FlashcardService(vector_size=1536, api_key=api_key)
    course_id = "4629"
    
    try:
        flashcards = flashcard_service.create_flashcards(course_id, model=settings.llm_model_name)
        if flashcards:
            print(f"{len(flashcards)} flashcards gerados com sucesso:")
            for i, card in enumerate(flashcards, 1):
                print(f"\nFlashcard {i}:")
                print(f"P: {card['pergunta']}")
                print(f"R: {card['resposta']}")
        else:
            print("Nenhum flashcard foi gerado.")
    except Exception as e:
        print(f"Erro ao executar o serviço de flashcards: {e}")


                                                        


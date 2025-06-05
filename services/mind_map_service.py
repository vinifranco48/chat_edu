# services/mind_map_service.py
from groq import Groq, APIError
import json
from typing import Dict, Any, Optional, List
import os
import time
import traceback 

class MindMapService:
    def __init__(self, vector_store_service, api_key: Optional[str] = None):
        self.vector_store = vector_store_service 
        self.client = Groq(api_key=api_key) if api_key else None

    def get_course_content(self, id_course: str) -> List[Dict[str, Any]]:
        """Recupera o conteúdo do curso do vector store."""
        try:
            print(f"[MindMapService DEBUG] Buscando conteúdo para o curso: {id_course}")
            course_content = self.vector_store.get_all_by_course_id(id_course)
            print(f"[MindMapService DEBUG] Encontrados {len(course_content)} documentos para o curso {id_course}")
            
            # Log dos primeiros documentos para debug
            # if course_content:
            #     for i, doc in enumerate(course_content[:2]): # Log apenas 2 para não poluir muito
            #         print(f"[MindMapService DEBUG] Doc {i} (preview): {str(doc)[:150]}...")
            return course_content
        except Exception as e:
            print(f"[MindMapService ERROR] Erro ao recuperar conteúdo do curso {id_course}: {e}")
            traceback.print_exc()
            return []

    def chunk_content_for_mindmap(self, course_content: List[Dict[str, Any]], max_text_length: int = 8000) -> List[str]:
        """Agrupa o conteúdo do curso em um único texto (ou chunks) para o mapa mental."""
        if not course_content:
            print("[MindMapService DEBUG] Nenhum conteúdo de curso fornecido para chunking")
            return []

        texts = []
        for doc in course_content:
            text_content = ""
            if isinstance(doc, dict):
                text_content = doc.get('text', '') or doc.get('content', '') or doc.get('page_content', '')
            elif hasattr(doc, 'page_content'):
                text_content = doc.page_content
            elif isinstance(doc, str):
                text_content = doc
            
            if text_content and text_content.strip():
                texts.append(text_content.strip())

        print(f"[MindMapService DEBUG] Extraídos {len(texts)} textos válidos dos documentos.")
        if not texts:
            print("[MindMapService WARNING] Nenhum texto válido extraído dos documentos.")
            return []

        combined_text = " ".join(texts)
        print(f"[MindMapService DEBUG] Texto combinado tem {len(combined_text)} caracteres.")

        if len(combined_text) > max_text_length:
            print(f"[MindMapService WARNING] Texto truncado de {len(combined_text)} para {max_text_length} caracteres.")
            return [combined_text[:max_text_length] + "..."]
        
        return [combined_text] if combined_text.strip() else []

    def generate_mind_map_prompt(self, course_name: str, text_content: str, max_main_topics: int = 5, max_sub_topics: int = 3) -> str:
        """Gera um prompt otimizado para criar mapas mentais com descrições."""
        prompt = f"""Você é um especialista em estruturação de conhecimento educacional e criação de mapas mentais.
Baseado no conteúdo do curso "{course_name}" fornecido abaixo, crie um mapa mental estruturado.

CONTEÚDO DO CURSO (resumo ou trechos principais):
{text_content}

INSTRUÇÕES DETALHADAS PARA O MAPA MENTAL:
1.  NÓ RAIZ: Deve representar o tema central do curso.
    - Use o ID "root".
    - Use o type "input".
    - O "label" deve ser "{course_name}".
    - Inclua uma "description" concisa, resumindo o curso em 1-2 frases.
2.  TÓPICOS PRINCIPAIS: Identifique de {max_main_topics-1} a {max_main_topics} tópicos principais (pilares do curso).
    - IDs no formato "topic-1", "topic-2", etc.
    - Para cada um, um "label" claro e uma "description" breve (1-2 frases).
3.  SUB-TÓPICOS: Para cada TÓPICO PRINCIPAL, identifique de {max_sub_topics-1} a {max_sub_topics} sub-conceitos ou detalhes importantes.
    - IDs no formato "subtopic-1-1" (para o primeiro sub-tópico do topic-1), "subtopic-1-2", etc.
    - Para cada um, um "label" e uma "description" ainda mais curta (1 frase idealmente).
4.  QUALIDADE DOS RÓTULOS (label): Devem ser concisos, informativos (idealmente de 1 a 5 palavras).
5.  QUALIDADE DAS DESCRIÇÕES (description): Devem ser BREVES (máximo 2-3 frases curtas para tópicos principais, 1-2 frases para sub-tópicos), conceituais e agregar valor. Evite redundância com o rótulo.
6.  FOCO: Concentre-se em conceitos, teorias, definições fundamentais e relações importantes. Evite exemplos numéricos, referências a exercícios específicos ou detalhes excessivamente granulares que não se encaixam bem em um mapa conceitual.
7.  ARESTAS (edges): Crie arestas para conectar o nó raiz aos tópicos principais, e os tópicos principais aos seus respectivos sub-tópicos. Use IDs de arestas como "edge-root-topic-1", "edge-topic-1-subtopic-1-1".

FORMATO DE SAÍDA ESTRITAMENTE JSON:
Responda APENAS com um objeto JSON contendo duas chaves principais: "nodes" e "edges".
- "nodes": Um array de objetos nó. Cada nó DEVE ter:
    - "id": Uma string ÚNICA.
    - "data": Um objeto contendo:
        - "label": Uma string (o texto do rótulo).
        - "description": Uma string (a breve explicação).
    - "type" (opcional): "input" para o nó raiz. Para os demais, pode omitir (será 'default' no React Flow).
- "edges": Um array de objetos aresta. Cada aresta DEVE ter:
    - "id": Uma string ÚNICA.
    - "source": O "id" do nó de origem.
    - "target": O "id" do nó de destino.
    - "animated" (opcional): `true` ou `false`.

EXEMPLO DE ESTRUTURA DE UM NÓ EM "nodes":
{{
    "id": "topic-1",
    "data": {{
        "label": "Conceito Chave A",
        "description": "Explicação concisa do Conceito Chave A."
    }}
}}

Não inclua nenhum texto, explicação, comentários ou formatação de markdown (como ```json) antes ou depois do objeto JSON. A resposta deve ser diretamente o JSON.
"""
        return prompt

    def create_mind_map_structure(self, id_course: str, course_name: str, model: str) -> Dict[str, List[Dict[str, Any]]]:
        """Cria a estrutura do mapa mental (nós e arestas) a partir do conteúdo do curso."""
        print(f"[MindMapService INFO] Iniciando criação de mapa mental para curso {id_course} ({course_name})")
        
        if not self.client:
            print("[MindMapService ERROR] Cliente Groq não inicializado. Verifique a API Key.")
            return self._create_fallback_structure(course_name, "Cliente Groq não inicializado (API Key ausente ou inválida).")

        course_content_docs = self.get_course_content(id_course)
        if not course_content_docs:
            print(f"[MindMapService WARNING] Nenhum conteúdo encontrado para o curso {id_course} no VectorStore.")
            return self._create_fallback_structure(course_name, "Nenhum conteúdo encontrado para este curso.")

        text_chunks = self.chunk_content_for_mindmap(course_content_docs)
        if not text_chunks or not text_chunks[0].strip():
            print(f"[MindMapService WARNING] Não foi possível processar/extrair texto do conteúdo do curso {id_course}.")
            return self._create_fallback_structure(course_name, "Conteúdo do curso indisponível ou vazio.")

        relevant_text = text_chunks[0]
        print(f"[MindMapService DEBUG] Usando {len(relevant_text)} caracteres de conteúdo para o prompt do mapa mental.")

        prompt = self.generate_mind_map_prompt(course_name, relevant_text)
        
        try:
            print(f"[MindMapService INFO] Enviando requisição para o modelo LLM: {model}")
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Você é um especialista em criar mapas mentais educacionais. Responda sempre e APENAS com JSON válido conforme as instruções."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=4000 
            )
            response_text = response.choices[0].message.content.strip()
            print(f"[MindMapService DEBUG] Resposta crua recebida do LLM (primeiros 300 chars): {response_text[:300]}...")

            json_text = response_text
            if json_text.startswith("```json"):
                json_text = json_text.replace("```json", "", 1).strip()
                if json_text.endswith("```"):
                    json_text = json_text[:-3].strip()
            elif json_text.startswith("```"):
                 json_text = json_text.replace("```", "", 1).strip()
                 if json_text.endswith("```"):
                    json_text = json_text[:-3].strip()

            print(f"[MindMapService DEBUG] JSON após tentativa de limpeza (primeiros 300 chars): {json_text[:300]}...")

            try:
                mind_map_structure = json.loads(json_text)
            except json.JSONDecodeError as e_json:
                print(f"[MindMapService ERROR] Erro ao parsear JSON da resposta do LLM: {e_json}")
                print(f"[MindMapService ERROR] Resposta original completa do LLM que causou o erro:\n{response_text}")
                return self._create_fallback_structure(course_name, f"LLM não retornou JSON válido. Detalhe: {e_json}")

            if not self._validate_structure(mind_map_structure):
                print("[MindMapService ERROR] Estrutura do mapa mental retornada pelo LLM é inválida ou incompleta.")
                print(f"[MindMapService DEBUG] Estrutura recebida que falhou na validação: {json.dumps(mind_map_structure, indent=2)}")
                return self._create_fallback_structure(course_name, "LLM retornou estrutura de mapa mental inválida.")

            print(f"[MindMapService SUCCESS] Mapa mental criado com {len(mind_map_structure.get('nodes',[]))} nós e {len(mind_map_structure.get('edges',[]))} arestas.")
            return mind_map_structure

        except APIError as e_api:
            print(f"[MindMapService ERROR] Erro na API Groq ao gerar mapa mental para curso {id_course}: {e_api}")
            return self._create_fallback_structure(course_name, f"Erro na comunicação com a API de IA: {e_api.status_code}")
        except Exception as e_general:
            print(f"[MindMapService ERROR] Erro inesperado ao gerar mapa mental para curso {id_course}: {e_general}")
            traceback.print_exc()
            return self._create_fallback_structure(course_name, f"Erro inesperado no servidor: {type(e_general).__name__}")

    def _validate_structure(self, structure: Dict) -> bool:
        """Valida se a estrutura do mapa mental está minimamente correta."""
        if not isinstance(structure, dict): return False
        if "nodes" not in structure or not isinstance(structure["nodes"], list): return False
        if "edges" not in structure or not isinstance(structure["edges"], list): return False
        if not structure["nodes"]: return False 
        
        has_root = False
        for node in structure["nodes"]:
            if not isinstance(node, dict): return False
            if "id" not in node or not isinstance(node["id"], str): return False
            if "data" not in node or not isinstance(node["data"], dict): return False
            if "label" not in node["data"] or not isinstance(node["data"]["label"], str): return False
            if "description" in node["data"] and not isinstance(node["data"]["description"], str): return False
            if node["id"] == "root": has_root = True
        
        if not has_root:
            print("[Validation DEBUG] Nó raiz com id 'root' não encontrado.")
            return False

        for edge in structure["edges"]:
            if not isinstance(edge, dict): return False
            if "id" not in edge or not isinstance(edge["id"], str): return False
            if "source" not in edge or not isinstance(edge["source"], str): return False
            if "target" not in edge or not isinstance(edge["target"], str): return False
        return True

    def _create_fallback_structure(self, course_name: str, reason: str = "Falha na geração") -> Dict[str, List[Dict[str, Any]]]:
        """Cria uma estrutura básica de mapa mental como fallback em caso de erro."""
        print(f"[MindMapService INFO] Criando estrutura de fallback para '{course_name}' devido a: {reason}")
        return {
            "nodes": [
                {
                    "id": "root", "type": "input",
                    "data": {"label": course_name, "description": f"Não foi possível gerar o mapa mental detalhado. ({reason})"}
                },
                {
                    "id": "fallback-info",
                    "data": {"label": "Informação Indisponível", "description": "Tente novamente mais tarde ou verifique o conteúdo do curso."}
                }
            ],
            "edges": [
                {"id": "edge-root-fallback", "source": "root", "target": "fallback-info", "animated": True}
            ]
        }
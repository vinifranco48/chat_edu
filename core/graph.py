# core/graph.py
from typing import TypedDict, List, Dict, Any, Optional # Adicionado Optional
from langgraph.graph import StateGraph, END
import json
import traceback
import time # Para debug

# Importa os serviços necessários
from services.embedding_service import EmbeddingService
from services.vector_store_service import VectorStoreService
from services.llm_service import LLMService
from core.prompt_utils import format_rag_prompt
from config.settings import settings

# --- Definição do Estado do Grafo ---
class GraphState(TypedDict):
    """Define o estado que flui através do grafo."""
    query: str
    query_embedding: Optional[List[float]] # Usando Optional e singular
    retrieved_docs: List[Dict[str, Any]] # Payloads recuperados
    context: str                        # Contexto formatado para LLM
    response: Optional[str]             # Resposta final (opcional)
    error: Optional[str]                # Mensagem de erro (opcional)

# --- Nós do Grafo LangGraph ---

def embed_query_node(state: GraphState, embedding_service: EmbeddingService) -> Dict[str, Any]:
    """Nó para gerar o embedding da query."""
    print('--- Nó: Embed Query ---')
    query = state.get("query")
    if not query:
        print("Erro: Query não encontrada no estado.")
        return {"error": json.dumps({"node": "embed_query", "message": "Query ausente no estado."})}

    embedding = None
    try:
        print(f"DEBUG: PREPARANDO para chamar embed_single_text.") # LOG ANTES
        start_time = time.time()
        embedding = embedding_service.embed_single_text(query) # Chama serviço
        end_time = time.time()
        print(f"DEBUG: embed_single_text RETORNOU em {end_time - start_time:.4f}s.") # LOG DEPOIS

        embedding_type = type(embedding)
        print(f"DEBUG: Tipo retornado = {embedding_type}")

        # Validação do resultado
        if embedding is None or not isinstance(embedding, list) or not embedding:
            error_msg = f"Falha ao gerar embedding (resultado inválido: tipo {embedding_type})."
            print(f"Erro: {error_msg}")
            return {"error": json.dumps({"node": "embed_query", "message": error_msg})}

        print("Embedding da query parece válido.")
        return {"query_embedding": embedding, "error": None}

    except Exception as e:
        print(f"Erro EXCEPCIONAL no embed_query_node:")
        detailed_error = traceback.format_exc()
        print(detailed_error)
        return {"error": json.dumps({"node": "embed_query", "message": f"Exceção no embedding: {str(e)}", "details": detailed_error})}

    print("AVISO: embed_query_node fallback. Retornando erro.")
    return {"error": json.dumps({"node": "embed_query", "message": "Fluxo inesperado no nó de embedding."})}


def retrieve_documents_node(state: GraphState, vector_store_service: VectorStoreService) -> Dict[str, Any]:
    """Nó para recuperar documentos relevantes com base no embedding da query."""
    print('--- Nó: Retrieve Documents ---')
    if state.get("error"):
        print(f"Erro anterior detectado: {state.get('error')}. Pulando recuperação.")
        return {}

    # Pega o embedding usando a chave correta (singular)
    query_embedding = state.get("query_embedding")
    if not query_embedding: # Verifica se o embedding foi encontrado no estado
        print("Erro: Embedding da query não encontrado no estado.")
        # Define o erro e retorna
        return {"error": json.dumps({"node": "retrieve_documents", "message": "Embedding da query não encontrado no estado."})}

    try:
        print(f"DEBUG: Buscando documentos com embedding (primeiros 5): {query_embedding[:5]}...")
        retrieved_payloads = vector_store_service.search(query_embedding, limit=settings.retrieval_limit)
        print(f"Recuperados {len(retrieved_payloads)} payloads do Qdrant.")

        context_texts = [payload.get('text') for payload in retrieved_payloads if payload.get('text')]

        if not context_texts:
             print("Aviso: Nenhum texto encontrado nos payloads recuperados.")
             context = "" # Define contexto vazio se nada for encontrado
        else:
             # Junta os textos com um separador claro
             context = "\n\n---\n\n".join(filter(None, context_texts))
             print(f"DEBUG: Contexto montado (primeiros 100 chars): {context[:100]}...")

        # Retorna os documentos e o contexto
        return {
            "retrieved_docs": retrieved_payloads,
            "context": context,
            "error": None 
        }

    except Exception as e:
        print(f"Erro excepcional ao recuperar documentos: {e}")
        detailed_error = traceback.format_exc()
        print(detailed_error)
        return {"error": json.dumps({"node": "retrieve_documents", "message": f"Exceção na busca vetorial: {str(e)}", "details": detailed_error})}


def generate_response_node(state: GraphState, llm_service: LLMService) -> Dict[str, Any]:
    """Nó para gerar a resposta final usando o LLM."""
    print('--- Nó: Generate Response ---')
    if state.get('error'):
        print(f"Erro anterior detectado: {state.get('error')}. Pulando geração de resposta.")
        return {}
    query = state.get('query')
    # Usa contexto, default para string vazia se ausente
    context = state.get('context', "")
    if not query:
        print("Erro: Query não encontrada para gerar resposta.")
        return{"error": json.dumps({"node": "generate_response", "message": "Query ausente."})}

    try:
        # Formata o prompt
        prompt = format_rag_prompt(query=query, context=context)
        print(f"DEBUG: Prompt para LLM (início): {prompt[:200]}...")

        # Usa o nome correto do método do LLMService
        response = llm_service.generate_response(prompt)
        if response is None:
            print("Erro: LLM Service retornou None.")
            return {"error": json.dumps({"node": "generate_response", "message": "Falha ao gerar resposta do LLM."})}

        print("Resposta do LLM gerada.")
        # Retorna a resposta
        return {"response": response, "error": None} # Limpa erro

    except Exception as e:
         print(f"Erro excepcional ao gerar resposta com LLM: {e}")
         detailed_error = traceback.format_exc()
         print(detailed_error)
         return {"error": json.dumps({"node": "generate_response", "message": f"Exceção na geração LLM: {str(e)}", "details": detailed_error})}


def create_compiled_graph(
    embedding_service: EmbeddingService,
    vector_store_service: VectorStoreService,
    llm_service: LLMService
):
    """Constrói e compila o grafo LangGraph, injetando os serviços."""
    print("Construindo e compilando o grafo LangGraph...")

    workflow = StateGraph(GraphState)

    # Adiciona nós, passando os serviços como argumentos fixos usando lambda
    workflow.add_node("embed_query", lambda state: embed_query_node(state, embedding_service))
    workflow.add_node("retrieve_documents", lambda state: retrieve_documents_node(state, vector_store_service))
    workflow.add_node("generate_response", lambda state: generate_response_node(state, llm_service))

    # Define fluxo
    workflow.set_entry_point("embed_query")
    workflow.add_edge("embed_query", "retrieve_documents")
    workflow.add_edge("retrieve_documents", "generate_response")
    workflow.add_edge("generate_response", END)

    # Compila
    compiled_graph = workflow.compile()
    print("Grafo compilado.")
    return compiled_graph
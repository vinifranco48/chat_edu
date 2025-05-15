# core/graph.py
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
import json
import traceback
import time # Para debug

# Importa os serviços necessários
from services.embedding_service import EmbeddingService
from services.vector_store_service import VectorStoreService # Presumo que esteja no caminho correto
from services.llm_service import LLMService # Presumo que esteja no caminho correto
from core.prompt_utils import format_rag_prompt # Presumo que esteja no caminho correto
from config.settings import settings # Presumo que esteja no caminho correto

# Import para o filtro Qdrant
from qdrant_client import models as qdrant_models # <--- ADICIONAR ESTE IMPORT

# --- Definição do Estado do Grafo ---
class GraphState(TypedDict):
    """Define o estado que flui através do grafo."""
    query: str
    id_course: Optional[str] # ID do curso (opcional)
    query_embedding: Optional[List[float]]
    retrieved_docs: List[Dict[str, Any]] # Payloads recuperados
    context: str                    # Contexto formatado para LLM
    response: Optional[str]             # Resposta final (opcional)
    error: Optional[str]                # Mensagem de erro (opcional)

# --- Nós do Grafo LangGraph ---

def embed_query_node(state: GraphState, embedding_service: EmbeddingService) -> Dict[str, Any]:
    """Nó para gerar o embedding da query."""
    print('--- Nó: Embed Query ---')
    query = state.get("query")
    if not query:
        print("Erro: Query não encontrada no estado.")
        return {"error": json.dumps({"node": "embed_query", "message": "Query ausente no estado."}), "query_embedding": None} # Garante que query_embedding exista no output

    embedding = None
    try:
        print(f"DEBUG: PREPARANDO para chamar embed_single_text para a query: '{query[:100]}...'")
        start_time = time.time()
        embedding = embedding_service.embed_single_text(query)
        end_time = time.time()
        print(f"DEBUG: embed_single_text RETORNOU em {end_time - start_time:.4f}s.")

        embedding_type = type(embedding)
        # print(f"DEBUG: Tipo retornado = {embedding_type}, Embedding (primeiros 5): {str(embedding)[:100] if embedding else 'None'}") # Log mais detalhado

        if embedding is None or not isinstance(embedding, list) or not all(isinstance(x, float) for x in embedding) or not embedding:
            error_msg = f"Falha ao gerar embedding (resultado inválido: tipo {embedding_type}, é lista? {isinstance(embedding, list)}, conteúdo é float? {'verificar'})."
            print(f"Erro: {error_msg}")
            return {"error": json.dumps({"node": "embed_query", "message": error_msg}), "query_embedding": None}

        print(f"Embedding da query gerado com sucesso (dimensão: {len(embedding)}).")
        return {"query_embedding": embedding, "error": None}

    except Exception as e:
        print(f"Erro EXCEPCIONAL no embed_query_node:")
        detailed_error = traceback.format_exc()
        print(detailed_error)
        return {"error": json.dumps({"node": "embed_query", "message": f"Exceção no embedding: {str(e)}", "details": detailed_error}), "query_embedding": None}
    
    # Esta linha não deve ser alcançada se a lógica try/except for abrangente.
    # print("AVISO: embed_query_node fallback. Retornando erro.")
    # return {"error": json.dumps({"node": "embed_query", "message": "Fluxo inesperado no nó de embedding."}), "query_embedding": None}


def retrieve_documents_node(state: GraphState, vector_store_service: VectorStoreService) -> Dict[str, Any]: # Removido id_course como argumento direto
    """Nó para recuperar documentos relevantes com base no embedding da query."""
    print('--- Nó: Retrieve Documents ---')
    if state.get("error"):
        print(f"Erro anterior detectado: {state.get('error')}. Pulando recuperação.")
        # Garante que as chaves esperadas existam no retorno, mesmo que vazias/None
        return {"retrieved_docs": [], "context": "", "error": state.get("error")}


    query_embedding = state.get("query_embedding")
    id_course = state.get("id_course") # Pega o id_course do estado

    if not query_embedding:
        print("Erro: Embedding da query não encontrado no estado.")
        return {"retrieved_docs": [], "context": "", "error": json.dumps({"node": "retrieve_documents", "message": "Embedding da query não encontrado no estado."})}

    try:
        # --- AJUSTE PRINCIPAL AQUI para construir o filtro Qdrant ---
        qdrant_filter_obj: Optional[qdrant_models.Filter] = None
        if id_course:
            print(f"DEBUG: Aplicando filtro para course_id: {id_course}")
            qdrant_filter_obj = qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="course_id",  # Certifique-se que este é o nome exato do campo no payload do Qdrant
                        match=qdrant_models.MatchValue(value=id_course)
                    )
                ]
            )
        else:
            print("DEBUG: Nenhum course_id fornecido, buscando em todos os documentos.")
        # --- Fim do ajuste do filtro ---

        print(f"DEBUG: Buscando documentos com embedding (primeiros 5): {str(query_embedding)[:100]}... e filtro: {qdrant_filter_obj}")
        
        # Passa o objeto de filtro construído para o método search
        retrieved_payloads = vector_store_service.search(
            query_vector=query_embedding, # Nomeado como query_vector no VectorStoreService
            limit=settings.retrieval_limit,
            filter=qdrant_filter_obj # Passa o objeto models.Filter
        )
        print(f"Recuperados {len(retrieved_payloads)} payloads do Qdrant.")

        context_texts = [payload.get('text') for payload in retrieved_payloads if payload and payload.get('text')] # Adicionada verificação de payload

        if not context_texts:
            print("Aviso: Nenhum texto encontrado nos payloads recuperados. Contexto estará vazio.")
            context = ""
        else:
            context = "\n\n---\n\n".join(context_texts) # Removido filter(None, ...) pois a list comprehension já cuida disso
            print(f"DEBUG: Contexto montado (primeiros 100 chars): {context[:100]}...")

        return {
            "retrieved_docs": retrieved_payloads,
            "context": context,
            "error": None
        }

    except Exception as e:
        print(f"Erro excepcional ao recuperar documentos: {e}")
        detailed_error = traceback.format_exc()
        print(detailed_error)
        return {"retrieved_docs": [], "context": "", "error": json.dumps({"node": "retrieve_documents", "message": f"Exceção na busca vetorial: {str(e)}", "details": detailed_error})}


def generate_response_node(state: GraphState, llm_service: LLMService) -> Dict[str, Any]:
    """Nó para gerar a resposta final usando o LLM."""
    print('--- Nó: Generate Response ---')
    if state.get('error'):
        print(f"Erro anterior detectado: {state.get('error')}. Pulando geração de resposta.")
        return {"response": None, "error": state.get("error")} # Garante que response exista no output

    query = state.get('query')
    context = state.get('context', "") # Default para string vazia se ausente ou None

    if not query:
        print("Erro: Query não encontrada para gerar resposta.")
        return{"response": None, "error": json.dumps({"node": "generate_response", "message": "Query ausente."})}

    try:
        prompt = format_rag_prompt(query=query, context=context)
        print(f"DEBUG: Prompt para LLM (início): {prompt[:200]}...")

        response = llm_service.generate_response(prompt) # Supondo que este método exista no LLMService
        if response is None: # Ou if not response: se uma string vazia também for considerada falha
            print("Erro: LLM Service retornou None ou resposta vazia.")
            return {"response": None, "error": json.dumps({"node": "generate_response", "message": "Falha ao gerar resposta do LLM (resposta None/vazia)."})}

        print(f"Resposta do LLM gerada (início): {response[:100]}...")
        return {"response": response, "error": None}

    except Exception as e:
        print(f"Erro excepcional ao gerar resposta com LLM: {e}")
        detailed_error = traceback.format_exc()
        print(detailed_error)
        return {"response": None, "error": json.dumps({"node": "generate_response", "message": f"Exceção na geração LLM: {str(e)}", "details": detailed_error})}


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
    # Não é mais necessário passar id_course aqui, pois o nó o pega do 'state'
    workflow.add_node("retrieve_documents", lambda state: retrieve_documents_node(state, vector_store_service))
    workflow.add_node("generate_response", lambda state: generate_response_node(state, llm_service))

    # Define fluxo
    workflow.set_entry_point("embed_query")
    workflow.add_edge("embed_query", "retrieve_documents")
    workflow.add_edge("retrieve_documents", "generate_response")
    workflow.add_edge("generate_response", END)

    # Compila
    compiled_graph = workflow.compile()
    print("Grafo compilado com sucesso.")
    return compiled_graph
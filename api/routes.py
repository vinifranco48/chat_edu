# api/routes.py

from fastapi import APIRouter, HTTPException, Depends, Query
from langgraph.graph.state import StateGraph
from typing import Annotated, Optional

from api.models import QueryRequest, QueryResponse
from core.graph import GraphState
import traceback
from services.vector_store_service import VectorStoreService 
from services.flashcard_service import FlashcardService
from crawler.login import navegar_e_extrair_cursos_visitando, realizar_login
import time
from dotenv import load_dotenv
import sys
import os
from config.settings import settings 


load_dotenv()
# Cria routers
router = APIRouter(
    prefix="/chat",
    tags=["Chatbot"]
)

auth_router = APIRouter(
    prefix="/login",
    tags=["Authentication"]
)

retriever_router = APIRouter(
    prefix="/retriever",
    tags=["Retriever"]
)


flashcards_router = APIRouter(
    prefix="/flashcards",
    tags=["flashcards"]
)
# Variáveis globais para instâncias injetadas
compiled_graph_instance: Optional[StateGraph] = None 
_vector_store_service_instance: Optional[VectorStoreService] = None 

def set_compiled_graph(graph: StateGraph):
    """Função para injetar o grafo compilado no router."""
    global compiled_graph_instance
    compiled_graph_instance = graph

def get_compiled_graph() -> StateGraph:
    if compiled_graph_instance is None:
        raise RuntimeError("Grafo LangGraph não foi inicializado corretamente.")
    return compiled_graph_instance

def set_vector_store_service(service: VectorStoreService):
    """Função para injetar a instância do VectorStoreService."""
    global _vector_store_service_instance
    _vector_store_service_instance = service

def get_vector_store_service_dependency() -> VectorStoreService:
    """Função de dependência para obter a instância do VectorStoreService."""
    if _vector_store_service_instance is None:
        raise RuntimeError("VectorStoreService não foi inicializado e injetado corretamente.")
    return _vector_store_service_instance


@router.post("/", response_model=QueryResponse)
async def handle_chat_query(
    request: QueryRequest,
    graph: Annotated[StateGraph, Depends(get_compiled_graph)]
) -> QueryResponse:
    """
    Recebe a consulta do usuário, processa através do grafo LangGraph e retorna a resposta.
    
    """
    print(f"\n--- Nova Requisição API Recebida (dentro de handle_chat_query) ---")
    print(f"Query Text: {request.text}")
    course_id_from_request = getattr(request, 'courseId', 'NÃO RECEBIDO')
    print(f"Course ID Recebido do Request: {course_id_from_request}")

    initial_state: GraphState = {
        "query": request.text,
        "id_course": course_id_from_request, 
        "query_embedding": None,
        "retrieved_docs": [],
        "context": "",
        "response": None,
        "error": None
    }
    print(f"Estado Inicial Configurado para o Grafo: {initial_state}")

    try:
        final_state = graph.invoke(initial_state)
        if final_state.get("error"):
            print(f"Erro retornado pelo grafo: {final_state['error']}")
            return QueryResponse(error=final_state["error"])

        response_text = final_state.get("response")
        if not response_text:
            print("Erro: Grafo concluiu sem resposta e sem erro explícito.")
            return QueryResponse(error="Falha interna ao gerar a resposta.")

        sources = []
        retrieved = final_state.get("retrieved_docs", [])
        for doc_payload in retrieved:
            source_info = {
                "source": doc_payload.get("source", "desconhecido"),
                "page": doc_payload.get("page", -1),
            }
            if source_info not in sources:
                sources.append(source_info)

        print(f"Resposta final: {response_text[:100]}...")
        return QueryResponse(response=response_text, retrieved_sources=sources)

    except Exception as e:
        print(f"Erro inesperado no endpoint /chat: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno no servidor: {e}")



@auth_router.post("/")
async def login(username: str, password: str):
    """ Realiza login no site e retorna os cursos disponíveis. """
    driver = None
    cursos_processados = []
    start_time = time.time()

    try:
        driver = realizar_login(username, password)
        if not driver:
            return {"success": False, "message": "Falha no login. Verifique suas credenciais."}

        cursos_processados = navegar_e_extrair_cursos_visitando(driver)
        if cursos_processados:
            return {"success": True, "cursos": cursos_processados}
        else:
            return {"success": True, "message": "Login bem-sucedido, mas nenhuma matéria encontrada.", "cursos": []}

    except KeyboardInterrupt:
        return {"success": False, "message": "Operação interrompida pelo usuário."}
    except Exception as e_main:
        print(f"Erro inesperado durante a execução principal: {e_main}")
        traceback.print_exc()
        return {"success": False, "message": f"Erro inesperado: {e_main}"}
    finally:
        end_time = time.time()
        print(f"Tempo total de execução: {end_time - start_time:.2f} segundos")
        if driver:
            try:
                driver.quit()
            except Exception as e_quit:
                print(f"Erro ao fechar navegador: {e_quit}")


@retriever_router.post("/{course_id}")
async def retriever_embeddings_id(
    course_id: str,
    # Injeta a instância correta do VectorStoreService
    svc: Annotated[VectorStoreService, Depends(get_vector_store_service_dependency)]
):
    """Retorna embeddings filtrados por course_id do VectorStoreService."""
    try:
        if not course_id:
            raise HTTPException(status_code=400, detail="ID do curso inválido.")
        documents_with_embeddings = svc.get_all_by_course_id(course_id_filter=course_id)
        
        if not documents_with_embeddings:
            # Alterado para retornar uma lista vazia em vez de 404,
            # pois o frontend espera um objeto com a chave "embeddings"
            return {"embeddings": []}
            # raise HTTPException(status_code=404, detail="Nenhum embedding encontrado para este curso.")

        # O frontend espera um dicionário com uma chave "embeddings" contendo uma lista.
        # A natureza dos "embeddings" aqui precisa ser clarificada.
        # Se `documents_with_embeddings` já for a lista de embeddings (vetores numéricos), ok.
        # Se for uma lista de Documentos Langchain, você precisa extrair o conteúdo ou metadados relevantes.
        # O frontend parece usar o resultado diretamente em `courseEmbeddings` e depois o envia
        # para o /chat. O /chat endpoint em `QueryRequest` espera `embeddings: courseEmbeddings`.
        # O grafo LangGraph provavelmente espera uma lista de Documentos ou strings.

        # Exemplo: se documents_with_embeddings for uma lista de objetos Document do Langchain
        # e você quer enviar os documentos para o frontend (que depois os envia para /chat)
        # talvez seja melhor retornar os documentos serializáveis.
        # Por enquanto, vou assumir que o que svc.search_with_filter retorna é o que o frontend espera.
        
        # Mapeie os documentos para o formato esperado pelo frontend/chat, se necessário.
        # O frontend espera que courseEmbeddings seja usado no corpo da requisição para /chat.
        # O backend /chat, por sua vez, passa isso para o grafo.
        # Se o grafo espera Documentos, e `svc.search_with_filter` retorna Documentos,
        # o frontend precisa ser capaz de serializar/deserializar isso, o que não é trivial.

        # Assumindo que `svc.search_with_filter` retorna dados serializáveis que o frontend pode manipular:
        return {"embeddings": documents_with_embeddings }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Erro inesperado ao buscar embeddings: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Erro interno ao buscar embeddings.")
    
@flashcards_router.post("/{id_course}")
async def generate_flashcards(
    id_course: str,
    vector_size: int = Query(1536, description="Tamanho do vetor para o serviço de flashcards.") # Explicitamente como Query
):
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("!!! ERRO CRÍTICO: GROQ_API_KEY não está configurada no ambiente !!!")
            raise HTTPException(status_code=500, detail="Configuração do servidor incompleta.")

        # Assumindo que 'settings.llm_model_name' existe e está configurado
        if not hasattr(settings, 'llm_model_name') or not settings.llm_model_name:
            print("!!! ERRO CRÍTICO: settings.llm_model_name não está configurado !!!")
            raise HTTPException(status_code=500, detail="Configuração do servidor incompleta.")

        # Lembre-se da discussão sobre a instância do VectorStoreService usada aqui
        flashcard_service_instance = FlashcardService(vector_size=vector_size, api_key=api_key)
        
        list_flashcards = flashcard_service_instance.create_flashcards(
            id_course=id_course,
            model=settings.llm_model_name
        )
        
        # create_flashcards deve retornar uma lista (pode ser vazia)
        return list_flashcards

    except HTTPException: # Re-raise HTTPExceptions para que não sejam capturadas pelo catch-all
        raise
    except Exception as e:
        print(f"!!! ERRO INESPERADO ao gerar flashcards para o curso {id_course} !!!")
        print(f"Tipo de Erro: {type(e).__name__}, Mensagem: {str(e)}")
        traceback.print_exc() # Imprime o stack trace completo no console do backend
        raise HTTPException(status_code=500, detail=f"Erro interno ao gerar flashcards: {str(e)}")

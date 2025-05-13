from fastapi import APIRouter, HTTPException, Depends
from langgraph.graph.state import StateGraph
from typing import Annotated 

from api.models import QueryRequest, QueryResponse
from core.graph import GraphState  # Importa o tipo do estado
from crawler.login import navegar_e_extrair_cursos_visitando, realizar_login
import time
import traceback
import os
from services.vector_store_service import VectorStoreService

# Cria routers para os diferentes endpoints da API
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

compiled_graph_instance: StateGraph | None = None


def set_compiled_graph(graph: StateGraph):
    """Função para injetar o grafo compilado no router."""
    global compiled_graph_instance
    compiled_graph_instance = graph


# Função de dependência para obter o grafo
def get_compiled_graph() -> StateGraph:
    if compiled_graph_instance is None:
        raise RuntimeError("Grafo LangGraph não foi inicializado corretamente.")
    return compiled_graph_instance


@router.post("/", response_model=QueryResponse)
async def handle_chat_query(
    request: QueryRequest,
    graph: Annotated[StateGraph, Depends(get_compiled_graph)]
) -> QueryResponse:
    """
    Recebe a consulta do usuário, processa através do grafo LangGraph e retorna a resposta.
    """
    print(f"\n--- Nova Requisição API Recebida --- \nQuery: {request.text}")
    initial_state: GraphState = {"query": request.text}

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
async def retriever_embeddings_id(course_id: str):
    """Retorna embeddings filtrados por course_id do VectorStoreService."""
    try:
        if not course_id:
            raise HTTPException(status_code=400, detail="ID do curso inválido.")
        svc = VectorStoreService()
        embeddings = svc.search_with_filter(course_id_filter=course_id)
        if not embeddings:
            raise HTTPException(status_code=404, detail="Nenhum embedding encontrado para este curso.")
        return {"embeddings": embeddings}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erro inesperado ao buscar embeddings: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Erro interno ao buscar embeddings.")

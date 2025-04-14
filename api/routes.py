from fastapi import APIRouter, HTTPException, Depends
from langgraph.graph.state import StateGraph
from typing import Annotated 

from api.models import QueryRequest, QueryResponse
from core.graph import GraphState # Importa o tipo do estado

# Cria um router para os endpoints da API
router = APIRouter(
tags=["Chatbot"] # Tag para a documentação Swagger/OpenAPI
)

compiled_graph_instance: StateGraph | None = None

def set_compiled_graph(graph: StateGraph):
    """Função para injetar o grafo compilado no router."""
    global compiled_graph_instance
    compiled_graph_instance = graph

# Função de dependência para obter o grafo
def get_compiled_graph() -> StateGraph:
     if compiled_graph_instance is None:
          # Isso indica um erro de inicialização na aplicação
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
        # Adicionar config se necessário: config={"recursion_limit": 5}
        final_state = graph.invoke(initial_state)

        # Processa o resultado
        if final_state.get("error"):
            print(f"Erro retornado pelo grafo: {final_state['error']}")
            # Não levanta HTTPException aqui, retorna no corpo da resposta
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
                 # Adicionar um snippet do texto? Cuidado com o tamanho da resposta.
                 # "snippet": doc_payload.get("text", "")[:100] + "..."
             }
             # Evitar duplicados baseados em source/page se necessário
             if source_info not in sources:
                  sources.append(source_info)

        print(f"Resposta final: {response_text[:100]}...")
        return QueryResponse(response=response_text, retrieved_sources=sources)

    except Exception as e:
        # Captura erros inesperados durante a invocação do grafo ou processamento
        print(f"Erro inesperado no endpoint /chat: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno no servidor: {e}")
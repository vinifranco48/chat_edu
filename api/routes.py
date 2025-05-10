from fastapi import APIRouter, HTTPException, Depends
from langgraph.graph.state import StateGraph
from typing import Annotated 

from api.models import QueryRequest, QueryResponse
from core.graph import GraphState # Importa o tipo do estado
from crawler.login import navegar_e_extrair_cursos_visitando, realizar_login
import time
import traceback
import os
import service.vector_store_service as vector_store_service

# Cria um router para os endpoints da API de chat
router = APIRouter(
    tags=["Chatbot"]
)

auth_router = APIRouter(
    tags=["Authentication"]
)

auth_router = APIRouter(
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


@auth_router.post("/")
async def login(username: str, password: str):
    """ Realiza login no site e retorna os cursos disponíveis. """
    driver = None # Inicializa a variável fora do try
    cursos_processados = [] # Inicializa lista de resultados
    start_time = time.time() # Medir tempo total

    try:
        # 1. Tenta realizar o login
        driver = realizar_login(username, password)

        # 2. Verifica se o login foi bem-sucedido
        if not driver:
            print("\n-----------------------------------------")
            print("VALIDAÇÃO: Falha no login. Script encerrado.")
            print("-----------------------------------------")
            return {"success": False, "message": "Falha no login. Verifique suas credenciais."}
        else:
            print("\n-----------------------------------------")
            print("VALIDAÇÃO: Login realizado com sucesso!")
            print(f"URL atual: {driver.current_url}")
            print("-----------------------------------------")

            # 3. Se o login funcionou, tenta extrair os cursos
            cursos_processados = navegar_e_extrair_cursos_visitando(driver)

            print("\n------------------- RESULTADO FINAL --------------------")
            if cursos_processados:
                print(f"MATÉRIAS PROCESSADAS ({len(cursos_processados)}):")
                erros_nome = 0
                for i, curso in enumerate(cursos_processados):
                    # Imprime formatado para melhor leitura
                    print(f"{i+1: >3}. ID: {curso.get('id', 'N/A'): <8} | Nome: {curso.get('nome', 'N/A')}")
                    # Descomente para ver a URL também
                    # print(f"      URL: {curso.get('url', 'N/A')}")
                    if "ERRO_" in curso.get('nome', ''):
                        erros_nome += 1
                if erros_nome > 0:
                    print(f"\nAlerta: {erros_nome} curso(s) tiveram erro na busca do nome na página do curso.")
                else:
                    print("\nTodos os nomes de curso foram extraídos com sucesso das páginas.")
                
                return {"success": True, "cursos": cursos_processados}
            else:
                print("MATÉRIAS: Não foi possível listar ou processar as matérias após o login.")
                return {"success": True, "message": "Login bem-sucedido, mas nenhuma matéria encontrada.", "cursos": []}
            print("-------------------------------------------------------")

    except KeyboardInterrupt:
        # Permite interromper o script com Ctrl+C de forma limpa
        print("\nOperação interrompida pelo usuário (Ctrl+C).")
        return {"success": False, "message": "Operação interrompida pelo usuário."}
    except Exception as e_main:
        # Captura qualquer outra exceção não tratada
        print(f"\nErro inesperado durante a execução principal: {str(e_main)}")
        traceback.print_exc()
        return {"success": False, "message": f"Erro inesperado: {str(e_main)}"}
    finally:
        # Este bloco SEMPRE será executado, independentemente de erros ou interrupções
        end_time = time.time()
        print(f"\nTempo total de execução: {end_time - start_time:.2f} segundos")
        if driver:
            print("Encerrando o navegador...")
            try:
                driver.quit() # Garante que o navegador e o driver sejam fechados
                print("Navegador encerrado com sucesso.")
            except Exception as e_quit:
                print(f"Erro ao tentar fechar o navegador: {str(e_quit)}")
                print("Pode ser necessário fechar processos 'chrome' ou 'chromedriver' manualmente.")

@auth_router.post("/")
async def retriever_embeddings_id(id: str):
    try:
        # Verifica se o ID do curso é válido
        if not id or not isinstance(id, str):
            raise HTTPException(status_code=400, detail="ID do curso inválido.")
        result = vector_store_service.search_with_filter(id_course=id)
        return result
    except Exception as e:
        print(f"Erro inesperado ao buscar embeddings: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao buscar embeddings.")



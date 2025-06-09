import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import traceback
import time
from pathlib import Path
try:
    from config.settings import settings
except Exception as config_error:
    print(f"\n !!! ERRO CRÍTICO AO CARREGAR settings.py !!!")
    print(f"Erro: {config_error}")
    traceback.print_exc()
    print("Verifique config/settings.py e .env. A aplicação será encerrada.")
    exit(1) 

from services.embedding_service import EmbeddingService
from services.vector_store_service import VectorStoreService
from services.llm_service import LLMService
from services.document_service import load_and_split_pdf
from core.graph import create_compiled_graph
from api.routes import ( 
    router as chat_router,
    auth_router,
    retriever_router,
    flashcards_router,
    mindmaps_router,  
    set_compiled_graph,
    set_vector_store_service
)

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

# --- Inicialização da Aplicação ---
print("--- Inicializando Aplicação Chat Edu ---")
try:
    pdf_directory_path_str = os.path.abspath(settings.pdf_dir) if settings.pdf_dir else None
    if not pdf_directory_path_str or not os.path.isdir(pdf_directory_path_str):
        raise FileNotFoundError(
            f"Diretório de PDFs (PDF_DIR='{settings.pdf_dir}') inválido, não encontrado ou não é um diretório. "
            f"Verifique .env e o caminho: '{pdf_directory_path_str}'"
        )
    print(f"Diretório de PDFs configurado: {pdf_directory_path_str}")

    print("Inicializando serviços...")
    embedding_service = EmbeddingService()
    vector_size = embedding_service.get_embedding_dimension()
    vector_store_service = VectorStoreService(vector_size=vector_size) 
    llm_service = LLMService()
    print("Serviços principais inicializados.")

    # --- Lógica de Ingestão de Dados (In-Memory Mode) ---
    if settings.qdrant_mode == 'memory':
        print(f"\n--- Iniciando Ingestão In-Memory (Modo '{settings.qdrant_mode}') ---")
        ingestion_start_time = time.time()

        pdf_directory = Path(pdf_directory_path_str)
        pdf_files_found = list(pdf_directory.glob("*.pdf"))

        all_documents = []
        if not pdf_files_found:
            print(f"Aviso: Nenhum arquivo .pdf encontrado no diretório '{pdf_directory}'. O Vector Store estará vazio se não houver ingestão prévia.")
        else:
            print(f"Encontrados {len(pdf_files_found)} arquivos PDF para processar.")
            for pdf_path in pdf_files_found:
                try:
                    print(f"Processando arquivo: {pdf_path.name}...")
                    docs = load_and_split_pdf(str(pdf_path))
                    if docs:
                        all_documents.extend(docs)
                        print(f"Processado {pdf_path.name}: {len(docs)} chunks.")
                    else:
                        print(f"Nenhum documento extraído de {pdf_path.name}.")
                except Exception as e_pdf:
                    print(f"Erro ao processar o arquivo PDF {pdf_path.name}: {e_pdf}")

            if all_documents:
                print(f"Total de {len(all_documents)} chunks de documentos para gerar embeddings.")
                all_contents = [doc.page_content for doc in all_documents if hasattr(doc, 'page_content')]
                
                if not all_contents or len(all_contents) != len(all_documents):
                    print("Aviso: Alguns documentos não possuem 'page_content' ou a lista de conteúdos está vazia.")
                
                if all_contents:
                    print("Gerando embeddings para os documentos...")
                    doc_embeddings = embedding_service.embed_texts(all_contents)
                    
                    if doc_embeddings and len(doc_embeddings) == len(all_contents):
                        
                        # Filtra documentos que não geraram conteúdo para manter a consistência
                        valid_documents_for_upsert = [doc for doc in all_documents if hasattr(doc, 'page_content') and doc.page_content]

                        if len(doc_embeddings) == len(valid_documents_for_upsert):
                            print(f"Inserindo {len(doc_embeddings)} documentos com embeddings no Vector Store...")
                            vector_store_service.upsert_documents(valid_documents_for_upsert, doc_embeddings)
                            print(f"Documentos e embeddings inseridos com sucesso.")
                        else:
                            print(f"Discrepância entre número de embeddings ({len(doc_embeddings)}) e documentos válidos ({len(valid_documents_for_upsert)}). Inserção abortada.")
                    else:
                        print("Falha na geração de embeddings ou contagem de embeddings divergente da contagem de conteúdos.")
            else:
                print("Nenhum documento foi carregado para ingestão.")
        
        ingestion_end_time = time.time()
        print(f"--- Ingestão In-Memory concluída em {(ingestion_end_time - ingestion_start_time):.2f}s ---\n")
    else:
        print(f"Modo Qdrant configurado para '{settings.qdrant_mode}'. "
              "Certifique-se de que os dados foram ingeridos previamente ou que o modo de persistência está configurado.")

    # --- Configuração do Grafo LangGraph e Injeção de Dependências ---
    print("Criando o grafo LangGraph...")
    compiled_graph = create_compiled_graph(
        embedding_service=embedding_service,
        vector_store_service=vector_store_service,
        llm_service=llm_service
    )
    set_compiled_graph(compiled_graph) 
    print("Grafo LangGraph criado e injetado no router.")
    
    set_vector_store_service(vector_store_service)
    print("VectorStoreService injetado no router.")

    # --- Criação da Aplicação FastAPI ---
    app = FastAPI(
        title="Chat Edu API",
        description="API para o chatbot educacional com LangGraph, RAG, Flashcards e Mapas Mentais.",
        version="1.3.0"  
    )

    # --- Configuração do Middleware (CORS) ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS, 
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Inclusão dos Routers ---
    print("Registrando rotas...")
    app.include_router(auth_router)
    app.include_router(chat_router)
    app.include_router(retriever_router)
    app.include_router(flashcards_router)
    app.include_router(mindmaps_router) 
    print("Rotas de autenticação, chat, retriever, flashcards e mapas mentais registradas.")

    #Imprimir todas as rotas registradas para verificação
    # print("\n--- Rotas Registradas na Aplicação ---")
    # for route in app.routes:
    # if hasattr(route, "methods"):
    # print(f"Path: {route.path}, Methods: {route.methods}, Name: {route.name}")
    # else:
    # print(f"Path: {route.path}, Name: {route.name}")
    # print("-------------------------------------\n")

    print("--- Aplicação Chat Edu pronta para iniciar ---")

except Exception as init_err:
    print(f"\n !!! ERRO CRÍTICO DURANTE A INICIALIZAÇÃO DA APLICAÇÃO !!!")
    print(f"Erro: {init_err}")
    traceback.print_exc()
    print("A aplicação será encerrada.")
    exit(1) #NOSONAR


if __name__ == "__main__":
    uvicorn_host = getattr(settings, 'uvicorn_host', '0.0.0.0')
    uvicorn_port = getattr(settings, 'uvicorn_port', 8000)
    uvicorn_reload = getattr(settings, 'uvicorn_reload', False)
    uvicorn_log_level = getattr(settings, 'uvicorn_log_level', 'info').lower()

    print(f"Iniciando servidor Uvicorn em {uvicorn_host}:{uvicorn_port}")
    uvicorn.run(
        "main:app",
        host=uvicorn_host,
        port=uvicorn_port,
        reload=uvicorn_reload,
        log_level=uvicorn_log_level
    )
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
    print("Usando valores padrão ou abortando. Verifique config/settings.py e .env")
    exit(1)

from services.embedding_service import EmbeddingService
from services.vector_store_service import VectorStoreService
from services.llm_service import LLMService
from services.document_service import load_and_split_pdf
from core.graph import create_compiled_graph
from api.routes import router as chat_router, set_compiled_graph, auth_router, retriever_router

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

# --- Inicialização dos Serviços ---
print("--- Inicializando Aplicação Chat Edu ---")
try:
    pdf_directory_path_str = os.path.abspath(settings.pdf_dir) if settings.pdf_dir else None
    if not pdf_directory_path_str or not os.path.isdir(pdf_directory_path_str):
        raise FileNotFoundError(
            f"Diretório de PDFs (PDF_DIR='{settings.pdf_dir}') inválido, não encontrado ou não é um diretório. Verifique .env e o caminho: '{pdf_directory_path_str}'"
        )
    print(f"Diretório de PDFs configurado: {pdf_directory_path_str}")

    # Inicializa serviços
    embedding_service = EmbeddingService()
    vector_size = embedding_service.get_embedding_dimension()
    vector_store_service = VectorStoreService(vector_size=vector_size)
    llm_service = LLMService()

    # Ingestão in-memory se aplicável
    if settings.qdrant_mode == 'memory':
        print(f"\n--- Iniciando Ingestão In-Memory (Modo '{settings.qdrant_mode}') ---")
        ingestion_start_time = time.time()

        pdf_directory = Path(pdf_directory_path_str)
        pdf_files_found = list(pdf_directory.glob("*.pdf"))

        all_documents = []
        if not pdf_files_found:
            print(f"Aviso: Nenhum arquivo .pdf encontrado no diretório '{pdf_directory}'. O Vector Store estará vazio.")
        else:
            for pdf_path in pdf_files_found:
                try:
                    docs = load_and_split_pdf(str(pdf_path))
                    if docs:
                        all_documents.extend(docs)
                        print(f"Processado {pdf_path.name}: {len(docs)} chunks.")
                except Exception as e:
                    print(f"Erro ao processar {pdf_path.name}: {e}")

        if all_documents:
            all_contents = [doc.page_content for doc in all_documents]
            embeddings = embedding_service.embed_texts(all_contents)
            if embeddings and len(embeddings) == len(all_documents):
                print(f"Gerando e inserindo {len(embeddings)} embeddings...")
                vector_store_service.upsert_documents(all_documents, embeddings)
            else:
                print("Falha na geração de embeddings ou contagem divergente.")
        ingestion_end_time = time.time()
        print(f"--- Ingestão In-Memory concluída em {(ingestion_end_time - ingestion_start_time):.2f}s ---\n")
    else:
        print(f"Modo Qdrant '{settings.qdrant_mode}'. Certifique-se de ingestão prévia de dados.")

    # Criação do Grafo
    print("Criando o grafo LangGraph...")
    compiled_graph = create_compiled_graph(
        embedding_service=embedding_service,
        vector_store_service=vector_store_service,
        llm_service=llm_service
    )
    set_compiled_graph(compiled_graph)
    print("Grafo LangGraph injetado no router.")

    # Criação do app FastAPI
    app = FastAPI(
        title="Chat Edu API",
        description="API para o chatbot educacional com LangGraph e RAG.",
        version="1.2.1"
    )

    # Middleware CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Inclusão de routers
    app.include_router(chat_router,      prefix="/chat")
    app.include_router(auth_router,      prefix="/login", tags=["Authentication"])
    app.include_router(retriever_router, prefix="/retriever", tags=["Retriever"])  # Corrigido: incluído retriever_router

    # Debug: listar rotas
    print("Rotas registradas:")
    for route in app.routes:
        print(f"{route.methods} -> {route.path}")

    print("--- Aplicação pronta para iniciar ---")

except Exception as init_err:
    print(f"\n !!! ERRO DURANTE A INICIALIZAÇÃO !!! {init_err}")
    traceback.print_exc()
    exit(1)

# Ponto de execução
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

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
from api.routes import router as chat_router, set_compiled_graph, auth_router

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

# --- Inicialização dos Serviços ---
print("--- Inicializando Aplicação Chat Edu ---")
try:
    # Validação inicial do diretório de PDFs (mesmo que a ingestão só ocorra depois)
    pdf_directory_path_str = os.path.abspath(settings.pdf_dir) if settings.pdf_dir else None
    if not pdf_directory_path_str or not os.path.isdir(pdf_directory_path_str):
          raise FileNotFoundError(f"Diretório de PDFs (PDF_DIR='{settings.pdf_dir}') inválido, não encontrado ou não é um diretório. Verifique .env e o caminho: '{pdf_directory_path_str}'")
    print(f"Diretório de PDFs configurado: {pdf_directory_path_str}")

    # Inicializa serviços essenciais primeiro
    embedding_service = EmbeddingService()
    vector_size = embedding_service.get_embedding_dimension()
    vector_store_service = VectorStoreService(vector_size=vector_size)
    llm_service = LLMService()

    # --- Ingestão de Dados (Apenas se Qdrant for in-memory) ---
    if settings.qdrant_mode == 'memory':
        print(f"\n--- Iniciando Ingestão In-Memory (Modo '{settings.qdrant_mode}') ---")
        ingestion_start_time = time.time()

        pdf_directory = Path(pdf_directory_path_str) 

        # Encontrar Arquivos PDF
        pdf_files_found = list(pdf_directory.glob("*.pdf"))

        if not pdf_files_found:
            print(f"Aviso: Nenhum arquivo .pdf encontrado no diretório '{pdf_directory}'. O Vector Store estará vazio.")
            all_documents = [] # Garante que a lista exista, mesmo vazia
        else:
            print(f"Encontrados {len(pdf_files_found)} arquivos PDF para processar:")
            for pdf_path in pdf_files_found:
                print(f"  - {pdf_path.name}")

            # Carregar e Dividir Documentos (Iterativamente)
            print("\nCarregando e dividindo documentos...")
            all_documents = [] # Inicializa a lista para guardar todos os chunks

            for pdf_path in pdf_files_found:
                print(f"Processando: {pdf_path.name}...")
                try:
                    # Chama a função que processa UM PDF por vez
                    documents_from_single_pdf = load_and_split_pdf(str(pdf_path)) # Converte Path para string
                    if documents_from_single_pdf:
                        all_documents.extend(documents_from_single_pdf)
                        print(f"  -> {len(documents_from_single_pdf)} chunks adicionados.")
                    else:
                        print(f"  -> Aviso: Nenhum chunk gerado para {pdf_path.name}.")
                except Exception as load_err:
                     print(f"  -> Erro ao processar {pdf_path.name}: {load_err}. Pulando este arquivo.")

            if not all_documents:
                 print("\nAviso: Nenhum chunk válido foi gerado após processar todos os PDFs encontrados. O Vector Store estará vazio.")
            else:
                 print(f"\nTotal de {len(all_documents)} chunks gerados de {len(pdf_files_found)} PDFs.")

                 # Gerar Embeddings (somente se houver documentos)
                 print("Gerando embeddings para os chunks...")
                 try:
                     all_doc_contents = [doc.page_content for doc in all_documents]
                     embeddings = embedding_service.embed_texts(all_doc_contents)

                     if embeddings and len(embeddings) == len(all_documents):
                         print(f"Embeddings gerados com sucesso ({len(embeddings)} vetores).")

                         # Inserir no Vector Store (somente se embeddings ok)
                         print("Inserindo documentos e embeddings no Vector Store in-memory...")
                         upsert_success = vector_store_service.upsert_documents(all_documents, embeddings)
                         if upsert_success:
                             print("Documentos inseridos com sucesso.")
                         else:
                             print("Aviso: Falha ao inserir documentos no Vector Store in-memory (verifique logs do VectorStoreService).")
                     else:
                         emb_count = len(embeddings) if embeddings else 0
                         doc_count = len(all_documents)
                         print(f"Aviso: Falha na geração de embeddings ou número de embeddings ({emb_count}) não corresponde ao número de documentos ({doc_count}). Nenhum dado foi inserido.")

                 except Exception as embed_upsert_err:
                     print(f"\n !!! ERRO DURANTE EMBEDDING/UPSERT !!!")
                     print(f"Erro: {embed_upsert_err}")
                     traceback.print_exc()
                     print("Ingestão in-memory falhou nesta etapa.")

        ingestion_end_time = time.time()
        duration = ingestion_end_time - ingestion_start_time
        print(f"--- Ingestão In-Memory Concluída em {duration:.2f} segundos ---\n")

    else: 
          print(f"Modo Qdrant '{settings.qdrant_mode}'. Certifique-se de que os dados foram ingeridos no Qdrant persistente (ex: usando um script como 'ingest_data.py' que processe múltiplos PDFs).")


    # --- Criação do Grafo Compilado ---
    print("Criando o grafo computacional LangGraph...")
    compiled_graph = create_compiled_graph(
        embedding_service=embedding_service,
        vector_store_service=vector_store_service,
        llm_service=llm_service
    )
    print("Grafo compilado criado com sucesso.")

    # Injenta o grafo compilado no módulo de rotas
    set_compiled_graph(compiled_graph)
    print("Grafo injetado no router da API.")

    # --- Criação da Aplicação FastAPI ---
    app = FastAPI(
        title="Chat Edu API",
        description="API para o chatbot educacional com LangGraph e RAG, processando múltiplos PDFs.",
        version="1.2.1",
    )

    # --- Middlewares ---
    print(f"Configurando CORS para permitir origens: {ALLOWED_ORIGINS}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Inclusão dos Routers da API ---
    app.include_router(chat_router, prefix="/chat") 
    app.include_router(auth_router, prefix="/login", tags=["Authentication"])
    print("Router da API de Chat incluído em /chat.")
    print("Router de autenticação incluído em /login.")

    print("--- Aplicação Pronta para Iniciar ---")

# Captura erros GERAIS durante a inicialização
except Exception as e:
     print(f"\n !!! ERRO CRÍTICO DURANTE A INICIALIZAÇÃO !!!")
     print(f"Erro: {e}")
     traceback.print_exc()
     print("Aplicação não pode ser iniciada.")
     exit(1)


# --- Ponto de Execução ---
if __name__ == "__main__":
    print("Iniciando servidor Uvicorn...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
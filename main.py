# main.py
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os # Importar os para acessar variáveis de ambiente se necessário
import traceback # Para log de erros

# Importa configurações e serviços
# Ainda precisamos das outras configurações de settings
try:
    from config.settings import settings
except Exception as config_error:
    # Se até o settings falhar, define valores padrão aqui ou para
    print(f"\n !!! ERRO CRÍTICO AO CARREGAR settings.py !!!")
    print(f"Erro: {config_error}")
    traceback.print_exc()
    print("Usando valores padrão ou abortando. Verifique config/settings.py e .env")
    # Você pode definir valores padrão aqui se quiser continuar,
    # mas é mais seguro parar se a configuração base falhar.
    # Ex: settings = type('obj', (object,), {'qdrant_mode': 'memory', 'pdf_path': None})() # Mock simples
    exit(1) # Aborta se a configuração essencial falhar

from services.embedding_service import EmbeddingService
from services.vector_store_service import VectorStoreService
from services.llm_service import LLMService
from services.document_service import load_and_split_pdf # Para ingestão in-memory

# Importa o criador do grafo e o router da API
from core.graph import create_compiled_graph
from api.routes import router as chat_router, set_compiled_graph # Importa o router e a função de setup

# --- Define as origens CORS diretamente aqui ---
# Edite esta lista conforme necessário para seu ambiente de frontend
ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Origem comum do frontend React em desenvolvimento
    "http://127.0.0.1:3000", # Outra forma de acessar localhost
    # Adicione outras origens se necessário (ex: URL de produção do frontend)
]
# Alternativa (MENOS SEGURO - permite qualquer origem):
# ALLOWED_ORIGINS = ["*"]


# --- Inicialização dos Serviços ---
print("--- Inicializando Aplicação Chat Edu ---")
try:
    # Verifica se o PDF_PATH essencial existe
    if not settings.pdf_dir or not os.path.exists(os.path.abspath(settings.pdf_dir)):
         raise FileNotFoundError(f"Caminho do PDF (PDF_PATH='{settings.pdf_dir}') inválido ou arquivo não encontrado. Verifique .env.")

    embedding_service = EmbeddingService()
    vector_size = embedding_service.get_embedding_dimension()

    vector_store_service = VectorStoreService(vector_size=vector_size)

    llm_service = LLMService()

    # --- Ingestão de Dados (Apenas se Qdrant for in-memory) ---
    # Para produção com Qdrant persistente, use o script ingest_data.py separadamente!
    if settings.qdrant_mode == 'memory':
        print("\n--- Iniciando Ingestão In-Memory (Apenas para Desenvolvimento) ---")
        # Usa o pdf_path validado das settings
        documents = load_and_split_pdf(settings.pdf_dir)
        if documents:
            doc_contents = [doc.page_content for doc in documents]
            embeddings = embedding_service.embed_texts(doc_contents)
            if embeddings and len(embeddings) == len(documents):
                vector_store_service.upsert_documents(documents, embeddings)
            else:
                print("Aviso: Falha na geração de embeddings para ingestão in-memory.")
        else:
            print("Aviso: Nenhum documento encontrado ou processado para ingestão in-memory.")
        print("--- Ingestão In-Memory Concluída ---\n")
    else:
         print(f"Modo Qdrant '{settings.qdrant_mode}'. Certifique-se de que os dados foram ingeridos (ex: via 'ingest_data.py').")


    # --- Criação do Grafo Compilado ---
    compiled_graph = create_compiled_graph(
        embedding_service=embedding_service,
        vector_store_service=vector_store_service,
        llm_service=llm_service
    )

    # Injenta o grafo compilado no módulo de rotas
    set_compiled_graph(compiled_graph)

    # --- Criação da Aplicação FastAPI ---
    app = FastAPI(
        title="Chat Edu API",
        description="API para o chatbot educacional com LangGraph e RAG.",
        version="1.1.1", # Incrementa a versão (opcional)
        # openapi_url="/api/v1/openapi.json", # Opcional: customizar URL da documentação
        # docs_url="/docs" # Opcional: customizar URL da documentação interativa
    )

    # --- Middlewares ---
    print(f"Configurando CORS para permitir origens: {ALLOWED_ORIGINS}") # Mostra as origens usadas
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS, # <<< USA A LISTA DEFINIDA ACIMA
        allow_credentials=True,        # Permite credenciais (cookies, auth headers)
        allow_methods=["*"],           # Permite todos os métodos HTTP (GET, POST, etc.)
        allow_headers=["*"],           # Permite todos os cabeçalhos HTTP
    )
    # Removido: print(f"CORS configurado para origens: {settings.CORS_ALLOWED_ORIGINS}")

    # --- Inclusão dos Routers da API ---
    app.include_router(chat_router) # Inclui as rotas definidas em api/routes.py
    print("Router da API de Chat incluído em /chat.")

    print("--- Aplicação Pronta para Iniciar ---")

# Captura erros GERAIS durante a inicialização (fora do try/except específico do settings)
except Exception as e:
     # Captura erros críticos durante a inicialização dos serviços, grafo, etc.
     print(f"\n !!! ERRO CRÍTICO DURANTE A INICIALIZAÇÃO !!!")
     print(f"Erro: {e}")
     traceback.print_exc() # Loga o traceback completo do erro
     print("Aplicação não pode ser iniciada.")
     exit(1) # Termina o script


# --- Ponto de Execução (para rodar com 'python main.py') ---
if __name__ == "__main__":
    print("Iniciando servidor Uvicorn...")
    # Configurações do Uvicorn
    uvicorn.run(
        "main:app",         # Módulo:Variável_App (main.py : app)
        host="0.0.0.0",     # Escuta em todas as interfaces de rede disponíveis
        port=8000,          # Porta padrão
        reload=True,        # Ativa auto-reload (ótimo para desenvolvimento, remova em produção)
        log_level="info"    # Nível de log do servidor (pode ser 'debug' para mais detalhes)
    )
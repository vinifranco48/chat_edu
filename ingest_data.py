# ingest_data.py
import time
from config.settings import settings
from services.document_service import load_and_split_pdf
from services.embedding_service import EmbeddingService
from services.vector_store_service import VectorStoreService

def run_ingestion():
    """Executa o processo completo de ingestão de dados."""
    print("--- Iniciando Processo de Ingestão ---")
    start_time = time.time()

    # 1. Carregar e dividir documentos
    print(f"Carregando documentos de: {settings.pdf_path}")
    documents = load_and_split_pdf(settings.pdf_path)
    if not documents:
        print("Nenhum documento para processar. Encerrando ingestão.")
        return

    # 2. Inicializar serviço de embedding (para obter a dimensão)
    try:
        embedding_service = EmbeddingService()
        vector_size = embedding_service.get_embedding_dimension()
    except Exception as e:
         print(f"Erro crítico ao inicializar serviço de embedding: {e}. Abortando ingestão.")
         return

    # 3. Gerar embeddings
    doc_contents = [doc.page_content for doc in documents]
    embeddings = embedding_service.embed_texts(doc_contents)
    if not embeddings or len(embeddings) != len(documents):
        print("Falha ao gerar embeddings ou contagem incompatível. Abortando ingestão.")
        return

    # 4. Inicializar serviço de vector store (agora com o vector_size)
    try:
        vector_store_service = VectorStoreService(vector_size=vector_size)
    except Exception as e:
         print(f"Erro crítico ao inicializar serviço de vector store: {e}. Abortando ingestão.")
         return

    # 5. Inserir no vector store
    success = vector_store_service.upsert_documents(documents, embeddings)

    end_time = time.time()
    duration = end_time - start_time

    if success:
        print(f"--- Ingestão Concluída com Sucesso em {duration:.2f} segundos ---")
    else:
        print(f"--- Ingestão Falhou após {duration:.2f} segundos ---")

if __name__ == "__main__":
    run_ingestion()
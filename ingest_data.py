# ingest_data.py
import time
from config.settings import settings
from services.document_service import load_and_split_pdf
from services.embedding_service import EmbeddingService
from services.vector_store_service import VectorStoreService
import os
from pathlib import Path

def run_ingestion(): # Ou a lógica dentro do if settings.qdrant_mode == 'memory':
    """Executa o processo de ingestão para TODOS os PDFs em PDF_DIR."""
    print("--- Iniciando Processo de Ingestão de Múltiplos PDFs ---")
    start_time = time.time()

    pdf_directory = Path(os.path.abspath(settings.pdf_dir)) # Usa pathlib para robustez
    if not pdf_directory.is_dir():
        print(f"Erro Crítico: Diretório PDF '{pdf_directory}' não encontrado. Abortando ingestão.")
        return

    all_documents = [] # Lista para guardar chunks de TODOS os PDFs
    pdf_files_found = list(pdf_directory.glob("*.pdf")) # Encontra todos os .pdf no diretório

    if not pdf_files_found:
        print(f"Aviso: Nenhum arquivo PDF encontrado em '{pdf_directory}'.")
        # Decide se quer continuar ou parar. Vamos parar por enquanto.
        return

    print(f"Encontrados {len(pdf_files_found)} arquivos PDF para processar:")
    for pdf_path in pdf_files_found:
        print(f"  - {pdf_path.name}")

    # 1. Carregar e dividir TODOS os documentos
    print("\nCarregando e dividindo documentos...")
    for pdf_path in pdf_files_found:
        print(f"Processando: {pdf_path.name}...")
        # A função load_and_split_pdf já existe e recebe um caminho
        # Ela deve adicionar o 'source' correto nos metadados automaticamente
        documents_from_single_pdf = load_and_split_pdf(str(pdf_path)) # Converte Path para string
        if documents_from_single_pdf:
            all_documents.extend(documents_from_single_pdf) # Adiciona os chunks à lista geral
            print(f"  -> {len(documents_from_single_pdf)} chunks adicionados.")
        else:
            print(f"  -> Aviso: Nenhum chunk gerado para {pdf_path.name}.")

    if not all_documents:
        print("Nenhum documento válido gerado após processar todos os PDFs. Encerrando ingestão.")
        return
    print(f"\nTotal de chunks de todos os PDFs: {len(all_documents)}")

    # 2. Inicializar serviço de embedding (como antes)
    try:
        embedding_service = EmbeddingService()
        vector_size = embedding_service.get_embedding_dimension()
    except Exception as e:
         print(f"Erro crítico ao inicializar serviço de embedding: {e}. Abortando.")
         return

    # 3. Gerar embeddings para TODOS os chunks de uma vez (mais eficiente)
    print("\nGerando embeddings para todos os chunks...")
    # Extrai o conteúdo textual de todos os documentos carregados
    all_doc_contents = [doc.page_content for doc in all_documents]
    all_embeddings = embedding_service.embed_texts(all_doc_contents)

    if not all_embeddings or len(all_embeddings) != len(all_documents):
        print("Falha ao gerar embeddings ou contagem incompatível. Abortando ingestão.")
        return
    print(f"Total de embeddings gerados: {len(all_embeddings)}")

    # 4. Inicializar serviço de vector store (como antes)
    try:
        vector_store_service = VectorStoreService(vector_size=vector_size)
        # IMPORTANTE: Certifique-se que _setup_collection NÃO APAGUE dados
        # se estiver usando Qdrant persistente (modo url). Idealmente,
        # ela deve criar a coleção APENAS se não existir. A versão com
        # recreate_collection apagará tudo a cada ingestão.
        print(f"AVISO: Verifique se a lógica de setup da coleção no VectorStoreService é segura para múltiplas ingestões (não use recreate_collection indiscriminadamente no modo 'url').")

    except Exception as e:
         print(f"Erro crítico ao inicializar serviço de vector store: {e}. Abortando.")
         return

    # 5. Inserir TODOS os chunks e embeddings no vector store de uma vez
    print("\nInserindo/Atualizando todos os pontos no Qdrant...")
    success = vector_store_service.upsert_documents(all_documents, all_embeddings)

    end_time = time.time()
    duration = end_time - start_time

    if success:
        print(f"--- Ingestão de {len(pdf_files_found)} PDFs ({len(all_documents)} chunks) Concluída com Sucesso em {duration:.2f} segundos ---")
    else:
        print(f"--- Ingestão Falhou após {duration:.2f} segundos ---")

# Se este código estiver em ingest_data.py, adicione:
if __name__ == "__main__":
    run_ingestion()
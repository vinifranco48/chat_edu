# ingest_data.py
import time
import os
import re  # Para extrair o ID da pasta com regex
import traceback
from pathlib import Path

# Importações dos seus módulos e serviços
from config.settings import settings
from services.document_service import load_and_split_pdf
from services.embedding_service import EmbeddingService
# Importe o VectorStoreService atualizado (que espera id_course no upsert)
from services.vector_store_service import VectorStoreService
# Se VectorStoreService ainda espera name_course, você pode passar None ou ""
# ou ajustar a chamada abaixo e a definição no VectorStoreService.

def run_ingestion():
    """
    Executa o processo de ingestão completo.
    Itera sobre as subpastas no diretório PDF_DIR, extrai o course_id
    do nome da pasta (ex: 'Curso-4592' -> '4592'), processa os PDFs
    dentro de cada pasta e insere os chunks e embeddings no Qdrant
    com o 'course_id' correto no payload.
    """
    print("--- Iniciando Processo de Ingestão por Curso (ID da Pasta) ---")
    start_time_total = time.time()

    # --- 1. Configuração Inicial e Validação do Diretório Base ---
    try:
        base_pdf_directory = Path(os.path.abspath(settings.pdf_dir))
        if not base_pdf_directory.is_dir():
            print(f"Erro Crítico: Diretório base de PDFs '{base_pdf_directory}' não encontrado. Abortando.")
            return
    except Exception as e:
        print(f"Erro ao acessar o diretório base de PDFs definido nas configurações: {e}")
        return

    # --- 2. Inicialização dos Serviços ---
    try:
        print("Inicializando serviços...")
        embedding_service = EmbeddingService()
        vector_size = embedding_service.get_embedding_dimension()
        vector_store_service = VectorStoreService(vector_size=vector_size)
        vector_store_service._setup_collection()
        print("Serviços inicializados com sucesso.")
    except Exception as e:
        print(f"Erro crítico ao inicializar serviços: {e}. Abortando.")
        traceback.print_exc()
        return

    # --- 3. Processamento por Pasta de Curso ---
    total_pdfs_processed = 0
    total_chunks_ingested = 0
    courses_processed_count = 0
    courses_failed = [] # Lista para rastrear IDs de cursos com falha

    print(f"\nProcurando por pastas de cursos em: {base_pdf_directory}")

    # Iterar sobre todos os itens no diretório base
    items_in_base_dir = list(base_pdf_directory.iterdir())
    if not items_in_base_dir:
        print("Aviso: Diretório base de PDFs está vazio.")
        return

    course_folders_found = [item for item in items_in_base_dir if item.is_dir()]
    if not course_folders_found:
         print("Aviso: Nenhuma subpasta encontrada no diretório base para processar como curso.")
         return

    print(f"Encontradas {len(course_folders_found)} subpastas. Iniciando processamento...")

    for course_dir_path in course_folders_found:
        folder_name = course_dir_path.name # Ex: "Curso-4592"

        # Tentar extrair o ID numérico do final do nome da pasta
        match = re.search(r'\d+$', folder_name)
        if match:
            course_id = match.group(0) # Ex: "4592"
            print(f"\n--- Processando Pasta: {folder_name} | ID Extraído: {course_id} ---")
        else:
            print(f"\nAviso: Não foi possível extrair um ID numérico do nome da pasta '{folder_name}'. Pulando esta pasta.")
            continue # Pula para a próxima pasta

        start_time_course = time.time()

        # Listar PDFs DENTRO da pasta do curso atual
        try:
            pdf_files_in_course = list(course_dir_path.glob("*.pdf"))
            if not pdf_files_in_course:
                print(f"Nenhum arquivo PDF encontrado em '{course_dir_path}'. Pulando para o próximo curso.")
                continue
            print(f"Encontrados {len(pdf_files_in_course)} PDFs para o curso {course_id}.")
        except Exception as e:
            print(f"Erro ao listar PDFs na pasta '{course_dir_path}': {e}. Pulando este curso.")
            courses_failed.append(course_id)
            continue

        # --- 3.1 Carregar e Dividir Documentos do Curso Atual ---
        course_documents = [] # Lista para guardar chunks DESTE curso
        print("Carregando e dividindo documentos do curso...")
        pdf_processing_failed = False
        for pdf_path in pdf_files_in_course:
            print(f"  Processando: {pdf_path.name}...")
            try:
                # Certifique-se que load_and_split_pdf aceita string ou Path
                documents_from_single_pdf = load_and_split_pdf(str(pdf_path))
                if documents_from_single_pdf:
                    course_documents.extend(documents_from_single_pdf)
                    print(f"    -> {len(documents_from_single_pdf)} chunks adicionados.")
                else:
                    print(f"    -> Aviso: Nenhum chunk gerado para {pdf_path.name}.")
            except Exception as e:
                 print(f"    -> ERRO CRÍTICO ao processar {pdf_path.name}: {e}")
                 traceback.print_exc()
                 # Decide se quer parar o curso ou apenas pular o arquivo
                 # Aqui, vamos marcar que houve falha neste curso e continuar com os outros PDFs se possível
                 pdf_processing_failed = True
                 # break # Descomente para parar de processar PDFs deste curso no primeiro erro

        if not course_documents:
            print("Nenhum chunk válido gerado para este curso após processar os PDFs. Pulando ingestão para este curso.")
            if pdf_processing_failed: courses_failed.append(course_id) # Marcar falha se erro ocorreu
            continue # Pula para o próximo curso

        print(f"Total de chunks para o curso {course_id}: {len(course_documents)}")

        # --- 3.2 Gerar Embeddings para os Chunks do Curso Atual ---
        print("Gerando embeddings para os chunks do curso...")
        try:
            # Extrai o conteúdo textual para o serviço de embedding
            course_doc_contents = [doc.page_content for doc in course_documents]
            course_embeddings = embedding_service.embed_texts(course_doc_contents)

            # Validação importante
            if not course_embeddings or len(course_embeddings) != len(course_documents):
                print("Erro: Falha ao gerar embeddings ou contagem incompatível com chunks. Pulando ingestão para este curso.")
                courses_failed.append(course_id)
                continue
            print(f"Embeddings gerados para o curso: {len(course_embeddings)}")

        except Exception as e:
            print(f"Erro CRÍTICO ao gerar embeddings para o curso {course_id}: {e}. Pulando ingestão.")
            traceback.print_exc()
            courses_failed.append(course_id)
            continue

        # --- 3.3 Inserir Chunks e Embeddings no Qdrant com Metadados ---
        print(f"Inserindo/Atualizando {len(course_documents)} pontos no Qdrant para o curso {course_id}...")
        try:
            # Chamada para o método upsert, passando o ID do curso extraído
            # Certifique-se que a assinatura do método em VectorStoreService corresponde
            # (removido name_course se você decidiu omiti-lo)
            success = vector_store_service.upsert_documents(
                documents=course_documents,
                embeddings=course_embeddings,
                id_course=course_id
                # batch_size=100 # Pode adicionar se o método aceitar
            )
        except Exception as e:
             print(f"Erro CRÍTICO durante chamada ao upsert_documents para o curso {course_id}: {e}")
             traceback.print_exc()
             success = False # Marcar como falha

        end_time_course = time.time()
        duration_course = end_time_course - start_time_course

        if success:
            print(f"--- Ingestão para o curso {course_id} Concluída com Sucesso em {duration_course:.2f} segundos ---")
            total_pdfs_processed += len(pdf_files_in_course)
            total_chunks_ingested += len(course_documents)
            courses_processed_count += 1
        else:
            print(f"--- Ingestão para o curso {course_id} Falhou após {duration_course:.2f} segundos ---")
            courses_failed.append(course_id) # Adiciona ID à lista de falhas

    # --- 4. Resumo Final da Ingestão ---
    end_time_total = time.time()
    duration_total = end_time_total - start_time_total
    print("\n--- Resumo Geral da Ingestão ---")
    print(f"Tempo total de execução: {duration_total:.2f} segundos")
    print(f"Total de Pastas de Curso Processadas com Sucesso: {courses_processed_count}")
    print(f"Total de Arquivos PDF Lidos: {total_pdfs_processed}")
    print(f"Total de Chunks Ingeridos/Atualizados no Qdrant: {total_chunks_ingested}")
    if courses_failed:
        # Usar set para mostrar IDs únicos que falharam
        unique_failed_courses = sorted(list(set(courses_failed)))
        print(f"Cursos com Falha em alguma etapa: {', '.join(unique_failed_courses)}")
    else:
         print("Todos os cursos foram processados sem erros críticos reportados.")
    print("--- Fim do Processo de Ingestão ---")

# --- Ponto de Entrada Principal ---
if __name__ == "__main__":
    run_ingestion()
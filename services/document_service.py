import os
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from config.settings import settings

def load_and_split_pdf(file_path:str) -> List[Document]:
    """Carrega e divide um pdf em chunks."""
    if not file_path or not os.path.exists(file_path):
        print(f"Erro: Arquivo {file_path} não encontrado.")
        return []
    
    print(f"Carregando arquivo: {file_path}")
    try:
        loader = PyPDFLoader(file_path)
        docs_loaded = loader.load()
        if not docs_loaded:
            print(f"Aviso: Nenhum documento carregado do arquivo {file_path}.")
            return []
        text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ". ", " ", ""], # Prioriza separadores maiores
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        split_docs = text_splitter.split_documents(docs_loaded)
        print(f"Documento dividido em {len(split_docs)} chunks.")
        return split_docs
    except Exception as e:
        print(f"Erro ao carregar ou dividir o PDF '{file_path}': {e}")
        return []
        

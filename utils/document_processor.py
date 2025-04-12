from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def file_to_documents(file_path: str):
    """Carrega e divide o documento em chunks usando parâmetros otimizados"""
    loader = PyPDFLoader(file_path)
    doc = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n", "\n\n", " "],
        chunk_size=600,
        chunk_overlap=50,
        length_function=len,
        is_separator_regex=False,
    )
    texts = text_splitter.split_documents(doc)
    return texts

# Manter por compatibilidade, mas usando a nova implementação
def load_and_split_documents(file_path):
    """Wrapper para manter compatibilidade com código existente"""
    return file_to_documents(file_path)

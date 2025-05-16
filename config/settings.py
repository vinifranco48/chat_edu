# config/settings.py (VERSÃO SIMPLIFICADA - SEM CORS)
import os
from typing import List, Optional, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, ValidationInfo
import traceback

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    # --- Chaves de API e Configs Essenciais ---
    groq_api_key: str = Field(..., validation_alias='GROQ_API_KEY')
    embedding_model_name: str = Field(
        "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        validation_alias='EMBEDDING_MODEL_NAME'
    )
    llm_model_name: str = Field(
        "meta-llama/llama-4-maverick-17b-128e-instruct",
        validation_alias='LLM_MODEL_NAME'
    )
    pdf_dir: str = Field("./data/", validation_alias='PDF_DIR')

    # --- Configurações do Qdrant ---
    qdrant_mode: str = Field("url", validation_alias='QDRANT_MODE')
    qdrant_url: Optional[str] = Field(None, validation_alias='QDRANT_URL')
    qdrant_api_key: Optional[str] = Field(None, validation_alias='QDRANT_API_KEY')
    qdrant_collection_name: str = Field("chat-edu", validation_alias='QDRANT_COLLECTION_NAME')

    # --- Configurações de Processamento de Documentos ---
    chunk_size: int = Field(2000, validation_alias='CHUNK_SIZE')
    chunk_overlap: int = Field(200, validation_alias='CHUNK_OVERLAP')


    # --- Configurações do Grafo ---
    retrieval_limit: int = Field(10, validation_alias='RETRIEVAL_LIMIT')

    # --- Cache para embeddings ---
    embedding_cache_dir: str = Field("embedding_cache", validation_alias="EMBEDDING_CACHE_DIR")

    # --- Validadores Adicionais ---
    @field_validator('qdrant_url')
    @classmethod
    def _check_qdrant_url(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
         if info.data.get('qdrant_mode') == 'url' and not v:
              raise ValueError("A variável de ambiente QDRANT_URL é obrigatória quando QDRANT_MODE é 'url'")
         return v

# --- Instanciação das Configurações ---
try:
    # Esta linha agora não deve mais ter problemas com CORS
    settings = Settings()
    print("Instância 'settings' criada com sucesso em config/settings.py (sem CORS).")
except Exception as e:
    print(f"Erro crítico ao INSTANCIAR Settings em config/settings.py:")
    print(f"Erro: {e}")
    traceback.print_exc()
    print("Verifique seu arquivo .env e a LÓGICA dentro de config/settings.py.")
    exit(1) # Aborta a execução do programa
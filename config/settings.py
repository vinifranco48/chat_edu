# config/settings.py

import os
import traceback
from typing import Optional
from pydantic import Field, field_validator, ValidationInfo, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Centraliza todas as configurações da aplicação, lendo de um arquivo .env.
    """
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore' # Ignora variáveis de ambiente extras que não estão definidas aqui
    )

    # --- Chaves de API e Configs de Modelos ---
    groq_api_key: str = Field(..., validation_alias='GROQ_API_KEY')
    embedding_model_name: str = Field(
        "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        validation_alias='EMBEDDING_MODEL_NAME'
    )
    llm_model_name: str = Field(
        "llama3-8b-8192", # Modelo padrão do Groq, pode ser sobrescrito pelo .env
        validation_alias='LLM_MODEL_NAME'
    )

    # --- Configurações do Qdrant ---
    qdrant_mode: str = Field("url", validation_alias='QDRANT_MODE')
    qdrant_url: Optional[str] = Field(None, validation_alias='QDRANT_URL')
    qdrant_api_key: Optional[str] = Field(None, validation_alias='QDRANT_API_KEY')
    qdrant_collection_name: str = Field("chat-edu", validation_alias='QDRANT_COLLECTION_NAME')

    # --- Configurações do Banco de Dados PostgreSQL (NOVO) ---
    postgres_user: str = Field(..., validation_alias='POSTGRES_USER')
    postgres_password: str = Field(..., validation_alias='POSTGRES_PASSWORD')
    postgres_host: str = Field(..., validation_alias='POSTGRES_HOST')
    postgres_port: int = Field(5432, validation_alias='POSTGRES_PORT')
    postgres_db: str = Field(..., validation_alias='POSTGRES_DB')

    @property
    def database_url(self) -> PostgresDsn:
        """ Gera a URL de conexão do banco de dados a partir das configurações. """
        return f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    # --- Configurações de Processamento de Documentos ---
    pdf_dir: str = Field("/app/data", validation_alias='PDF_DIR') # Caminho dentro do contêiner
    chunk_size: int = Field(2000, validation_alias='CHUNK_SIZE')
    chunk_overlap: int = Field(200, validation_alias='CHUNK_OVERLAP')

    # --- Configurações do Grafo e Recuperação ---
    retrieval_limit: int = Field(10, validation_alias='RETRIEVAL_LIMIT')

    # --- Cache para embeddings ---
    embedding_cache_dir: str = Field("/app/embedding_cache", validation_alias="EMBEDDING_CACHE_DIR")

    # --- Validadores ---
    @field_validator('qdrant_url')
    @classmethod
    def _check_qdrant_url(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        # Validador para garantir que a URL do Qdrant exista se o modo for 'url'
        if info.data.get('qdrant_mode') == 'url' and not v:
            raise ValueError("A variável de ambiente QDRANT_URL é obrigatória quando QDRANT_MODE é 'url'")
        return v

# --- Instanciação Singleton das Configurações ---
try:
    settings = Settings()
    print("✅ Configurações (settings) carregadas com sucesso!")
except Exception as e:
    print(f"❌ Erro crítico ao carregar as configurações de 'config/settings.py':")
    print(f"   Erro: {e}")
    traceback.print_exc()
    print("   Por favor, verifique se o seu arquivo .env contém todas as variáveis necessárias.")
    exit(1)
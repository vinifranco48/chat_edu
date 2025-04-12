# api/models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional # Garanta que Optional esteja importado se usar

class QueryRequest(BaseModel):
    """Modelo para a requisição da consulta do usuário."""
    text: str = Field(..., min_length=1, description="Texto da consulta do usuário")

class SourceInfo(BaseModel): # Renomeado de retrieved_docs para clareza no uso
    """Modelo para informações de uma fonte recuperada."""
    source: str = Field(description="Nome ou caminho do arquivo fonte")
    page: int = Field(description="Número da página")

class QueryResponse(BaseModel):
    """Modelo para a resposta da API ao usuário."""
    # --- CORRIGIDO ---
    # Tipo agora é opcional (str | None) e o default é None, tornando o campo não obrigatório.
    response: str | None = Field(None, description="Resposta textual gerada pelo chatbot")
    # --- FIM DA CORREÇÃO ---

    # Melhoria: Usar default_factory para listas
    retrieved_sources: List[SourceInfo] = Field(default_factory=list, description="Lista de fontes consultadas para gerar a resposta") # Nome atualizado

    # Já estava correto (opcional com default None)
    error: str | None = Field(None, description="Mensagem de erro detalhada, se ocorrido")
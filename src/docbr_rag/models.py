"""
Modelos de dados do docbr-rag.
Define as estruturas de entrada e saída com validação via Pydantic.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class TipoDocumento(str, Enum):
    """Tipos de documentos brasileiros suportados."""
    CONTRATO = "contrato"
    NFE = "nfe"
    BOLETO = "boleto"
    LAUDO = "laudo"
    CERTIDAO = "certidao"
    HOLERITE = "holerite"
    DESCONHECIDO = "desconhecido"


class Chunk(BaseModel):
    """Fragmento de texto extraído do documento."""
    texto: str
    pagina: int
    indice: int
    metadata: dict = Field(default_factory=dict)


class Resposta(BaseModel):
    """Resposta gerada pelo RAG."""
    texto: str
    fonte: Optional[str] = None
    paginas_referenciadas: list[int] = Field(default_factory=list)
    confianca: Optional[float] = None

    def __str__(self) -> str:
        return self.texto


class DocumentoInfo(BaseModel):
    """Informações extraídas de um documento brasileiro."""
    tipo: TipoDocumento
    caminho: str
    total_paginas: int
    total_chunks: int
    campos: dict = Field(default_factory=dict)
    indexado: bool = False

    class Config:
        use_enum_values = True

"""
docbr-rag — RAG especializado em documentos brasileiros.
100% local, gratuito e open source.
"""

from src.docbr_rag.core import DocBR
from src.docbr_rag.models import Resposta, DocumentoInfo, TipoDocumento

__version__ = "0.1.0"
__all__ = ["DocBR", "Resposta", "DocumentoInfo", "TipoDocumento"]

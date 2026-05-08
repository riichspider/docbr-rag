from docbr_rag.extractors.pdf import (
    extrair_texto_pdf, criar_chunks, detectar_tipo
)
from docbr_rag.extractors.docx import (
    extrair_texto_docx, detectar_tipo_docx, extrair_metadados_docx, extrair_tabelas_docx
)
from docbr_rag.extractors.txt import (
    extrair_texto_txt, detectar_tipo_txt, extrair_metadados_txt
)

__all__ = [
    "extrair_texto_pdf", "criar_chunks", "detectar_tipo",
    "extrair_texto_docx", "detectar_tipo_docx", "extrair_metadados_docx", "extrair_tabelas_docx",
    "extrair_texto_txt", "detectar_tipo_txt", "extrair_metadados_txt"
]

"""
Extrator de texto de documentos PDF brasileiros.
Usa pdfplumber como principal e pymupdf como fallback.
"""

import re
from pathlib import Path
from typing import Optional
import pdfplumber
from ..models import Chunk, TipoDocumento


# Padrões que identificam tipos de documentos brasileiros
_PADROES_TIPO = {
    TipoDocumento.NFE: [
        r"NOTA FISCAL ELETR[ÔO]NICA",
        r"NF-?e",
        r"CHAVE DE ACESSO",
        r"DANFE",
    ],
    TipoDocumento.BOLETO: [
        r"BOLETO",
        r"BANCO\s+\w+\s+S\.?A\.?",
        r"C[ÓO]DIGO DE BARRAS",
        r"NOSSO N[ÚU]MERO",
        r"VENCIMENTO",
    ],
    TipoDocumento.CONTRATO: [
        r"CONTRATO\s+(DE|SOCIAL|PARTICULAR|DE PRESTA)",
        r"CONTRATANTE",
        r"CONTRATADO",
        r"CL[ÁA]USULA",
        r"FORO",
    ],
    TipoDocumento.LAUDO: [
        r"LAUDO\s+(T[ÉE]CNICO|M[ÉE]DICO|PERICIAL)",
        r"PERITO",
        r"CONCLUS[ÃA]O",
        r"OBJETO DA PER[ÍI]CIA",
    ],
    TipoDocumento.CERTIDAO: [
        r"CERTID[ÃA]O",
        r"CERTIFIC[OA]",
        r"REGISTRO CIVIL",
        r"CART[ÓO]RIO",
    ],
    TipoDocumento.HOLERITE: [
        r"HOLERITE",
        r"CONTRACHEQUE",
        r"RECIBO DE PAGAMENTO",
        r"INSS",
        r"FGTS",
        r"SALÁRIO BASE",
    ],
}


def detectar_tipo(texto: str) -> TipoDocumento:
    """
    Detecta o tipo de documento brasileiro com base no conteúdo.

    Args:
        texto: Texto extraído do documento

    Returns:
        TipoDocumento identificado ou DESCONHECIDO
    """
    texto_upper = texto.upper()
    pontuacao = {tipo: 0 for tipo in TipoDocumento}

    for tipo, padroes in _PADROES_TIPO.items():
        for padrao in padroes:
            if re.search(padrao, texto_upper):
                pontuacao[tipo] += 1

    melhor_tipo = max(pontuacao, key=pontuacao.get)
    if pontuacao[melhor_tipo] == 0:
        return TipoDocumento.DESCONHECIDO

    return melhor_tipo


def extrair_texto_pdf(caminho: str | Path) -> list[tuple[int, str]]:
    """
    Extrai texto de cada página do PDF.

    Args:
        caminho: Caminho para o arquivo PDF

    Returns:
        Lista de tuplas (numero_pagina, texto)
    """
    caminho = Path(caminho)
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    if not caminho.suffix.lower() == ".pdf":
        raise ValueError(f"Arquivo deve ser PDF: {caminho}")

    paginas = []

    try:
        with pdfplumber.open(caminho) as pdf:
            for i, pagina in enumerate(pdf.pages, start=1):
                texto = pagina.extract_text() or ""
                texto = _limpar_texto(texto)
                paginas.append((i, texto))
    except Exception as e:
        # Fallback para pymupdf
        try:
            import fitz  # pymupdf
            doc = fitz.open(str(caminho))
            for i, pagina in enumerate(doc, start=1):
                texto = pagina.get_text()
                texto = _limpar_texto(texto)
                paginas.append((i, texto))
            doc.close()
        except Exception:
            raise RuntimeError(f"Não foi possível extrair texto do PDF: {e}")

    return paginas


def criar_chunks(
    paginas: list[tuple[int, str]],
    tamanho_chunk: int = 500,
    sobreposicao: int = 100,
    tipo: Optional[TipoDocumento] = None,
) -> list[Chunk]:
    """
    Divide o texto em chunks otimizados para documentos BR.

    A estratégia de chunking respeita estruturas comuns em documentos
    brasileiros: cláusulas numeradas, artigos, seções com CAPS.

    Args:
        paginas: Lista de (pagina, texto) extraídas do PDF
        tamanho_chunk: Tamanho máximo de cada chunk em caracteres
        sobreposicao: Sobreposição entre chunks consecutivos
        tipo: Tipo do documento (influencia estratégia de chunking)

    Returns:
        Lista de Chunk prontos para indexação
    """
    chunks = []
    indice = 0

    for num_pagina, texto in paginas:
        if not texto.strip():
            continue

        # Divide por separadores naturais de documentos BR
        segmentos = _dividir_por_estrutura(texto, tipo)

        buffer = ""
        for segmento in segmentos:
            if len(buffer) + len(segmento) <= tamanho_chunk:
                buffer += segmento + " "
            else:
                if buffer.strip():
                    chunks.append(Chunk(
                        texto=buffer.strip(),
                        pagina=num_pagina,
                        indice=indice,
                    ))
                    indice += 1
                # Sobreposição: mantém fim do buffer anterior
                overlap = buffer[-sobreposicao:] if len(
                    buffer) > sobreposicao else buffer
                buffer = overlap + segmento + " "

        if buffer.strip():
            chunks.append(Chunk(
                texto=buffer.strip(),
                pagina=num_pagina,
                indice=indice,
            ))
            indice += 1

    return chunks


def _dividir_por_estrutura(texto: str, tipo: Optional[TipoDocumento]) -> list[str]:
    """
    Divide o texto respeitando estruturas de documentos brasileiros.
    Ex: cláusulas de contrato, artigos, seções numeradas.
    """
    # Padrões de separação naturais em documentos BR
    padroes = [
        r"(?=CL[ÁA]USULA\s+\w+)",        # Cláusulas de contrato
        r"(?=ART(?:IGO)?\.?\s+\d+)",       # Artigos
        r"(?=§\s*\d+)",                     # Parágrafos
        r"(?=\d+\.\d+\s+[A-Z])",           # Seções numeradas
        r"(?=\n[A-Z\s]{10,}\n)",           # Títulos em maiúsculas
    ]

    padrao_combinado = "|".join(padroes)
    partes = re.split(padrao_combinado, texto)
    return [p.strip() for p in partes if p.strip()]


def _limpar_texto(texto: str) -> str:
    """Limpa artefatos comuns em PDFs brasileiros."""
    # Remove múltiplos espaços
    texto = re.sub(r" {2,}", " ", texto)
    # Remove múltiplas quebras de linha
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    # Remove hifenização de fim de linha
    texto = re.sub(r"-\n(\w)", r"\1", texto)
    return texto.strip()

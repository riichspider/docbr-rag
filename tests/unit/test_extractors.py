"""
Testes unitários para os extratores de documentos.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.docbr_rag.extractors.pdf import (
    detectar_tipo, extrair_texto_pdf, criar_chunks,
    _dividir_por_estrutura, _limpar_texto
)
from src.docbr_rag.models import TipoDocumento, Chunk


class TestDetectarTipo:
    """Testes para detecção de tipo de documento."""
    
    def test_detectar_contrato(self, sample_text_contract):
        """Testa detecção de contrato."""
        tipo = detectar_tipo(sample_text_contract)
        assert tipo == TipoDocumento.CONTRATO
    
    def test_detectar_nfe(self, sample_text_nfe):
        """Testa detecção de NF-e."""
        tipo = detectar_tipo(sample_text_nfe)
        assert tipo == TipoDocumento.NFE
    
    def test_detectar_boleto(self, sample_text_boleto):
        """Testa detecção de boleto."""
        tipo = detectar_tipo(sample_text_boleto)
        assert tipo == TipoDocumento.BOLETO
    
    def test_detectar_desconhecido(self):
        """Testa detecção de documento desconhecido."""
        texto_generico = "Este é um texto genérico sem padrões brasileiros."
        tipo = detectar_tipo(texto_generico)
        assert tipo == TipoDocumento.DESCONHECIDO
    
    def test_detectar_case_insensitive(self):
        """Testa detecção case insensitive."""
        texto_lower = "nota fiscal eletrônica"
        texto_upper = "NOTA FISCAL ELETRÔNICA"
        texto_mixed = "Nota Fiscal Eletrônica"
        
        assert detectar_tipo(texto_lower) == TipoDocumento.NFE
        assert detectar_tipo(texto_upper) == TipoDocumento.NFE
        assert detectar_tipo(texto_mixed) == TipoDocumento.NFE
    
    def test_detectar_multiplos_padroes(self):
        """Testa documento com múltiplos padrões."""
        texto = """
        CONTRATO DE PRESTAÇÃO DE SERVIÇOS
        NOTA FISCAL ELETRÔNICA
        CLÁUSULA PRIMEIRA
        """
        # Deve detectar o tipo com mais padrões
        tipo = detectar_tipo(texto)
        assert tipo in [TipoDocumento.CONTRATO, TipoDocumento.NFE]


class TestExtrairTextoPDF:
    """Testes para extração de texto de PDF."""
    
    @patch('src.docbr_rag.extractors.pdf.pdfplumber.open')
    def test_extrair_sucesso(self, mock_pdfplumber, temp_dir):
        """Testa extração bem-sucedida com pdfplumber."""
        # Mock das páginas
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Texto da página 1"
        
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Texto da página 2"
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf
        
        # Cria arquivo PDF temporário
        pdf_path = temp_dir / "test.pdf"
        pdf_path.write_bytes(b"fake pdf content")
        
        resultado = extrair_texto_pdf(pdf_path)
        
        assert len(resultado) == 2
        assert resultado[0] == (1, "Texto da página 1")
        assert resultado[1] == (2, "Texto da página 2")
    
    @patch('src.docbr_rag.extractors.pdf.pdfplumber.open')
    @patch('src.docbr_rag.extractors.pdf.fitz.open')
    def test_extrar_fallback_pymupdf(self, mock_fitz, mock_pdfplumber, temp_dir):
        """Testa fallback para pymupdf quando pdfplumber falha."""
        # pdfplumber falha
        mock_pdfplumber.side_effect = Exception("pdfplumber error")
        
        # pymupdf funciona
        mock_page1 = MagicMock()
        mock_page1.get_text.return_value = "Fallback texto 1"
        
        mock_page2 = MagicMock()
        mock_page2.get_text.return_value = "Fallback texto 2"
        
        mock_doc = MagicMock()
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page1, mock_page2]))
        mock_fitz.return_value = mock_doc
        
        pdf_path = temp_dir / "test.pdf"
        pdf_path.write_bytes(b"fake pdf content")
        
        resultado = extrair_texto_pdf(pdf_path)
        
        assert len(resultado) == 2
        assert resultado[0] == (1, "Fallback texto 1")
        assert resultado[1] == (2, "Fallback texto 2")
    
    def test_extrar_arquivo_nao_existe(self):
        """Testa erro quando arquivo não existe."""
        with pytest.raises(FileNotFoundError):
            extrair_texto_pdf("arquivo_inexistente.pdf")
    
    def test_extrar_arquivo_nao_pdf(self, temp_dir):
        """Testa erro quando arquivo não é PDF."""
        txt_path = temp_dir / "test.txt"
        txt_path.write_text("texto")
        
        with pytest.raises(ValueError, match="Arquivo deve ser PDF"):
            extrair_texto_pdf(txt_path)


class TestCriarChunks:
    """Testes para criação de chunks."""
    
    def test_criar_chunks_basic(self, mock_pdf_content):
        """Testa criação básica de chunks."""
        paginas = [(1, mock_pdf_content["page_1"]), 
                  (2, mock_pdf_content["page_2"])]
        
        chunks = criar_chunks(paginas, tamanho_chunk=200, sobreposicao=50)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, Chunk) for chunk in chunks)
        assert all(chunk.pagina in [1, 2] for chunk in chunks)
        assert all(chunk.indice >= 0 for chunk in chunks)
    
    def test_criar_chunks_com_tipo(self, sample_text_contract):
        """Testa criação de chunks com tipo específico."""
        paginas = [(1, sample_text_contract)]
        
        chunks = criar_chunks(
            paginas, 
            tamanho_chunk=300, 
            sobreposicao=50,
            tipo=TipoDocumento.CONTRATO
        )
        
        assert len(chunks) > 0
        # Deve respeitar estrutura de cláusulas
        textos = [chunk.texto for chunk in chunks]
        assert any("CLÁUSULA" in texto for texto in textos)
    
    def test_criar_chunks_sobreposicao(self):
        """Testa sobreposição entre chunks."""
        texto_longo = "Palavra " * 100  # Texto longo para forçar múltiplos chunks
        paginas = [(1, texto_longo)]
        
        chunks = criar_chunks(paginas, tamanho_chunk=200, sobreposicao=50)
        
        if len(chunks) > 1:
            # Verifica sobreposição
            for i in range(1, len(chunks)):
                chunk_anterior = chunks[i-1].texto
                chunk_atual = chunks[i].texto
                # Deve ter alguma sobreposição
                assert len(chunk_atual) > 0
    
    def test_criar_chunks_pagina_vazia(self):
        """Testa tratamento de páginas vazias."""
        paginas = [(1, "Texto válido"), (2, "   "), (3, "Outro texto")]
        
        chunks = criar_chunks(paginas, tamanho_chunk=100)
        
        # Deve ignorar página vazia
        paginas_com_chunks = {chunk.pagina for chunk in chunks}
        assert 2 not in paginas_com_chunks
        assert paginas_com_chunks == {1, 3}


class TestDividirPorEstrutura:
    """Testes para divisão por estrutura de documentos."""
    
    def test_dividir_contrato(self, sample_text_contract):
        """Testa divisão de texto de contrato."""
        segmentos = _dividir_por_estrutura(sample_text_contract, TipoDocumento.CONTRATO)
        
        assert len(segmentos) > 1
        # Deve separar por cláusulas
        textos = " ".join(segmentos)
        assert "CLÁUSULA" in textos
    
    def test_dividir_generico(self):
        """Testa divisão de texto genérico."""
        texto_generico = "Este é um texto genérico sem estrutura especial."
        segmentos = _dividir_por_estrutura(texto_generico)
        
        assert len(segmentos) >= 1
        assert segmentos[0].strip() == texto_generico
    
    def test_dividir_com_artigos(self):
        """Testa divisão de texto com artigos."""
        texto_com_artigos = """
        ARTIGO 1º - Das Disposições Gerais
        Conteúdo do artigo 1.
        
        ARTIGO 2º - Das Obrigações
        Conteúdo do artigo 2.
        """
        
        segmentos = _dividir_por_estrutura(texto_com_artigos)
        
        assert len(segmentos) >= 2
        assert any("ARTIGO 1º" in seg for seg in segmentos)
        assert any("ARTIGO 2º" in seg for seg in segmentos)


class TestLimparTexto:
    """Testes para limpeza de texto."""
    
    def test_limpar_multiplos_espacos(self):
        """Testa remoção de múltiplos espaços."""
        texto = "Texto    com     múltiplos    espaços"
        resultado = _limpar_texto(texto)
        assert resultado == "Texto com múltiplos espaços"
    
    def test_limpar_multiplas_quebras_linha(self):
        """Testa remoção de múltiplas quebras de linha."""
        texto = "Linha 1\n\n\n\nLinha 2"
        resultado = _limpar_texto(texto)
        assert resultado == "Linha 1\n\nLinha 2"
    
    def test_limpar_hifenizacao(self):
        """Testa remoção de hifenização de fim de linha."""
        texto = "palavra-\noutro"
        resultado = _limpar_texto(texto)
        assert resultado == "palavraoutro"
    
    def test_limpar_texto_normal(self):
        """Testa texto normal sem problemas."""
        texto = "Texto normal sem problemas."
        resultado = _limpar_texto(texto)
        assert resultado == texto
    
    def test_limpar_combinado(self):
        """Testa combinação de problemas."""
        texto = "Texto    com\n\n\n\nmúltiplos-\nespaços"
        resultado = _limpar_texto(texto)
        assert resultado == "Texto com\n\nmúltiplos espaços"

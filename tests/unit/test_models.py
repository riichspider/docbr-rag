"""
Testes unitários para os modelos de dados.
"""

import pytest
from pydantic import ValidationError

from src.docbr_rag.models import (
    TipoDocumento, Chunk, Resposta, DocumentoInfo
)


class TestTipoDocumento:
    """Testes para o enum TipoDocumento."""
    
    def test_tipo_documento_values(self):
        """Verifica se todos os tipos esperados existem."""
        expected_types = {
            "contrato", "nfe", "boleto", "laudo", 
            "certidao", "holerite", "desconhecido"
        }
        actual_types = {tipo.value for tipo in TipoDocumento}
        assert actual_types == expected_types
    
    def test_tipo_documento_string_behavior(self):
        """Verifica comportamento de string do enum."""
        tipo = TipoDocumento.CONTRATO
        assert str(tipo) == "contrato"
        assert tipo == "contrato"
        assert tipo != TipoDocumento.NFE


class TestChunk:
    """Testes para o modelo Chunk."""
    
    def test_chunk_creation_valid(self):
        """Testa criação de chunk com dados válidos."""
        chunk = Chunk(
            texto="Texto de exemplo",
            pagina=1,
            indice=0,
            metadata={"tipo": "contrato"}
        )
        
        assert chunk.texto == "Texto de exemplo"
        assert chunk.pagina == 1
        assert chunk.indice == 0
        assert chunk.metadata == {"tipo": "contrato"}
    
    def test_chunk_creation_minimal(self):
        """Testa criação de chunk com dados mínimos."""
        chunk = Chunk(
            texto="Texto mínimo",
            pagina=1,
            indice=0
        )
        
        assert chunk.texto == "Texto mínimo"
        assert chunk.metadata == {}
    
    def test_chunk_validation(self):
        """Testa validação de campos obrigatórios."""
        with pytest.raises(ValidationError):
            Chunk(texto="", pagina=1, indice=0)  # texto vazio
        
        with pytest.raises(ValidationError):
            Chunk(texto="texto", pagina=0, indice=0)  # página inválida
        
        with pytest.raises(ValidationError):
            Chunk(texto="texto", pagina=1, indice=-1)  # índice inválido


class TestResposta:
    """Testes para o modelo Resposta."""
    
    def test_resposta_creation_basic(self):
        """Testa criação de resposta básica."""
        resposta = Resposta(texto="Resposta de exemplo")
        
        assert resposta.texto == "Resposta de exemplo"
        assert resposta.fonte is None
        assert resposta.paginas_referenciadas == []
        assert resposta.confianca is None
    
    def test_resposta_creation_complete(self):
        """Testa criação de resposta completa."""
        resposta = Resposta(
            texto="Resposta completa",
            fonte="Documento X",
            paginas_referenciadas=[1, 2, 3],
            confianca=0.85
        )
        
        assert resposta.texto == "Resposta completa"
        assert resposta.fonte == "Documento X"
        assert resposta.paginas_referenciadas == [1, 2, 3]
        assert resposta.confianca == 0.85
    
    def test_resposta_str_representation(self):
        """Testa representação string da resposta."""
        resposta = Resposta(texto="Teste")
        assert str(resposta) == "Teste"
    
    def test_resposta_validation_confianca(self):
        """Testa validação do campo confiança."""
        # Confiança deve estar entre 0 e 1
        resposta = Resposta(texto="Teste", confianca=0.5)
        assert resposta.confianca == 0.5
        
        # Pydantic não valida range automaticamente, mas podemos testar valores extremos
        resposta = Resposta(texto="Teste", confianca=1.0)
        assert resposta.confianca == 1.0
        
        resposta = Resposta(texto="Teste", confianca=0.0)
        assert resposta.confianca == 0.0


class TestDocumentoInfo:
    """Testes para o modelo DocumentoInfo."""
    
    def test_documento_info_creation(self):
        """Testa criação de informações de documento."""
        doc_info = DocumentoInfo(
            tipo=TipoDocumento.CONTRATO,
            caminho="/path/to/contract.pdf",
            total_paginas=10,
            total_chunks=25,
            campos={"valor": "5000", "vigencia": "12 meses"},
            indexado=True
        )
        
        assert doc_info.tipo == TipoDocumento.CONTRATO
        assert doc_info.caminho == "/path/to/contract.pdf"
        assert doc_info.total_paginas == 10
        assert doc_info.total_chunks == 25
        assert doc_info.campos == {"valor": "5000", "vigencia": "12 meses"}
        assert doc_info.indexado is True
    
    def test_documento_info_defaults(self):
        """Testa valores padrão de DocumentoInfo."""
        doc_info = DocumentoInfo(
            tipo=TipoDocumento.NFE,
            caminho="/path/to/nfe.pdf",
            total_paginas=1,
            total_chunks=5
        )
        
        assert doc_info.campos == {}
        assert doc_info.indexado is False
    
    def test_documento_info_validation(self):
        """Testa validação de campos obrigatórios."""
        with pytest.raises(ValidationError):
            DocumentoInfo(
                tipo=TipoDocumento.CONTRATO,
                caminho="",  # caminho vazio
                total_paginas=0,
                total_chunks=0
            )
        
        with pytest.raises(ValidationError):
            DocumentoInfo(
                tipo=TipoDocumento.CONTRATO,
                caminho="/path/to/file.pdf",
                total_paginas=-1,  # páginas negativas
                total_chunks=0
            )
    
    def test_documento_info_config(self):
        """Testa configuração de enum values."""
        doc_info = DocumentoInfo(
            tipo=TipoDocumento.CONTRATO,
            caminho="/path/to/file.pdf",
            total_paginas=5,
            total_chunks=10
        )
        
        # Verifica se o dict usa valores do enum
        doc_dict = doc_info.model_dump()
        assert doc_dict["tipo"] == "contrato"  # string, não enum

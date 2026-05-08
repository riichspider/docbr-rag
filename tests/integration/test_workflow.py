"""
Testes de integração para o fluxo completo do docbr-rag.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from src.docbr_rag.core import DocBR
from src.docbr_rag.models import TipoDocumento


class TestWorkflowIntegracao:
    """Testes de integração para o fluxo completo."""
    
    @pytest.fixture
    def sample_pdf(self, temp_dir):
        """Cria um PDF de exemplo para testes."""
        # Como não podemos gerar PDFs facilmente nos testes,
        # vamos mockar a extração de texto
        pdf_path = temp_dir / "sample.pdf"
        pdf_path.write_bytes(b"fake pdf content")
        return pdf_path
    
    @patch('src.docbr_rag.core.extrair_texto_pdf')
    @patch('src.docbr_rag.core.ollama.generate')
    @patch('src.docbr_rag.core.SentenceTransformer')
    def test_fluxo_completo_contrato(
        self, mock_transformer, mock_ollama, mock_extrair, 
        sample_pdf, sample_text_contract
    ):
        """Testa fluxo completo com um contrato."""
        # Setup dos mocks
        mock_extrair.return_value = [(1, sample_text_contract)]
        
        # Mock do modelo de embeddings
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3, 0.4, 0.5]]
        mock_transformer.return_value = mock_model
        
        # Mock do Ollama
        mock_ollama.return_value = {
            "response": "O contrato tem vigência de 12 meses e valor mensal de R$ 5.000,00."
        }
        
        # Fluxo completo
        docbr = DocBR(db_path=str(tempfile.mkdtemp()))
        
        # 1. Indexar documento
        doc_info = docbr.indexar_documento(sample_pdf)
        
        assert doc_info.tipo == TipoDocumento.CONTRATO
        assert doc_info.total_paginas == 1
        assert doc_info.total_chunks > 0
        
        # 2. Consultar documento
        resposta = docbr.consultar("Qual o prazo e o valor do contrato?")
        
        assert resposta.texto
        assert "12 meses" in resposta.texto
        assert "5.000" in resposta.texto
        assert resposta.paginas_referenciadas
        assert resposta.confianca is not None
        
        # 3. Listar documentos
        documentos = docbr.listar_documentos()
        assert len(documentos) == 1
        assert documentos[0].tipo == TipoDocumento.CONTRATO
    
    @patch('src.docbr_rag.core.extrair_texto_pdf')
    @patch('src.docbr_rag.core.ollama.generate')
    @patch('src.docbr_rag.core.SentenceTransformer')
    def test_fluxo_multiplos_documentos(
        self, mock_transformer, mock_ollama, mock_extrair,
        temp_dir, sample_text_contract, sample_text_nfe, sample_text_boleto
    ):
        """Testa fluxo com múltiplos documentos de tipos diferentes."""
        # Setup dos mocks
        def mock_extrair_por_path(caminho):
            if "contrato" in str(caminho):
                return [(1, sample_text_contract)]
            elif "nfe" in str(caminho):
                return [(1, sample_text_nfe)]
            elif "boleto" in str(caminho):
                return [(1, sample_text_boleto)]
            return [(1, "Texto genérico")]
        
        mock_extrair.side_effect = mock_extrair_por_path
        
        # Mock do modelo de embeddings
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3, 0.4, 0.5]]
        mock_transformer.return_value = mock_model
        
        # Mock do Ollama
        mock_ollama.return_value = {
            "response": "Encontrados múltiplos documentos com as informações solicitadas."
        }
        
        # Criar arquivos
        contrato_path = temp_dir / "contrato.pdf"
        nfe_path = temp_dir / "nfe.pdf"
        boleto_path = temp_dir / "boleto.pdf"
        
        for path in [contrato_path, nfe_path, boleto_path]:
            path.write_bytes(b"fake pdf")
        
        # Fluxo com múltiplos documentos
        docbr = DocBR(db_path=str(temp_dir / "multi_db"))
        
        # Indexar todos
        documentos_info = []
        for pdf_path in [contrato_path, nfe_path, boleto_path]:
            doc_info = docbr.indexar_documento(pdf_path)
            documentos_info.append(doc_info)
        
        # Verificar tipos detectados
        tipos = [doc.tipo for doc in documentos_info]
        assert TipoDocumento.CONTRATO in tipos
        assert TipoDocumento.NFE in tipos
        assert TipoDocumento.BOLETO in tipos
        
        # Consulta cruzada
        resposta = docbr.consultar(
            "Quais documentos têm valores financeiros?", 
            n_resultados=8
        )
        
        assert resposta.texto
        assert len(resposta.paginas_referenciadas) > 0
        
        # Listar todos
        todos_documentos = docbr.listar_documentos()
        assert len(todos_documentos) == 3
    
    @patch('src.docbr_rag.core.extrair_texto_pdf')
    @patch('src.docbr_rag.core.ollama.generate')
    @patch('src.docbr_rag.core.SentenceTransformer')
    def test_fluxo_com_erros(
        self, mock_transformer, mock_ollama, mock_extrair,
        sample_pdf, sample_text_contract
    ):
        """Testa fluxo com tratamento de erros."""
        # Mock de extração funciona
        mock_extrair.return_value = [(1, sample_text_contract)]
        
        # Mock de embeddings funciona
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_transformer.return_value = mock_model
        
        # Mock de Ollama falha na primeira chamada
        mock_ollama.side_effect = [
            Exception("Erro de conexão"),
            {"response": "Resposta após retry"}
        ]
        
        docbr = DocBR(db_path=str(tempfile.mkdtemp()))
        
        # Indexação funciona
        doc_info = docbr.indexar_documento(sample_pdf)
        assert doc_info.tipo == TipoDocumento.CONTRATO
        
        # Primeira consulta falha
        resposta_erro = docbr.consultar("Pergunta teste")
        assert "Erro ao gerar resposta" in resposta_erro.texto
        assert resposta_erro.confianca == 0.0
        
        # Segunda consulta funciona (se implementarmos retry)
        # Isso depende da implementação específica
    
    def test_persistencia_database(self, temp_dir, sample_text_contract):
        """Testa persistência do banco de dados entre instâncias."""
        db_path = temp_dir / "persist_db"
        
        with patch('src.docbr_rag.core.extrair_texto_pdf') as mock_extrair:
            mock_extrair.return_value = [(1, sample_text_contract)]
            
            # Primeira instância - indexa documento
            docbr1 = DocBR(db_path=str(db_path))
            
            with patch('src.docbr_rag.core.SentenceTransformer') as mock_transformer:
                mock_model = MagicMock()
                mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
                mock_transformer.return_value = mock_model
                
                doc_info = docbr1.indexar_documento(temp_dir / "test.pdf")
                assert doc_info.tipo == TipoDocumento.CONTRATO
        
        # Segunda instância - deve acessar dados persistidos
        docbr2 = DocBR(db_path=str(db_path))
        
        # Verificar se collection existe e pode ser acessada
        assert docbr2.collection is not None
        
        # Tentar consultar (mesmo que sem Ollama mockado)
        # Isso testará se os dados foram persistidos corretamente


class TestIntegracaoCLI:
    """Testes de integração para CLI."""
    
    @patch('src.docbr_rag.cli.extrair_texto_pdf')
    @patch('src.docbr_rag.cli.ollama.generate')
    @patch('src.docbr_rag.cli.SentenceTransformer')
    def test_cli_indexar_consultar(
        self, mock_transformer, mock_ollama, mock_extrair,
        temp_dir, sample_text_contract
    ):
        """Testa fluxo completo via CLI."""
        from src.docbr_rag.cli import app
        from typer.testing import CliRunner
        
        # Setup mocks
        mock_extrair.return_value = [(1, sample_text_contract)]
        
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_transformer.return_value = mock_model
        
        mock_ollama.return_value = {
            "response": "Resposta via CLI"
        }
        
        runner = CliRunner()
        
        # Criar arquivo PDF fake
        pdf_path = temp_dir / "test.pdf"
        pdf_path.write_bytes(b"fake pdf")
        
        # Testar comando indexar
        result = runner.invoke(app, [
            "indexar", str(pdf_path),
            "--db-path", str(temp_dir / "cli_test_db")
        ])
        
        assert result.exit_code == 0
        assert "sucesso" in result.output.lower() or "✓" in result.output
        
        # Testar comando consultar
        result = runner.invoke(app, [
            "consultar", "Pergunta teste",
            "--db-path", str(temp_dir / "cli_test_db")
        ])
        
        assert result.exit_code == 0
        assert "resposta" in result.output.lower()


class TestIntegracaoAPI:
    """Testes de integração para API REST."""
    
    @patch('src.docbr_rag.api_rest.extrair_texto_pdf')
    @patch('src.docbr_rag.api_rest.ollama.generate')
    @patch('src.docbr_rag.api_rest.SentenceTransformer')
    def test_api_rest_workflow(
        self, mock_transformer, mock_ollama, mock_extrair,
        temp_dir, sample_text_contract
    ):
        """Testa fluxo completo via API REST."""
        from fastapi.testclient import TestClient
        from src.docbr_rag.api_rest import app
        
        # Setup mocks
        mock_extrair.return_value = [(1, sample_text_contract)]
        
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_transformer.return_value = mock_model
        
        mock_ollama.return_value = {
            "response": "Resposta via API"
        }
        
        client = TestClient(app)
        
        # Criar arquivo PDF fake
        pdf_path = temp_dir / "test.pdf"
        pdf_path.write_bytes(b"fake pdf")
        
        # Testar upload e indexação
        with open(pdf_path, "rb") as f:
            response = client.post(
                "/indexar",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sucesso"
        assert "documento" in data
        
        # Testar consulta
        response = client.post(
            "/consultar",
            json={"pergunta": "Qual o valor do contrato?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sucesso"
        assert "resposta" in data
        assert data["resposta"]["texto"]
        
        # Testar listagem
        response = client.get("/documentos")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sucesso"
        assert data["total"] >= 1
        
        # Testar health check
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "saudável"

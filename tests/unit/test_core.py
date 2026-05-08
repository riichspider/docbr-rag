"""
Testes unitários para o módulo core.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.docbr_rag.core import DocBR
from src.docbr_rag.models import TipoDocumento, Resposta, DocumentoInfo


class TestDocBR:
    """Testes para a classe principal DocBR."""

    def test_init_default(self):
        """Testa inicialização com valores padrão."""
        docbr = DocBR()

        assert docbr.model_name == "all-MiniLM-L6-v2"
        assert docbr.llm_model == "llama3.2:3b"
        assert docbr.chunk_size == 500
        assert docbr.chunk_overlap == 100
        assert docbr._documentos_indexados == []

    @patch('src.docbr_rag.core.SentenceTransformer')
    def test_init_custom(self, mock_transformer, temp_dir):
        """Testa inicialização com valores personalizados."""
        db_path = temp_dir / "custom_db"
        docbr = DocBR(
            model_name="custom-model",
            llm_model="custom-llm",
            db_path=str(db_path),
            chunk_size=300,
            chunk_overlap=50
        )

        assert docbr.model_name == "custom-model"
        assert docbr.llm_model == "custom-llm"
        assert docbr.chunk_size == 300
        assert docbr.chunk_overlap == 50

    @patch('src.docbr_rag.core.extrair_texto_pdf')
    @patch('src.docbr_rag.core.detectar_tipo')
    @patch('src.docbr_rag.core.criar_chunks')
    @patch('src.docbr_rag.core.SentenceTransformer')
    def test_indexar_documento_sucesso(
        self, mock_transformer, mock_criar_chunks,
        mock_detectar, mock_extrair, temp_dir
    ):
        """Testa indexação bem-sucedida de documento."""
        # Setup dos mocks
        mock_extrair.return_value = [(1, "Texto da página 1")]
        mock_detectar.return_value = TipoDocumento.CONTRATO

        mock_chunk = MagicMock()
        mock_chunk.texto = "Texto do chunk"
        mock_chunk.pagina = 1
        mock_chunk.indice = 0
        mock_criar_chunks.return_value = [mock_chunk]

        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_transformer.return_value = mock_model

        # Cria arquivo temporário
        pdf_path = temp_dir / "test.pdf"
        pdf_path.write_bytes(b"fake pdf")

        docbr = DocBR(db_path=str(temp_dir / "test_db"))

        # Testa indexação
        doc_info = docbr.indexar_documento(pdf_path)

        # Verificações
        assert isinstance(doc_info, DocumentoInfo)
        assert doc_info.tipo == TipoDocumento.CONTRATO
        assert doc_info.total_paginas == 1
        assert doc_info.total_chunks == 1
        assert doc_info.indexado is True
        assert len(docbr._documentos_indexados) == 1

    @patch('src.docbr_rag.core.extrair_texto_pdf')
    def test_indexar_documento_arquivo_nao_existe(self, mock_extrair):
        """Testa indexação de arquivo inexistente."""
        mock_extrair.side_effect = FileNotFoundError("Arquivo não encontrado")

        docbr = DocBR()

        from src.docbr_rag.exceptions import PDFExtractionError
        with pytest.raises(PDFExtractionError):
            docbr.indexar_documento("arquivo_inexistente.pdf")

    @patch('src.docbr_rag.core.ollama.generate')
    @patch('src.docbr_rag.core.SentenceTransformer')
    def test_consultar_sucesso(self, mock_transformer, mock_ollama):
        """Testa consulta bem-sucedida."""
        # Mock do modelo de embeddings
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_transformer.return_value = mock_model

        # Mock do ChromaDB
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "documents": [["Contexto relevante"]],
            "metadatas": [[{"pagina": 1, "tipo_documento": "contrato"}]]
        }

        # Mock do Ollama
        mock_ollama.return_value = {"response": "Resposta gerada"}

        docbr = DocBR()
        docbr.collection = mock_collection

        resposta = docbr.consultar("Pergunta de teste")

        assert isinstance(resposta, Resposta)
        assert resposta.texto == "Resposta gerada"
        assert resposta.paginas_referenciadas == [1]

    @patch('src.docbr_rag.core.SentenceTransformer')
    def test_consultar_sem_resultados(self, mock_transformer):
        """Testa consulta sem resultados relevantes."""
        # Mock do modelo de embeddings
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_transformer.return_value = mock_model

        # Mock do ChromaDB sem resultados
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "documents": [[]],
            "metadatas": [[]]
        }

        docbr = DocBR()
        docbr.collection = mock_collection

        resposta = docbr.consultar("Pergunta sem resultados")

        assert isinstance(resposta, Resposta)
        assert "Nenhum documento relevante" in resposta.texto
        assert resposta.confianca == 0.0

    @patch('src.docbr_rag.core.ollama.generate')
    @patch('src.docbr_rag.core.SentenceTransformer')
    def test_consultar_erro_ollama(self, mock_transformer, mock_ollama):
        """Testa consulta com erro no Ollama."""
        # Mock do modelo de embeddings
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_transformer.return_value = mock_model

        # Mock do ChromaDB
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "documents": [["Contexto"]],
            "metadatas": [[{"pagina": 1, "tipo_documento": "contrato"}]]
        }

        # Mock do Ollama com erro
        mock_ollama.side_effect = Exception("Erro Ollama")

        docbr = DocBR()
        docbr.collection = mock_collection

        resposta = docbr.consultar("Pergunta com erro")

        assert isinstance(resposta, Resposta)
        assert "Erro ao gerar resposta" in resposta.texto
        assert resposta.confianca == 0.0

    def test_listar_documentos_vazio(self):
        """Testa listagem de documentos vazia."""
        docbr = DocBR()
        documentos = docbr.listar_documentos()

        assert documentos == []

    def test_listar_documentos_com_itens(self, temp_dir):
        """Testa listagem com documentos indexados."""
        docbr = DocBR(db_path=str(temp_dir / "test_db"))

        # Adiciona documentos mockados
        doc_info1 = DocumentoInfo(
            tipo=TipoDocumento.CONTRATO,
            caminho="/path/contract1.pdf",
            total_paginas=5,
            total_chunks=10,
            indexado=True
        )
        doc_info2 = DocumentoInfo(
            tipo=TipoDocumento.NFE,
            caminho="/path/nfe1.pdf",
            total_paginas=1,
            total_chunks=3,
            indexado=True
        )

        docbr._documentos_indexados = [doc_info1, doc_info2]

        documentos = docbr.listar_documentos()

        assert len(documentos) == 2
        assert documentos[0].tipo == TipoDocumento.CONTRATO
        assert documentos[1].tipo == TipoDocumento.NFE

    def test_limpar_database(self, temp_dir):
        """Testa limpeza do banco de dados."""
        docbr = DocBR(db_path=str(temp_dir / "test_db"))

        # Adiciona documento
        doc_info = DocumentoInfo(
            tipo=TipoDocumento.CONTRATO,
            caminho="/path/test.pdf",
            total_paginas=1,
            total_chunks=1,
            indexado=True
        )
        docbr._documentos_indexados = [doc_info]

        # Limpa database
        docbr.limpar_database()

        # Verificações
        assert len(docbr._documentos_indexados) == 0
        # Verifica se collection foi recriada
        assert docbr.collection is not None

    def test_construir_prompt(self):
        """Testa construção de prompt."""
        docbr = DocBR()

        contextos = ["Contexto 1", "Contexto 2"]
        metadados = [
            {"pagina": 1, "tipo_documento": "contrato"},
            {"pagina": 2, "tipo_documento": "contrato"}
        ]
        pergunta = "Qual o valor?"

        prompt = docbr._construir_prompt(pergunta, contextos, metadados)

        assert "Contexto 1" in prompt
        assert "Contexto 2" in prompt
        assert "página 1" in prompt
        assert "página 2" in prompt
        assert "Qual o valor?" in prompt
        assert "contrato" in prompt

    def test_calcular_confianca(self):
        """Testa cálculo de confiança."""
        docbr = DocBR()

        # Teste com contexto vazio
        confianca = docbr._calcular_confianca([], "pergunta")
        assert confianca == 0.0

        # Teste com contexto pequeno
        confianca = docbr._calcular_confianca(["curto"], "pergunta")
        assert 0.0 <= confianca <= 1.0

        # Teste com múltiplos contextos
        confianca = docbr._calcular_confianca(
            ["contexto 1" * 100, "contexto 2" * 100],
            "pergunta"
        )
        assert 0.0 <= confianca <= 1.0

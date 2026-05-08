"""
Configuração compartilhada para testes do docbr-rag.
"""

import pytest
import tempfile
from pathlib import Path
import shutil

from src.docbr_rag.core import DocBR
from src.docbr_rag.models import TipoDocumento


@pytest.fixture
def temp_dir():
    """Cria um diretório temporário para testes."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def docbr_instance(temp_dir):
    """Instância do DocBR para testes com DB temporário."""
    db_path = temp_dir / "test_db"
    return DocBR(
        model_name="all-MiniLM-L6-v2",
        llm_model="llama3.2:3b",
        db_path=str(db_path),
        chunk_size=300,  # Menor para testes
        chunk_overlap=50
    )


@pytest.fixture
def sample_text_contract():
    """Texto de contrato de exemplo para testes."""
    return """
CONTRATO DE PRESTAÇÃO DE SERVIÇOS

CONTRATANTE: Empresa ABC Ltda.
CONTRATADO: Serviços XYZ ME

CLÁUSULA PRIMEIRA - DO OBJETO
O contratado se obriga a prestar serviços de consultoria em tecnologia.

CLÁUSULA SEGUNDA - DO PRAZO
O presente contrato terá vigência de 12 (doze) meses.

CLÁUSULA TERCEIRA - DO VALOR
O valor mensal dos serviços é de R$ 5.000,00 (cinco mil reais).

CLÁUSULA QUARTA - DAS PENALIDADES
Em caso de rescisão antecipada, será aplicada multa de 2 (dois) salários.

CLÁUSULA QUINTA - DO FORO
Fica eleito o Foro da Comarca de São Paulo para dirimir quaisquer dúvidas.
""".strip()


@pytest.fixture
def sample_text_nfe():
    """Texto de NF-e de exemplo para testes."""
    return """
NOTA FISCAL ELETRÔNICA

CHAVE DE ACESSO: 1234 5678 9012 3456 7890 1234 5678 9012 3456 7890 1234

EMITENTE: Empresa ABC Ltda.
CNPJ: 12.345.678/0001-90

DESTINATÁRIO: Cliente XYZ ME
CNPJ: 98.765.432/0001-01

DANFE

ITENS:
1 - Serviço de Consultoria - R$ 5.000,00
2 - Desenvolvimento de Software - R$ 3.000,00

VALOR TOTAL: R$ 8.000,00
IMPOSTOS: ICMS R$ 960,00
VALOR LIQUIDO: R$ 7.040,00
""".strip()


@pytest.fixture
def sample_text_boleto():
    """Texto de boleto de exemplo para testes."""
    return """
BANCO ABC S.A.

CÓDIGO DE BARRAS: 12345.67890 12345.678901 12345.678901 2 12345678901234

NOSSO NÚMERO: 12345678-9
VENCIMENTO: 15/12/2025
VALOR: R$ 1.234,56

PAGADOR: João da Silva
CPF: 123.456.789-01

BENEFICIÁRIO: Empresa ABC Ltda.
CNPJ: 12.345.678/0001-90
""".strip()


@pytest.fixture
def mock_pdf_content():
    """Conteúdo simulado de PDF para testes."""
    return {
        "page_1": "CONTRATO DE PRESTAÇÃO DE SERVIÇOS\n\nCONTRATANTE: Empresa ABC\n\nCLÁUSULA PRIMEIRA",
        "page_2": "CLÁUSULA SEGUNDA - DO PRAZO\n\nO contrato terá vigência de 12 meses.",
        "page_3": "CLÁUSULA TERCEIRA - DO VALOR\n\nValor mensal: R$ 5.000,00"
    }


@pytest.fixture
def expected_chunks():
    """Chunks esperados para testes de chunking."""
    return [
        "CONTRATO DE PRESTAÇÃO DE SERVIÇOS\n\nCONTRATANTE: Empresa ABC\n\nCLÁUSULA PRIMEIRA",
        "CLÁUSULA SEGUNDA - DO PRAZO\n\nO contrato terá vigência de 12 meses.",
        "CLÁUSULA TERCEIRA - DO VALOR\n\nValor mensal: R$ 5.000,00"
    ]


@pytest.fixture(scope="session")
def skip_if_no_ollama():
    """Pula testes que precisam de Ollama se não estiver disponível."""
    try:
        import ollama
        ollama.list()
        return False
    except (ImportError, Exception):
        return True


@pytest.fixture
def mock_ollama_response():
    """Resposta mockada do Ollama para testes."""
    return {
        "response": "Com base no contrato, o prazo é de 12 meses e o valor mensal é de R$ 5.000,00."
    }

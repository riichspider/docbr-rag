# Contribuindo para o docbr-rag

Obrigado pelo seu interesse em contribuir! Este guia vai ajudar você a contribuir de forma eficaz.

## 🚀 Começando

### Pré-requisitos

- Python 3.10+
- Git
- Docker (opcional, para testes)
- Ollama (para testes completos)

### Setup do Ambiente

```bash
# 1. Fork e clone
git clone https://github.com/SEU-USUARIO/docbr-rag.git
cd docbr-rag

# 2. Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# 3. Instale dependências
pip install -e ".[dev]"

# 4. Instale pre-commit hooks
pre-commit install

# 5. Baixe modelo LLM (opcional)
ollama pull llama3.2:3b
```

## 📋 Fluxo de Trabalho

### 1. Crie uma Branch

```bash
git checkout -b feature/sua-feature
# ou
git checkout -b fix/bug-description
```

### 2. Faça as Mudanças

- Siga as convenções de código
- Adicione testes para novas funcionalidades
- Documente mudanças importantes

### 3. Teste suas Mudanças

```bash
# Formatação e lint
ruff check src/ tests/
ruff format src/ tests/
mypy src/

# Testes
pytest tests/ -v --cov=src/docbr_rag

# Testes de integração (se aplicável)
pytest tests/integration/ -v
```

### 4. Commit suas Mudanças

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Features
git commit -m "feat: add support for DOCX files"

# Bug fixes
git commit -m "fix: resolve PDF parsing issue for scanned documents"

# Documentation
git commit -m "docs: update installation guide"

# Refactoring
git commit -m "refactor: improve chunking algorithm performance"

# Tests
git commit -m "test: add integration tests for API endpoints"
```

### 5. Push e Pull Request

```bash
git push origin feature/sua-feature
```

Abra um Pull Request no GitHub com:
- Título descritivo
- Descrição detalhada das mudanças
- Screenshots se aplicável
- Links para issues relacionadas

## 🏗️ Arquitetura do Projeto

### Estrutura de Diretórios

```
src/docbr_rag/
├── core.py              # Lógica principal RAG
├── config.py            # Sistema de configuração
├── logging_config.py    # Configuração de logging
├── exceptions.py        # Exceções customizadas
├── models.py           # Modelos Pydantic
├── cli.py              # Interface CLI
└── extractors/
    └── pdf.py          # Extração de PDFs
```

### Princípios de Design

1. **Separação de Responsabilidades**: Cada módulo tem uma função clara
2. **Configuração Centralizada**: Use `config.py` para configurações
3. **Logging Estruturado**: Use o sistema de logging configurado
4. **Tratamento de Erros**: Use exceções customizadas
5. **Testes**: Todo código novo deve ter testes

## 🧪 Guia de Testes

### Tipos de Testes

1. **Unitários**: Testam componentes isolados
2. **Integração**: Testam fluxos completos
3. **End-to-End**: Testam casos de uso reais

### Escrevendo Testes

```python
import pytest
from unittest.mock import patch
from src.docbr_rag.models import TipoDocumento

class TestNovaFuncionalidade:
    def test_caso_basico(self):
        """Testa caso básico da funcionalidade."""
        result = sua_funcao(parametro_teste)
        assert result == esperado
    
    def test_caso_erro(self):
        """Testa tratamento de erro."""
        with pytest.raises(SuaExcecao):
            sua_funcao(parametro_invalido)
    
    @patch('modulo.dependencia_externa')
    def test_com_mock(self, mock_dep):
        """Testa com dependência externa mockada."""
        mock_dep.return_value = "mockado"
        result = sua_funcao()
        mock_dep.assert_called_once()
```

### Fixtures Reutilizáveis

Use fixtures do `conftest.py`:

```python
@pytest.fixture
def sample_contract_text():
    return """
    CONTRATO DE PRESTAÇÃO DE SERVIÇOS
    CONTEÚDO DO CONTRATO...
    """

@pytest.fixture
def docbr_instance(temp_dir):
    return DocBR(db_path=str(temp_dir / "test_db"))
```

### Executando Testes

```bash
# Todos os testes
pytest

# Apenas unitários
pytest tests/unit/

# Com coverage
pytest --cov=src/docbr_rag --cov-report=html

# Teste específico
pytest tests/unit/test_models.py::TestTipoDocumento::test_tipo_documento_values
```

## 📝 Guia de Estilo

### Python

- Seguimos [PEP 8](https://pep8.org/)
- Usamos [Black](https://black.readthedocs.io/) para formatação
- Limite de linha: 88 caracteres
- Type hints obrigatórios

### Nomenclatura

```python
# Classes: PascalCase
class DocumentProcessor:
    pass

# Funções e variáveis: snake_case
def processar_documento(caminho_arquivo):
    return resultado

# Constantes: UPPER_CASE
MAX_CHUNK_SIZE = 500

# Privado: underscore prefix
def _funcao_interna():
    pass
```

### Docstrings

Use Google Style:

```python
def extrair_texto_pdf(caminho: str) -> List[Tuple[int, str]]:
    """Extrai texto de um arquivo PDF.
    
    Args:
        caminho: Caminho para o arquivo PDF.
        
    Returns:
        Lista de tuplas (número_página, texto).
        
    Raises:
        PDFExtractionError: Se o PDF não puder ser lido.
    """
    pass
```

## 🔧 Desenvolvimento

### Adicionando Novos Tipos de Documento

1. **Atualize o Enum** em `models.py`:
```python
class TipoDocumento(str, Enum):
    # ... tipos existentes ...
    NOVO_TIPO = "novo_tipo"
```

2. **Adicione Padrões** em `extractors/pdf.py`:
```python
_PADROES_TIPO = {
    # ... padrões existentes ...
    TipoDocumento.NOVO_TIPO: [
        r"PADRÃO 1",
        r"PADRÃO 2",
    ],
}
```

3. **Adicione Testes**:
```python
def test_detectar_novo_tipo(self, sample_text_novo_tipo):
    tipo = detectar_tipo(sample_text_novo_tipo)
    assert tipo == TipoDocumento.NOVO_TIPO
```

### Adicionando Novos Extractors

1. **Crie o módulo** em `extractors/`
2. **Implemente interface padrão**:
```python
def extrair_texto_formato(caminho: str) -> List[Tuple[int, str]]:
    """Extrai texto do formato específico."""
    pass

def detectar_tipo_formato(texto: str) -> TipoDocumento:
    """Detecta tipo de documento no formato."""
    pass
```

3. **Exporte em `extractors/__init__.py`**

4. **Adicione testes**

### Configuração

Para novas opções de configuração:

1. **Adicione ao modelo Pydantic** em `config.py`
2. **Adicione variável de ambiente** se necessário
3. **Documente** no `docbr_config.yaml`

## 🐛 Debug e Troubleshooting

### Debug Local

```bash
# Ative logging debug
export DOCBR_LOG_LEVEL=DEBUG

# Use pdb
python -m pdb -c continue src/docbr_rag/cli.py

# Logs detalhados
pytest -v -s tests/unit/test_core.py
```

### Problemas Comuns

1. **ImportError**: Verifique se instalou dependências
2. **Ollama não encontrado**: Inicie o serviço Ollama
3. **Testes falhando**: Verifique se os mocks estão corretos
4. **Coverage baixo**: Adicione testes para o código não coberto

## 📖 Documentação

### Atualizando Documentação

- **README.md**: Para usuários finais
- **CONTEXT.md**: Para desenvolvedores
- **Código**: Docstrings para API

### Exemplos

Adicione exemplos em `examples/`:

```python
# examples/novo_exemplo.py
"""
Exemplo de nova funcionalidade.
"""

from src.docbr_rag import DocBR

def main():
    docbr = DocBR()
    # Demonstre a funcionalidade
    
if __name__ == "__main__":
    main()
```

## 🚀 Release Process

### Versionamento

Usamos [Semantic Versioning](https://semver.org/):

- **MAJOR**: Mudanças que quebram compatibilidade
- **MINOR**: Novas funcionalidades (backward compatible)
- **PATCH**: Bug fixes

### Fazendo Release

1. **Atualize versão** em `pyproject.toml`
2. **Atualize CHANGELOG.md**
3. **Crie tag**: `git tag v1.2.3`
4. **Push**: `git push origin v1.2.3`
5. **GitHub Actions** vai publicar automaticamente

## 🤝 Código de Conduta

Seja respeitoso e profissional. Reporte problemas para os mantenedores.

## 🎯 Boas Práticas

### Do's

- ✅ Escreva testes para novo código
- ✅ Use type hints
- ✅ Siga convenções de commit
- ✅ Documente código complexo
- ✅ Mantenha commits atômicos
- ✅ Use issues para discussões

### Don'ts

- ❌ Commits grandes e monolíticos
- ❌ Código sem testes
- ❌ Ignorar warnings do lint
- ❌ Hardcode de valores configuráveis
- ❌ Mudanças sem documentação

## 📞 Ajuda

### Canais de Comunicação

- **GitHub Issues**: Bugs e feature requests
- **Discussions**: Dúvidas e discussões
- **Pull Requests**: Contribuições de código

### Mantenedores

- **@seu-usuario**: Mantenedor principal
- **@outro-mantenedor**: Especialista em ML

### Recursos

- [Documentação completa](https://github.com/seu-usuario/docbr-rag/wiki)
- [API Reference](https://seu-usuario.github.io/docbr-rag/)
- [Exemplos](https://github.com/seu-usuario/docbr-rag/tree/main/examples)

---

## 🙏 Agradecimentos

Obrigado por contribuir! Cada contribuição ajuda a tornar o docbr-rag melhor para toda a comunidade brasileira.

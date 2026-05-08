# Testes do docbr-rag

Este diretório contém a suíte de testes do projeto docbr-rag.

## 📁 Estrutura

```
tests/
├── __init__.py              # Configuração do pacote de testes
├── conftest.py              # Fixtures compartilhadas
├── pytest.ini              # Configuração do pytest
├── unit/                   # Testes unitários
│   ├── test_models.py       # Testes dos modelos Pydantic
│   ├── test_extractors.py   # Testes dos extratores de PDF
│   └── test_core.py        # Testes do módulo core
├── integration/            # Testes de integração
│   └── test_workflow.py    # Testes do fluxo completo
└── fixtures/               # Dados de teste (PDFs, etc.)
```

## 🚀 Como Executar

### Pré-requisitos

```bash
# Instalar dependências de desenvolvimento
pip install -e ".[dev]"

# Opcional: Instalar Ollama para testes completos
ollama pull llama3.2:3b
```

### Executar Todos os Testes

```bash
# Rodar todos os testes
pytest

# Com coverage
pytest --cov=src/docbr_rag --cov-report=html

# Com output detalhado
pytest -v -s
```

### Executar Testes Específicos

```bash
# Apenas testes unitários
pytest tests/unit/

# Apenas testes de integração
pytest tests/integration/

# Teste específico
pytest tests/unit/test_models.py::TestTipoDocumento::test_tipo_documento_values

# Testes que precisam de Ollama
pytest -m requires_ollama
```

### Executar com Paralelização

```bash
# Instalar pytest-xdist
pip install pytest-xdist

# Rodar em paralelo (4 processos)
pytest -n 4
```

## 📋 Tipos de Testes

### Unitários (`tests/unit/`)

Testam componentes isolados:

- **`test_models.py`**: Validação dos modelos Pydantic
- **`test_extractors.py`**: Extração e processamento de PDFs
- **`test_core.py`**: Lógica principal da classe DocBR

### Integração (`tests/integration/`)

Testam o fluxo completo:

- **`test_workflow.py`**: Indexação → Consulta → Resposta
- Testes com múltiplos documentos
- Testes de API REST e CLI

## 🔧 Fixtures Disponíveis

### Fixtures Gerais

- `temp_dir`: Diretório temporário para testes
- `docbr_instance`: Instância do DocBR com DB temporário

### Fixtures de Conteúdo

- `sample_text_contract`: Texto de contrato exemplo
- `sample_text_nfe`: Texto de NF-e exemplo  
- `sample_text_boleto`: Texto de boleto exemplo
- `mock_pdf_content`: Conteúdo simulado de PDF
- `expected_chunks`: Chunks esperados para validação

### Fixtures de Mock

- `skip_if_no_ollama`: Pula testes se Ollama não estiver disponível
- `mock_ollama_response`: Resposta mockada do Ollama

## 📊 Coverage

Para gerar relatório de coverage:

```bash
# Gerar relatório HTML
pytest --cov=src/docbr_rag --cov-report=html

# Ver no navegador
open htmlcov/index.html

# Gerar relatório no terminal
pytest --cov=src/docbr_rag --cov-report=term-missing
```

Meta: **>90% de cobertura** nos módulos principais.

## 🏆 Boas Práticas

### Escrevendo Testes

1. **Testes unitários** devem ser rápidos e isolados
2. **Use mocks** para dependências externas (Ollama, ChromaDB)
3. **Testes de integração** devem testar fluxos reais
4. **Fixtures reutilizáveis** para dados comuns

### Nomenclatura

```python
class TestNomeDaClasse:
    def test_metodo_situacao_esperada(self):
        # Arrange
        # Act  
        # Assert
```

### Marcadores (Markers)

```python
@pytest.mark.unit
def test_unitario():
    pass

@pytest.mark.integration  
def test_integracao():
    pass

@pytest.mark.requires_ollama
def test_com_ollama():
    pass
```

## 🐛 Debug de Testes

### Executar com Debug

```bash
# Parar no primeiro erro
pytest -x

# Executar com pdb
pytest --pdb

# Executar teste específico com debug
pytest tests/unit/test_models.py::TestTipoDocumento -s -v
```

### Ver Output

```bash
# Mostrar print statements
pytest -s

# Ver output capturado
pytest --capture=no

# Ver logs
pytest --log-cli-level=DEBUG
```

## 🔄 CI/CD

Os testes são executados automaticamente em:

- **Pull Requests**: Validação de código
- **Main Branch**: Testes completos com coverage
- **Releases**: Testes de regressão

### GitHub Actions

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Run tests
        run: pytest --cov=src/docbr_rag
```

## 📈 Métricas

### Cobertura Atual

- **Models**: 95%
- **Extractors**: 88%  
- **Core**: 82%
- **CLI**: 75%

### Performance

- **Testes unitários**: < 2s
- **Testes integração**: < 30s
- **Todos os testes**: < 1min

## 🚧 Limitações

1. **PDFs reais**: Testes usam mocks para evitar dependência de arquivos
2. **Ollama**: Alguns testes pulados se Ollama não disponível
3. **Performance**: Testes de performance em desenvolvimento

## 🤝 Contribuindo

### Adicionando Novos Testes

1. **Unitários**: Adicione em `tests/unit/`
2. **Integração**: Adicione em `tests/integration/`
3. **Fixtures**: Adicione em `conftest.py` se reutilizável

### Revisão de Code

- **Coverage** não deve diminuir
- **Testes** devem ser rápidos (< 1s para unitários)
- **Mocks** para dependências externas
- **Asserts** descritivos com mensagens claras

## 📝 Exemplos

### Teste Unitário

```python
def test_detectar_tipo_contrato(self, sample_text_contract):
    """Testa detecção de contrato."""
    tipo = detectar_tipo(sample_text_contract)
    assert tipo == TipoDocumento.CONTRATO
```

### Teste de Integração

```python
def test_fluxo_completo(self, sample_pdf):
    """Testa indexação e consulta."""
    docbr = DocBR()
    doc_info = docbr.indexar_documento(sample_pdf)
    resposta = docbr.consultar("Pergunta teste")
    
    assert doc_info.tipo == TipoDocumento.CONTRATO
    assert resposta.texto
```

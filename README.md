# 📄 docbr-rag

> RAG especializado em documentos brasileiros — 100% local, gratuito e open source.

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

---

## ✨ O que é

**docbr-rag** é um sistema de RAG (Retrieval-Augmented Generation) especializado em documentos brasileiros. Funciona 100% localmente, entendendo o contexto de contratos, NFe, laudos, certidões e outros documentos brasileiros.

```python
from docbr_rag import DocBR

# Inicializa o sistema
docbr = DocBR()

# Indexa um documento
docbr.indexar_documento("contrato.pdf")

# Faz perguntas em português
resposta = docbr.consultar("Qual o prazo e a multa por rescisão?")
print(resposta.texto)
print(f"Fonte: páginas {resposta.paginas_referenciadas}")
```

---

## 🚀 Características

- ✅ **100% Local** - Sem APIs externas, sem envio de dados
- ✅ **Especializado** - Otimizado para documentos brasileiros
- ✅ **Open Source** - Código aberto e modificável
- ✅ **Gratuito** - Sem custos de API ou modelo
- ✅ **Multi-formato** - Contratos, NFe, boletos, laudos, certidões, holerites

---

## 📦 Instalação

### Pré-requisitos

1. **Python 3.10+**
2. **Ollama** instalado localmente

```bash
# Instalar Ollama (Linux/macOS)
curl -fsSL https://ollama.ai/install.sh | sh

# Windows: baixe de https://ollama.ai/

# Baixar modelo LLM
ollama pull llama3.2:3b
```

### Instalação do Projeto

```bash
# Clonar repositório
git clone https://github.com/seu-usuario/docbr-rag
cd docbr-rag

# Instalar em modo desenvolvimento
pip install -e .

# Ou instalar dependências manualmente
pip install pdfplumber pymupdf sentence-transformers chromadb ollama pydantic typer rich
```

---

## 🔧 Uso Rápido

### Linha de Comando

```bash
# Indexar um documento
docbr-rag indexar contrato.pdf

# Consultar documento indexado
docbr-rag consultar "Qual o valor total do contrato?"

# Listar documentos indexados
docbr-rag listar

# Limpar banco de dados
docbr-rag limpar --confirmar
```

### Python API

```python
from docbr_rag import DocBR
from pathlib import Path

# Inicializar com configurações personalizadas
docbr = DocBR(
    model_name="all-MiniLM-L6-v2",  # Modelo de embeddings
    llm_model="llama3.2:3b",         # Modelo de linguagem
    db_path="./meu_db"              # Banco de dados local
)

# Indexar múltiplos documentos
documentos = ["contrato.pdf", "nfe.pdf", "laudo.pdf"]
for doc in documentos:
    if Path(doc).exists():
        doc_info = docbr.indexar_documento(doc)
        print(f"✅ {doc_info.tipo.value}: {doc_info.total_chunks} chunks")

# Fazer consultas específicas
perguntas = [
    "Qual o valor total da NF-e?",
    "Quais as cláusulas de penalidade?",
    "Qual foi a conclusão do laudo?"
]

for pergunta in perguntas:
    resposta = docbr.consultar(pergunta, n_resultados=3)
    print(f"❓ {pergunta}")
    print(f"📝 {resposta.texto}")
    print(f"📄 Páginas: {resposta.paginas_referenciadas}")
    print(f"🎯 Confiança: {resposta.confianca}\n")
```

---

## 📋 Tipos de Documentos Suportados

| Tipo | Status | Padrões Reconhecidos |
|---|---|---|
| Contrato | ✅ | CLÁUSULA, CONTRATANTE, VIGÊNCIA, FORO |
| NFe / Nota Fiscal | ✅ | NOTA FISCAL ELETRÔNICA, CHAVE DE ACESSO, DANFE |
| Boleto | ✅ | BOLETO, CÓDIGO DE BARRAS, VENCIMENTO, NOSSO NÚMERO |
| Laudo Técnico | ✅ | LAUDO TÉCNICO, PERITO, CONCLUSÃO, OBJETO DA PERÍCIA |
| Certidão | ✅ | CERTIDÃO, CARTÓRIO, REGISTRO CIVIL |
| Holerite | ✅ | HOLERITE, INSS, FGTS, SALÁRIO BASE |

---

## 🏗️ Estrutura do Projeto

```
docbr-rag/
├── src/
│   └── docbr_rag/
│       ├── __init__.py         # Exportações principais
│       ├── core.py             # Classe DocBR (RAG engine)
│       ├── cli.py              # Interface de linha de comando
│       ├── models.py           # Modelos de dados (Pydantic)
│       └── extractors/
│           ├── __init__.py     # Exportações de extratores
│           └── pdf.py          # Extração de PDF brasileiros
├── examples/                   # Exemplos de uso
│   ├── basico.py              # Uso básico
│   ├── lote.py                # Processamento em lote
│   ├── api_rest.py            # API REST com FastAPI
│   └── README.md              # Documentação dos exemplos
├── CONTEXT.md                 # Arquitetura e decisões
├── README.md                  # Documentação principal
└── pyproject.toml             # Configuração do pacote
```

---

## 📚 Exemplos

### Exemplo Básico
```bash
cd examples
python basico.py
```

### Processamento em Lote
```bash
cd examples
mkdir documentos
# Coloque seus PDFs na pasta documentos/
python lote.py
```

### API REST
```bash
cd examples
pip install fastapi uvicorn
python api_rest.py
# Acesse http://localhost:8000/docs
```

---

## 🧪 Testes

```bash
# Instalar dependências de desenvolvimento
pip install -e ".[dev]"

# Rodar testes
pytest

# Rodar com coverage
pytest --cov=src/docbr_rag

# Verificar código
ruff check src/
mypy src/
```

---

## 🤝 Como Contribuir

1. **Fork** o repositório
2. **Crie** uma branch para sua feature
3. **Adicione** testes para novas funcionalidades
4. **Execute** os testes existentes
5. **Abra** um Pull Request

**Áreas que precisam de ajuda:**
- 🆕 Novos tipos de documentos brasileiros
- 🔧 Melhorias no chunking específico por tipo
- 🧪 Testes com documentos reais (anonimizados)
- 📖 Melhorias na documentação
- 🚀 Performance e otimizações

---

## 📄 Licença

MIT — use, modifique e distribua livremente.

---

## � Links Úteis

- [CONTEXT.md](CONTEXT.md) - Arquitetura detalhada
- [examples/](examples/) - Exemplos práticos
- [Issues](https://github.com/seu-usuario/docbr-rag/issues) - Bugs e feature requests

---

## 🙏 Por que este projeto?

Documentos brasileiros têm estrutura, linguagem e regras próprias que ferramentas genéricas não entendem. Este projeto nasceu da necessidade de uma alternativa **open source**, **gratuita** e **local** para o ecossistema brasileiro de documentos.

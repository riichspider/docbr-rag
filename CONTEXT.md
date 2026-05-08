# docbr-rag - Contexto e Arquitetura

## Visão Geral

O **docbr-rag** é um sistema RAG (Retrieval-Augmented Generation) especializado em documentos brasileiros, funcionando 100% localmente sem dependências de APIs externas.

## Arquitetura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Documentos    │───▶│   Extratores     │───▶│   Chunks        │
│  (PDFs BR)      │    │  (PDF Brasileiro)│    │  (Estruturados) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                       │
┌─────────────────┐    ┌──────────────────┐           ▼
│   Respostas     │◀───│      Core        │    ┌─────────────────┐
│  (Geradas LLM)  │    │   (DocBR RAG)    │◀───│   Embeddings    │
└─────────────────┘    └──────────────────┘    │   (Semânticos)  │
                                              └─────────────────┘
                                                       │
                                              ┌─────────────────┐
                                              │   Vector DB     │
                                              │  (ChromaDB)     │
                                              └─────────────────┘
```

## Fluxo Principal

### 1. Indexação de Documentos
```
PDF → Extração de Texto → Detecção Tipo → Chunking → Embeddings → Vector DB
```

**Detalhes:**
- **Extração**: pdfplumber (principal) + pymupdf (fallback)
- **Detecção**: Padrões regex para documentos brasileiros
- **Chunking**: Respeita estruturas (cláusulas, artigos, seções)
- **Embeddings**: Sentence Transformers (modelo configurável)
- **Storage**: ChromaDB persistente

### 2. Consulta RAG
```
Pergunta → Embedding → Busca Similar → Contexto → LLM Local → Resposta
```

**Detalhes:**
- **Busca**: Similaridade coseno no vetor DB
- **Contexto**: Top-k chunks mais relevantes
- **LLM**: Ollama com modelo local (llama3.2:3b padrão)
- **Resposta**: Com fontes, páginas e confiança

## Tipos de Documentos Suportados

### Padrões de Detecção
- **NF-e**: "NOTA FISCAL ELETRÔNICA", "CHAVE DE ACESSO", "DANFE"
- **Boleto**: "BOLETO", "CÓDIGO DE BARRAS", "VENCIMENTO"
- **Contrato**: "CONTRATO", "CLÁUSULA", "CONTRATANTE"
- **Laudo**: "LAUDO TÉCNICO", "PERITO", "CONCLUSÃO"
- **Certidão**: "CERTIDÃO", "CARTÓRIO", "REGISTRO CIVIL"
- **Holerite**: "HOLERITE", "INSS", "FGTS", "SALÁRIO"

### Estratégia de Chunking Específica
- **Contratos**: Divide por cláusulas numeradas
- **Documentos Legais**: Respeita artigos e parágrafos
- **Financeiros**: Preserva valores e datas
- **Geral**: Títulos maiúsculos e seções numeradas

## Componentes

### Core (`src/docbr_rag/core.py`)
- **Classe `DocBR`**: Orquestrador principal
- **Métodos**: `indexar_documento()`, `consultar()`, `listar_documentos()`
- **Configuração**: Modelos, DB, parâmetros de chunking

### Extractors (`src/docbr_rag/extractors/`)
- **PDF**: Extração robusta com fallback
- **Detecção**: Identificação automática de tipo
- **Chunking**: Otimizado para estrutura brasileira

### Models (`src/docbr_rag/models.py`)
- **Pydantic**: Validação de dados
- **Tipos**: `DocumentoInfo`, `Chunk`, `Resposta`, `TipoDocumento`
- **Serialização**: JSON automático

### CLI (`src/docbr_rag/cli.py`)
- **Typer**: Interface moderna
- **Rich**: Output formatado
- **Comandos**: `indexar`, `consultar`, `listar`, `limpar`

## Configurações Recomendadas

### Modelos
- **Embeddings**: `all-MiniLM-L6-v2` (leve e eficaz)
- **LLM**: `llama3.2:3b` (local e rápido)
- **Alternativas**: `paraphrase-multilingual-MiniLM-L12-v2`

### Parâmetros
- **Chunk Size**: 500 caracteres (ideal para docs BR)
- **Overlap**: 100 caracteres (mantém contexto)
- **Top-k**: 5 chunks (bom equilíbrio)

### Performance
- **CPU**: Funciona bem em 4+ cores
- **RAM**: 8GB+ recomendado
- **Storage**: DB cresce ~1MB por 100 páginas

## Casos de Uso

### 1. Análise de Contratos
```python
docbr = DocBR()
docbr.indexar_documento("contrato_social.pdf")
resposta = docbr.consultar("Qual é a cláusula de rescisão?")
```

### 2. Consulta de Notas Fiscais
```python
resposta = docbr.consultar("Qual o valor total da NF-e?")
# Retorna com página e confiança
```

### 3. Laudos Técnicos
```python
resposta = docbr.consultar("Quais foram as conclusões do perito?")
# Busca em seções específicas
```

## Limitações Atuais

- **Formatos**: Apenas PDF (planos para DOC/DOCX)
- **Idioma**: Otimizado para português brasileiro
- **Escalabilidade**: Single-thread (pode ser paralelizado)
- **Modelos**: Requer Ollama instalado

## Próximas Melhorias

### Curto Prazo
- [ ] Testes automatizados com documentos reais
- [ ] Logging estruturado
- [ ] Tratamento de erros robusto
- [ ] Configuração via arquivo

### Médio Prazo
- [ ] Suporte a outros formatos (DOCX, TXT)
- [ ] Processamento paralelo
- [ ] Interface web simples
- [ ] API REST

### Longo Prazo
- [ ] Fine-tuning de modelos para docs BR
- [ ] Extração de entidades específicas
- [ ] Integração com sistemas legados
- [ ] Multi-tenant

## Decisões de Design

### Por que ChromaDB?
- Leve e local
- Interface Python amigável
- Suporte a metadados
- Persistência automática

### Por que Sentence Transformers?
- Modelos pré-treinados multilíngues
- Performance em CPU
- API simples
- Sem dependências externas

### Por que Pydantic?
- Validação automática
- Serialização JSON
- Type hints
- Documentação integrada

## Boas Práticas

### Indexação
- Documentos pequenos: < 100 páginas ideal
- Nomes de arquivos: descritivos e sem espaços
- Backup regular do DB

### Consultas
- Perguntas específicas funcionam melhor
- Contexto relevante ajuda na precisão
- Verificar confiança da resposta

### Performance
- Limpar DB periodicamente
- Usar modelos menores para produção
- Monitorar uso de RAM

## Troubleshooting

### Problemas Comuns
- **PDF corrompido**: Fallback automático para pymupdf
- **Baixa confiança**: Aumentar chunk size ou top-k
- **Respostas vagas**: Prompt engineering no LLM
- **Performance**: Reduzir tamanho dos chunks

### Debug
- Logs em `core.py` mostram fluxo completo
- Metadados salvos permitem rastreabilidade
- CLI com modo verbose planejado

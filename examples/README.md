# Exemplos de Uso do docbr-rag

Este diretório contém exemplos práticos para demonstrar como usar o sistema docbr-rag em diferentes cenários.

## Pré-requisitos

1. **Instale o projeto**:
   ```bash
   pip install -e .
   ```

2. **Instale o Ollama** (para LLM local):
   ```bash
   # Linux/macOS
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Windows: baixe de https://ollama.ai/
   ```

3. **Baixe o modelo LLM**:
   ```bash
   ollama pull llama3.2:3b
   ```

## Exemplos Disponíveis

### 1. `basico.py` - Uso Básico

**Quando usar**: Primeiros testes, entendimento do fluxo básico

**O que faz**:
- Indexa um único documento PDF
- Realiza consultas específicas sobre o documento
- Mostra confiança e fontes das respostas

**Como executar**:
```bash
cd examples
python basico.py
```

**Pré-requisitos**: Tenha um arquivo PDF brasileiro no mesmo diretório e atualize o nome em `caminho_documento`.

---

### 2. `lote.py` - Processamento em Lote

**Quando usar**: Múltiplos documentos, análise comparativa

**O que faz**:
- Encontra e indexa todos os PDFs de um diretório
- Gera estatísticas por tipo de documento
- Realiza consultas cruzadas entre documentos
- Lista todos os documentos indexados

**Como executar**:
```bash
cd examples
mkdir documentos
# Coloque seus PDFs brasileiros na pasta documentos/
python lote.py
```

**Estrutura esperada**:
```
examples/
├── documentos/
│   ├── contrato.pdf
│   ├── nfe.pdf
│   ├── laudo.pdf
│   └── boleto.pdf
└── lote.py
```

---

### 3. `api_rest.py` - API REST

**Quando usar**: Integração com outras aplicações, uso via HTTP

**O que faz**:
- Expõe endpoints REST para indexação e consulta
- Suporta upload de arquivos via multipart/form-data
- Retorna respostas em formato JSON
- Inclui health check e documentação automática

**Como executar**:
```bash
cd examples
pip install fastapi uvicorn
python api_rest.py
```

**Endpoints disponíveis**:
- `GET /` - Informações da API
- `POST /indexar` - Indexar documento (upload)
- `POST /consultar` - Consultar documentos
- `GET /documentos` - Listar documentos
- `DELETE /documentos` - Limpar banco
- `GET /health` - Health check

**Exemplo de uso via curl**:
```bash
# Indexar documento
curl -X POST "http://localhost:8000/indexar" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@contrato.pdf"

# Consultar
curl -X POST "http://localhost:8000/consultar" \
     -H "accept: application/json" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "pergunta=Qual o valor do contrato?"

# Listar documentos
curl -X GET "http://localhost:8000/documentos"
```

---

## Dicas de Uso

### Para Documentos Brasileiros

1. **Contratos**: Funciona melhor com PDFs textuais (não escaneados)
2. **NF-e**: Reconhece campos como chave de acesso e valores
3. **Boletos**: Identifica bancos, valores e vencimentos
4. **Laudos**: Extrai conclusões e metodologias
5. **Certidões**: Reconhece cartórios e datas

### Performance

- **CPU**: 4+ cores recomendado para processamento em lote
- **RAM**: 8GB+ para múltiplos documentos
- **Storage**: DB cresce ~1MB por 100 páginas

### Consultas Eficazes

**Boas práticas**:
- Seja específico: "Qual a cláusula de multa?" vs "O que tem no contrato?"
- Use termos brasileiros: "contratante", "vencimento", "alvará"
- Contextualize: "Segundo o laudo pericial, qual foi a conclusão?"

**Exemplos por tipo**:
- **Contratos**: "cláusula", "vigência", "rescisão", "penalidade"
- **NF-e**: "valor total", "CFOP", "chave de acesso", "emitente"
- **Boletos**: "vencimento", "banco", "valor", "nosso número"
- **Laudos**: "conclusão", "metodologia", "perito", "objeto"

## Troubleshooting

### Problemas Comuns

1. **"Arquivo não encontrado"**:
   - Verifique o caminho completo do arquivo
   - Use barras normais `/` mesmo no Windows

2. **"Modelo não encontrado"**:
   - Execute `ollama pull llama3.2:3b`
   - Verifique se o Ollama está rodando

3. **"Baixa confiança"**:
   - Aumente `n_resultados` na consulta
   - Verifique se o documento foi corretamente extraído

4. **"Respostas vagas"**:
   - Seja mais específico na pergunta
   - Verifique o tipo de documento detectado

### Debug

Para debug detalhado, modifique o código para adicionar logs:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Próximos Passos

Depois de testar os exemplos:

1. **Adaptar** para seus documentos específicos
2. **Ajustar** parâmetros de chunking para seu domínio
3. **Estender** com novos tipos de documentos
4. **Integrar** com seus sistemas existentes

## Contribuições

Contribuições são bem-vindas! Algumas ideias:
- Novos exemplos de uso
- Melhorias nos prompts
- Suporte a outros formatos
- Otimizações de performance

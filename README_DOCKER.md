# Docker para docbr-rag

Este documento explica como usar Docker para deploy e desenvolvimento do docbr-rag.

## 🐋 Imagens Disponíveis

O Dockerfile suporta múltiplos targets:

- **`base`**: Imagem base com Python e Ollama
- **`development`**: Inclui dependências de desenvolvimento
- **`production`**: Imagem otimizada para produção
- **`cli`**: Imagem para uso via CLI

## 🚀 Uso Rápido

### Produção (API)

```bash
# Build e execução
docker-compose up -d

# Acesse a API
curl http://localhost:8000/docs
```

### Desenvolvimento

```bash
# Com hot reload
docker-compose -f docker-compose.dev.yml up

# Acesse a API de desenvolvimento
curl http://localhost:8000/docs
```

### CLI Interativo

```bash
# Executar CLI
docker-compose run docbr-cli

# Exemplo de uso
docbr-rag indexar /app/documents/contrato.pdf
docbr-rag consultar "Qual o valor do contrato?"
```

## 📁 Estrutura de Volumes

### Produção
- `./data` - Banco de dados e arquivos persistentes
- `ollama_data` - Modelos LLM baixados

### Desenvolvimento
- `./` - Código fonte (para hot reload)
- `./documents` - Documentos PDF para testar
- `./data` - Dados de desenvolvimento

## 🔧 Comandos Úteis

### Build

```bash
# Build de produção
docker build -t docbr-rag:latest .

# Build de desenvolvimento
docker build -t docbr-rag:dev --target development .

# Build com cache
docker-compose build --no-cache
```

### Execução

```bash
# Iniciar todos os serviços
docker-compose up -d

# Ver logs
docker-compose logs -f docbr-api

# Parar serviços
docker-compose down

# Limpar volumes
docker-compose down -v
```

### Desenvolvimento

```bash
# Iniciar ambiente de dev
docker-compose -f docker-compose.dev.yml up -d

# Entrar no container de CLI
docker-compose -f docker-compose.dev.yml exec docbr-cli-dev bash

# Rodar testes
docker-compose -f docker-compose.dev.yml run --rm docbr-tests
```

## ⚙️ Configuração

### Variáveis de Ambiente

Configure via `docker-compose.yml` ou `.env`:

```yaml
environment:
  - DOCBR_DB_PATH=/app/data/docbr_db
  - DOCBR_LLM_MODEL=llama3.2:3b
  - DOCBR_LOG_LEVEL=INFO
  - DOCBR_EMBEDDING_MODEL=all-MiniLM-L6-v2
  - DOCBR_CHUNK_SIZE=500
```

### Arquivo de Configuração

Monte arquivo de configuração:

```yaml
volumes:
  - ./docbr_config.yaml:/app/config.yaml
```

E defina a variável:
```yaml
environment:
  - DOCBR_CONFIG_FILE=/app/config.yaml
```

## 🎯 Casos de Uso

### 1. API de Produção

```bash
# Inicia API
docker-compose up -d docbr-api

# Testa saúde
curl http://localhost:8000/health

# Indexa documento
curl -X POST "http://localhost:8000/indexar" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@contrato.pdf"

# Consulta
curl -X POST "http://localhost:8000/consultar" \
     -H "accept: application/json" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "pergunta=Qual o valor do contrato?"
```

### 2. Desenvolvimento com Hot Reload

```bash
# Inicia com hot reload
docker-compose -f docker-compose.dev.yml up docbr-api-dev

# Altere código - as mudanças serão aplicadas automaticamente
# Logs aparecem em tempo real
```

### 3. Processamento em Lote

```bash
# Coloque PDFs em ./documents/
docker-compose run --rm docbr-cli \
     python examples/lote.py
```

### 4. Testes Automatizados

```bash
# Roda todos os testes
docker-compose -f docker-compose.dev.yml run --rm docbr-tests

# Testes específicos
docker-compose -f docker-compose.dev.yml run --rm docbr-tests \
     pytest tests/unit/ -v
```

## 🔍 Debug e Troubleshooting

### Ver Logs

```bash
# Logs de todos os serviços
docker-compose logs

# Logs específicos
docker-compose logs docbr-api
docker-compose logs ollama

# Logs em tempo real
docker-compose logs -f
```

### Debug Interativo

```bash
# Entrar no container
docker-compose exec docbr-api bash

# Verificar Ollama
docker-compose exec ollama ollama list

# Verificar banco de dados
docker-compose exec docbr-api ls -la /app/data/
```

### Problemas Comuns

**1. Porta em uso:**
```bash
# Verifique as portas
netstat -tulpn | grep :8000
netstat -tulpn | grep :11434

# Mude as portas em docker-compose.yml
```

**2. Permissões:**
```bash
# Ajuste permissões dos volumes
sudo chown -R $USER:$USER ./data
sudo chown -R $USER:$USER ./documents
```

**3. Modelo não encontrado:**
```bash
# Baixe modelo manualmente
docker-compose exec ollama ollama pull llama3.2:3b

# Verifique modelos disponíveis
docker-compose exec ollama ollama list
```

**4. Memória insuficiente:**
```bash
# Limpe containers não usados
docker system prune -a

# Aumente limite de memória no Docker Desktop
```

## 📊 Monitoramento

### Health Checks

```bash
# Verificar saúde dos containers
docker-compose ps

# Health check da API
curl http://localhost:8000/health

# Health check do Ollama
curl http://localhost:11434/api/tags
```

### Recursos

```bash
# Uso de recursos
docker stats

# Uso de disco
docker system df

# Informações do container
docker inspect docbr-api
```

## 🚀 Deploy em Produção

### 1. Preparação

```bash
# Crie arquivo .env
cat > .env << EOF
DOCBR_LLM_MODEL=llama3.2:3b
DOCBR_LOG_LEVEL=INFO
DOCBR_DB_PATH=/app/data/docbr_db
EOF

# Crie diretórios
mkdir -p data documents
```

### 2. Deploy

```bash
# Build e deploy
docker-compose up -d

# Verifique funcionamento
curl http://localhost:8000/health
```

### 3. Backup

```bash
# Backup do banco de dados
docker run --rm -v docbr_docbr-db:/data -v $(pwd):/backup \
     alpine tar czf /backup/docbr-db-backup.tar.gz -C /data .

# Backup dos modelos Ollama
docker run --rm -v docbr_ollama_data:/data -v $(pwd):/backup \
     alpine tar czf /backup/ollama-backup.tar.gz -C /data .
```

### 4. Restore

```bash
# Restore do banco de dados
docker run --rm -v docbr_docbr-db:/data -v $(pwd):/backup \
     alpine tar xzf /backup/docbr-db-backup.tar.gz -C /data

# Restore dos modelos
docker run --rm -v docbr_ollama_data:/data -v $(pwd):/backup \
     alpine tar xzf /backup/ollama-backup.tar.gz -C /data
```

## 🔒 Segurança

### 1. Rede

```bash
# Use rede customizada
docker network create docbr-private
docker-compose --project-name docbr up -d
```

### 2. Variáveis Sensíveis

```bash
# Use secrets do Docker
echo "senha_secreta" | docker secret create db_password -

# Referencie no compose.yml
secrets:
  db_password:
    external: true
```

### 3. Imagens

```bash
# Use imagens específicas (não latest)
docker build -t docbr-rag:v1.0.0 .

# Scanneie vulnerabilidades
docker scan docbr-rag:v1.0.0
```

## 📈 Performance

### 1. GPU Support

Descomente no `docker-compose.yml`:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

### 2. Otimizações

```yaml
# Limite de memória
deploy:
  resources:
    limits:
      memory: 4G

# CPU limit
deploy:
  resources:
    limits:
      cpus: '2.0'
```

## 🧪 Testes

### Testes de Integração

```bash
# Teste completo via Docker
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Testes de carga
docker-compose run --rm docbr-tests \
     pytest tests/integration/ -v --benchmark-only
```

### Testes de Staging

```bash
# Ambiente de staging
docker-compose -f docker-compose.staging.yml up -d

# Testes automatizados
./scripts/test-staging.sh
```

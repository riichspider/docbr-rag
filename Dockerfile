# Dockerfile para docbr-rag
# Multi-stage build para otimização de tamanho

FROM python:3.11-slim as base

# Configura ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    git \
    zstd \
    && rm -rf /var/lib/apt/lists/*

# Instala Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Cria usuário não-root
RUN useradd -m -u 1000 docbr && \
    mkdir -p /app /home/docbr/.ollama && \
    chown -R docbr:docbr /app /home/docbr/.ollama

WORKDIR /app

# Stage de desenvolvimento
FROM base as development

# Copia requirements e instala dependências
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"

# Copia código fonte
COPY . .

# Muda para usuário não-root
USER docbr

# Expõe porta para API
EXPOSE 8000

# Comando padrão
CMD ["python", "-m", "src.docbr_rag.cli"]

# Stage de produção
FROM base as production

# Copia apenas requirements e instala dependências de produção
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Copia código fonte
COPY . .

# Muda para usuário não-root
USER docbr

# Baixa modelo LLM padrão (opcional - pode ser feito em runtime)
# RUN ollama pull llama3.2:3b

# Expõe porta para API
EXPOSE 8000

# Volume para dados persistentes
VOLUME ["/app/data", "/home/docbr/.ollama"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Comando padrão para API
CMD ["uvicorn", "src.docbr_rag.api_rest:app", "--host", "0.0.0.0", "--port", "8000"]

# Stage de CLI
FROM base as cli

# Instala dependências
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Copia código
COPY . .

# Muda para usuário não-root
USER docbr

# Comando para CLI
CMD ["python", "-m", "src.docbr_rag.cli"]

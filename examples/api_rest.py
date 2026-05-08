"""
Exemplo de API REST simples usando FastAPI.
Expõe endpoints para indexação e consulta de documentos.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import tempfile
import shutil
from typing import List, Optional

from src.docbr_rag import DocBR, Resposta
from src.docbr_rag.models import DocumentoInfo

# Inicializa FastAPI
app = FastAPI(
    title="docbr-rag API",
    description="API REST para RAG especializado em documentos brasileiros",
    version="0.1.0"
)

# Instância global do DocBR
docbr = DocBR(
    model_name="all-MiniLM-L6-v2",
    llm_model="llama3.2:3b",
    db_path="./api_db"
)


@app.get("/")
async def root():
    """Endpoint raiz com informações da API."""
    return {
        "nome": "docbr-rag API",
        "versao": "0.1.0",
        "descricao": "RAG especializado em documentos brasileiros",
        "endpoints": {
            "indexar": "POST /indexar",
            "consultar": "POST /consultar",
            "listar": "GET /documentos",
            "limpar": "DELETE /documentos"
        }
    }


@app.post("/indexar")
async def indexar_documento(file: UploadFile = File(...)):
    """
    Indexa um arquivo PDF enviado via upload.

    Args:
        file: Arquivo PDF enviado via multipart/form-data

    Returns:
        Informações do documento indexado
    """
    # Validação do arquivo
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Arquivo deve ser PDF")

    # Salva temporariamente
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        # Indexa o documento
        doc_info = docbr.indexar_documento(tmp_path)

        return {
            "status": "sucesso",
            "documento": {
                "tipo": doc_info.tipo.value,
                "nome": file.filename,
                "paginas": doc_info.total_paginas,
                "chunks": doc_info.total_chunks,
                "indexado": doc_info.indexado
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao indexar: {str(e)}")

    finally:
        # Remove arquivo temporário
        Path(tmp_path).unlink(missing_ok=True)


@app.post("/consultar")
async def consultar_documentos(
    pergunta: str,
    n_resultados: Optional[int] = 5,
    temperatura: Optional[float] = 0.7
):
    """
    Realiza consulta nos documentos indexados.

    Args:
        pergunta: Pergunta sobre os documentos
        n_resultados: Número de chunks relevantes
        temperatura: Temperatura para geração

    Returns:
        Resposta gerada com metadados
    """
    try:
        resposta = docbr.consultar(
            pergunta=pergunta,
            n_resultados=n_resultados,
            temperatura=temperatura
        )

        return {
            "status": "sucesso",
            "pergunta": pergunta,
            "resposta": {
                "texto": resposta.texto,
                "fonte": resposta.fonte,
                "paginas": resposta.paginas_referenciadas,
                "confianca": resposta.confianca
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro na consulta: {str(e)}")


@app.get("/documentos")
async def listar_documentos():
    """Lista todos os documentos indexados."""
    try:
        documentos = docbr.listar_documentos()

        return {
            "status": "sucesso",
            "total": len(documentos),
            "documentos": [
                {
                    "tipo": doc.tipo.value,
                    "caminho": doc.caminho,
                    "paginas": doc.total_paginas,
                    "chunks": doc.total_chunks,
                    "indexado": doc.indexado
                }
                for doc in documentos
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao listar: {str(e)}")


@app.delete("/documentos")
async def limpar_documentos(confirmar: bool = False):
    """
    Remove todos os documentos do banco de dados.

    Args:
        confirmar: Confirmação obrigatória para evitar exclusão acidental
    """
    if not confirmar:
        raise HTTPException(
            status_code=400,
            detail="Envie ?confirmar=true para realmente limpar o banco"
        )

    try:
        docbr.limpar_database()

        return {
            "status": "sucesso",
            "mensagem": "Banco de dados limpo com sucesso"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao limpar: {str(e)}")


@app.get("/health")
async def health_check():
    """Verifica saúde da API e dependências."""
    try:
        # Testa listagem de documentos (operação leve)
        docbr.listar_documentos()

        return {
            "status": "saudavel",
            "servicos": {
                "docbr_rag": "online",
                "chromadb": "online",
                "sentence_transformers": "online"
            }
        }

    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "erro",
                "erro": str(e)
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

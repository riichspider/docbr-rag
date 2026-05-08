"""
Módulo principal do docbr-rag.
Implementa a classe DocBR que orquestra todo o processo RAG.
"""

from pathlib import Path
from typing import Optional, List
import chromadb
from sentence_transformers import SentenceTransformer
import ollama

from .models import Resposta, DocumentoInfo, TipoDocumento, Chunk
from .extractors import extrair_texto_pdf, criar_chunks, detectar_tipo
from .exceptions import (
    DocumentProcessingError, PDFExtractionError, EmbeddingGenerationError,
    VectorDBError, LLMError, OllamaConnectionError, ModelNotFoundError
)
from .logging_config import get_logger, log_performance, DocBRLoggerAdapter


class DocBR:
    """
    Classe principal para processamento de documentos brasileiros com RAG.

    Gerencia extração, indexação e consulta de documentos de forma 100% local.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        llm_model: str = "llama3.2:3b",
        db_path: str = "./docbr_db",
        chunk_size: int = 500,
        chunk_overlap: int = 100,
    ):
        """
        Inicializa o sistema RAG.

        Args:
            model_name: Modelo de embeddings para busca semântica
            llm_model: Modelo de linguagem para geração de respostas
            db_path: Caminho para o banco de dados vetorial
            chunk_size: Tamanho dos chunks de texto
            chunk_overlap: Sobreposição entre chunks
        """
        # Inicializa logger
        self.logger = DocBRLoggerAdapter(
            get_logger("docbr_rag.core"),
            {"component": "DocBR"}
        )

        self.model_name = model_name
        self.llm_model = llm_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self.logger.info(
            f"Inicializando DocBR com model={model_name}, llm={llm_model}")

        try:
            # Inicializa modelo de embeddings
            self.logger.debug(f"Carregando modelo de embeddings: {model_name}")
            self.embedding_model = SentenceTransformer(model_name)
            self.logger.info("Modelo de embeddings carregado com sucesso")

            # Inicializa banco de dados vetorial
            self.logger.debug(f"Inicializando ChromaDB em: {db_path}")
            self.client = chromadb.PersistentClient(path=db_path)
            self.collection = self.client.get_or_create_collection(
                name="documentos_br",
                metadata={"hnsw:space": "cosine"}
            )
            self.logger.info("Banco de dados vetorial inicializado")

            self._documentos_indexados: List[DocumentoInfo] = []

        except Exception as e:
            self.logger.error(f"Erro na inicialização: {e}", exc_info=True)
            raise DocumentProcessingError(
                f"Falha na inicialização do DocBR: {e}") from e

    @log_performance(get_logger("docbr_rag.core"))
    def indexar_documento(self, caminho_pdf: str | Path) -> DocumentoInfo:
        """
        Indexa um documento PDF para consulta.

        Args:
            caminho_pdf: Caminho para o arquivo PDF

        Returns:
            DocumentoInfo com informações do documento indexado
        """
        caminho = Path(caminho_pdf)

        self.logger.info(f"Iniciando indexação do documento: {caminho.name}")

        try:
            # Extrai texto do PDF
            self.logger.debug("Extraindo texto do PDF")
            paginas = extrair_texto_pdf(caminho)
            self.logger.info(f"Extraídas {len(paginas)} páginas")

            # Detecta tipo de documento
            self.logger.debug("Detectando tipo de documento")
            texto_completo = " ".join(texto for _, texto in paginas)
            tipo = detectar_tipo(texto_completo)
            self.logger.info(f"Tipo detectado: {tipo.value}")

            # Cria chunks
            self.logger.debug(
                f"Criando chunks (size={self.chunk_size}, overlap={self.chunk_overlap})")
            chunks = criar_chunks(
                paginas,
                tamanho_chunk=self.chunk_size,
                sobreposicao=self.chunk_overlap,
                tipo=tipo
            )
            self.logger.info(f"Criados {len(chunks)} chunks")

            # Gera embeddings
            self.logger.debug("Gerando embeddings")
            textos = [chunk.texto for chunk in chunks]
            embeddings = self.embedding_model.encode(textos)
            self.logger.debug("Embeddings gerados com sucesso")

            # Prepara metadados para ChromaDB
            ids = [f"{caminho.stem}_chunk_{i}" for i in range(len(chunks))]
            metadados = [
                {
                    "pagina": chunk.pagina,
                    "documento": str(caminho),
                    "tipo_documento": tipo.value,
                    "chunk_indice": chunk.indice,
                    **chunk.metadata
                }
                for chunk in chunks
            ]

            # Adiciona ao banco de dados
            self.logger.debug("Adicionando ao ChromaDB")
            self.collection.add(
                documents=textos,
                embeddings=embeddings.tolist(),
                metadatas=metadados,
                ids=ids
            )

            # Cria informações do documento
            doc_info = DocumentoInfo(
                tipo=tipo,
                caminho=str(caminho),
                total_paginas=len(paginas),
                total_chunks=len(chunks),
                indexado=True
            )

            self._documentos_indexados.append(doc_info)
            self.logger.info(f"Documento indexado com sucesso: {caminho.name}")

            return doc_info

        except FileNotFoundError as e:
            self.logger.error(f"Arquivo não encontrado: {caminho}")
            raise PDFExtractionError(
                f"Arquivo não encontrado: {caminho}", str(caminho), e) from e
        except Exception as e:
            self.logger.error(
                f"Erro na indexação de {caminho}: {e}", exc_info=True)
            raise DocumentProcessingError(
                f"Erro processando {caminho}: {e}", str(caminho), e) from e

    def consultar(
        self,
        pergunta: str,
        n_resultados: int = 5,
        temperatura: float = 0.7,
    ) -> Resposta:
        """
        Realiza consulta RAG sobre os documentos indexados.

        Args:
            pergunta: Pergunta do usuário
            n_resultados: Número de chunks relevantes para recuperar
            temperatura: Temperatura para geração de resposta

        Returns:
            Resposta gerada com fontes e confiança
        """
        # Gera embedding da pergunta
        pergunta_embedding = self.embedding_model.encode([pergunta])

        # Busca chunks relevantes
        resultados = self.collection.query(
            query_embeddings=pergunta_embedding.tolist(),
            n_results=n_resultados
        )

        if not resultados["documents"][0]:
            return Resposta(
                texto="Nenhum documento relevante encontrado para sua pergunta.",
                confianca=0.0
            )

        # Prepara contexto
        contextos = resultados["documents"][0]
        metadados = resultados["metadados"][0]
        paginas_referenciadas = list(set(meta["pagina"] for meta in metadados))

        # Constrói prompt
        prompt = self._construir_prompt(pergunta, contextos, metadados)

        # Gera resposta com LLM local
        try:
            response = ollama.generate(
                model=self.llm_model,
                prompt=prompt,
                options={"temperature": temperatura}
            )
            texto_resposta = response["response"]
            confianca = self._calcular_confianca(contextos, pergunta)
        except Exception as e:
            return Resposta(
                texto=f"Erro ao gerar resposta: {str(e)}",
                confianca=0.0
            )

        return Resposta(
            texto=texto_resposta,
            fonte="Documentos indexados localmente",
            paginas_referenciadas=paginas_referenciadas,
            confianca=confianca
        )

    def listar_documentos(self) -> List[DocumentoInfo]:
        """Retorna lista de documentos indexados."""
        return self._documentos_indexados.copy()

    def limpar_database(self) -> None:
        """Remove todos os documentos do banco de dados."""
        self.client.delete_collection("documentos_br")
        self.collection = self.client.get_or_create_collection(
            name="documentos_br",
            metadata={"hnsw:space": "cosine"}
        )
        self._documentos_indexados.clear()

    def _construir_prompt(
        self,
        pergunta: str,
        contextos: List[str],
        metadados: List[dict]
    ) -> str:
        """Constrói prompt para o LLM com contexto e pergunta."""
        contexto_formatado = "\n\n".join(
            f"Contexto {i+1} (página {meta['pagina']}, {meta['tipo_documento']}):\n{ctx}"
            for i, (ctx, meta) in enumerate(zip(contextos, metadados))
        )

        prompt = f"""
Você é um assistente especializado em documentos brasileiros. Use apenas o contexto fornecido para responder à pergunta.

Contexto:
{contexto_formatado}

Pergunta: {pergunta}

Responda de forma clara e objetiva, citando as páginas relevantes quando possível. Se a informação não estiver no contexto, informe que não conseguiu encontrar a resposta nos documentos disponíveis.
"""
        return prompt

    def _calcular_confianca(
        self,
        contextos: List[str],
        pergunta: str
    ) -> float:
        """Calcula confiança da resposta baseada na relevância do contexto."""
        if not contextos:
            return 0.0

        # Simplificado: baseado na quantidade e tamanho do contexto
        total_caracteres = sum(len(ctx) for ctx in contextos)
        confianca_base = min(total_caracteres / 1000, 1.0)

        # Ajuste baseado na quantidade de contextos
        fator_qtd = min(len(contextos) / 3, 1.0)

        return round(confianca_base * fator_qtd, 2)

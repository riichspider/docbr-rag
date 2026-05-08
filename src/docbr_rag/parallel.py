"""
Processamento paralelo para grandes documentos no docbr-rag.
Otimiza performance com multiprocessing e threading.
"""

import concurrent.futures
import multiprocessing as mp
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional, Callable
import time
import threading
from dataclasses import dataclass

from .models import Chunk, TipoDocumento
from .logging_config import get_logger
from .monitoring import monitor_operation


@dataclass
class ParallelConfig:
    """Configuração para processamento paralelo."""
    max_workers: Optional[int] = None
    chunk_size: int = 1000
    use_processes: bool = True
    timeout_seconds: int = 300


class ParallelProcessor:
    """Processador paralelo para documentos grandes."""
    
    def __init__(self, config: Optional[ParallelConfig] = None):
        """
        Inicializa processador paralelo.
        
        Args:
            config: Configuração de processamento
        """
        self.config = config or ParallelConfig()
        self.logger = get_logger("docbr_rag.parallel")
        
        # Detecta número de workers
        if self.config.max_workers is None:
            self.config.max_workers = min(
                mp.cpu_count(),
                8  # Limite para não sobrecarregar
            )
        
        self.logger.info(
            f"Processador paralelo inicializado: {self.config.max_workers} workers"
        )
    
    def process_documents_parallel(
        self,
        documentos: List[str | Path],
        process_func: Callable,
        *args,
        **kwargs
    ) -> List[Any]:
        """
        Processa múltiplos documentos em paralelo.
        
        Args:
            documentos: Lista de caminhos de documentos
            process_func: Função de processamento
            *args: Argumentos posicionais para process_func
            **kwargs: Argumentos nomeados para process_func
            
        Returns:
            Lista de resultados
        """
        if len(documentos) == 1:
            # Para documento único, não vale a pena o overhead
            return [process_func(documentos[0], *args, **kwargs)]
        
        self.logger.info(
            f"Processando {len(documentos)} documentos em paralelo "
            f"com {self.config.max_workers} workers"
        )
        
        operation_id = monitor_operation("parallel_processing")
        
        try:
            # Escolhe executor baseado na configuração
            if self.config.use_processes:
                executor_class = concurrent.futures.ProcessPoolExecutor
            else:
                executor_class = concurrent.futures.ThreadPoolExecutor
            
            with executor_class(max_workers=self.config.max_workers) as executor:
                # Envia tarefas
                future_to_doc = {
                    executor.submit(
                        self._process_with_timeout,
                        process_func,
                        doc,
                        *args,
                        **kwargs
                    ): doc
                    for doc in documentos
                }
                
                # Coleta resultados
                resultados = []
                for future in concurrent.futures.as_completed(
                    future_to_doc,
                    timeout=self.config.timeout_seconds
                ):
                    doc = future_to_doc[future]
                    try:
                        resultado = future.result()
                        resultados.append(resultado)
                        self.logger.debug(f"Documento {doc} processado com sucesso")
                    except Exception as e:
                        self.logger.error(f"Erro processando {doc}: {e}")
                        resultados.append(None)
            
            monitor_operation(operation_id, success=True)
            return resultados
            
        except Exception as e:
            monitor_operation(operation_id, success=False, error_message=str(e))
            raise
    
    def _process_with_timeout(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Executa função com timeout.
        
        Args:
            func: Função a executar
            *args: Argumentos posicionais
            **kwargs: Argumentos nomeados
            
        Returns:
            Resultado da função
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Erro na execução paralela: {e}")
            raise
    
    def process_large_document_chunks(
        self,
        paginas: List[Tuple[int, str]],
        chunk_func: Callable,
        *args,
        **kwargs
    ) -> List[Chunk]:
        """
        Processa chunks de documento grande em paralelo.
        
        Args:
            paginas: Lista de páginas do documento
            chunk_func: Função de chunking
            *args: Argumentos para chunk_func
            **kwargs: Argumentos para chunk_func
            
        Returns:
            Lista de chunks processados
        """
        if len(paginas) < 10:
            # Para documentos pequenos, processamento sequencial
            return chunk_func(paginas, *args, **kwargs)
        
        self.logger.info(
            f"Processando {len(paginas)} páginas em paralelo "
            f"com {self.config.max_workers} workers"
        )
        
        operation_id = monitor_operation("parallel_chunking")
        
        try:
            # Divide páginas em batches para workers
            batch_size = max(1, len(paginas) // self.config.max_workers)
            batches = [
                paginas[i:i + batch_size]
                for i in range(0, len(paginas), batch_size)
            ]
            
            # Processa batches em paralelo
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.config.max_workers
            ) as executor:
                
                future_to_batch = {
                    executor.submit(chunk_func, batch, *args, **kwargs): batch
                    for batch in batches
                }
                
                # Coleta resultados
                all_chunks = []
                for future in concurrent.futures.as_completed(
                    future_to_batch,
                    timeout=self.config.timeout_seconds
                ):
                    batch = future_to_batch[future]
                    try:
                        chunks = future.result()
                        all_chunks.extend(chunks)
                    except Exception as e:
                        self.logger.error(f"Erro no batch: {e}")
            
            monitor_operation(operation_id, success=True)
            return all_chunks
            
        except Exception as e:
            monitor_operation(operation_id, success=False, error_message=str(e))
            raise
    
    def parallel_embedding_generation(
        self,
        textos: List[str],
        embedding_model,
        batch_size: Optional[int] = None
    ) -> List[List[float]]:
        """
        Gera embeddings em paralelo.
        
        Args:
            textos: Lista de textos para embeddar
            embedding_model: Modelo de embeddings
            batch_size: Tamanho do batch (opcional)
            
        Returns:
            Lista de embeddings
        """
        if len(textos) < 10:
            # Para poucos textos, processamento sequencial
            return embedding_model.encode(textos)
        
        batch_size = batch_size or self.config.chunk_size
        self.logger.info(
            f"Gerando embeddings para {len(textos)} textos "
            f"em batches de {batch_size}"
        )
        
        operation_id = monitor_operation("parallel_embeddings")
        
        try:
            # Divide em batches
            batches = [
                textos[i:i + batch_size]
                for i in range(0, len(textos), batch_size)
            ]
            
            # Processa batches em paralelo
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.config.max_workers
            ) as executor:
                
                future_to_batch = {
                    executor.submit(embedding_model.encode, batch): batch
                    for batch in batches
                }
                
                # Coleta resultados
                all_embeddings = []
                for future in concurrent.futures.as_completed(
                    future_to_batch,
                    timeout=self.config.timeout_seconds
                ):
                    try:
                        embeddings = future.result()
                        all_embeddings.extend(embeddings)
                    except Exception as e:
                        self.logger.error(f"Erro no batch de embeddings: {e}")
            
            monitor_operation(operation_id, success=True)
            return all_embeddings
            
        except Exception as e:
            monitor_operation(operation_id, success=False, error_message=str(e))
            raise


class DocumentBatchProcessor:
    """Processador de lotes de documentos com otimizações."""
    
    def __init__(self, parallel_config: Optional[ParallelConfig] = None):
        """
        Inicializa processador de lotes.
        
        Args:
            parallel_config: Configuração paralela
        """
        self.parallel_processor = ParallelProcessor(parallel_config)
        self.logger = get_logger("docbr_rag.batch_processor")
    
    def process_document_batch(
        self,
        documentos: List[str | Path],
        extract_func: Callable,
        chunk_func: Callable,
        embedding_model,
        tipo_detector: Optional[Callable] = None,
        **kwargs
    ) -> Tuple[List[Dict], List[List[float]]]:
        """
        Processa lote de documentos completo.
        
        Args:
            documentos: Lista de documentos
            extract_func: Função de extração
            chunk_func: Função de chunking
            embedding_model: Modelo de embeddings
            tipo_detector: Função de detecção de tipo (opcional)
            **kwargs: Argumentos adicionais
            
        Returns:
            Tupla (metadados, embeddings)
        """
        self.logger.info(f"Processando lote de {len(documentos)} documentos")
        
        start_time = time.time()
        operation_id = monitor_operation("batch_processing")
        
        try:
            # Etapa 1: Extração paralela
            self.logger.info("Etapa 1: Extração de texto")
            extracoes = self.parallel_processor.process_documents_parallel(
                documentos,
                self._extract_with_metadata,
                extract_func,
                tipo_detector
            )
            
            # Filtra extrações com erro
            extracoes_validas = [
                ext for ext in extracoes if ext and not ext.get("erro")
            ]
            
            if not extracoes_validas:
                self.logger.warning("Nenhuma extração válida no lote")
                monitor_operation(operation_id, success=False)
                return [], []
            
            # Etapa 2: Chunking paralelo
            self.logger.info("Etapa 2: Chunking dos documentos")
            chunks_por_documento = []
            
            for extracao in extracoes_validas:
                chunks = chunk_func(
                    extracao["paginas"],
                    **extracao.get("chunk_args", {})
                )
                chunks_por_documento.append(chunks)
            
            # Achata todos os chunks
            todos_chunks = [chunk for chunks in chunks_por_documento for chunk in chunks]
            
            # Etapa 3: Embeddings paralelas
            self.logger.info("Etapa 3: Geração de embeddings")
            textos_chunks = [chunk.texto for chunk in todos_chunks]
            
            if textos_chunks:
                embeddings = self.parallel_processor.parallel_embedding_generation(
                    textos_chunks,
                    embedding_model
                )
            else:
                embeddings = []
            
            # Prepara metadados
            metadados = []
            chunk_index = 0
            
            for i, extracao in enumerate(extracoes_validas):
                chunks_doc = chunks_por_documento[i]
                
                for chunk in chunks_doc:
                    metadado = {
                        "documento": str(extracao["caminho"]),
                        "pagina": chunk.pagina,
                        "tipo_documento": extracao.get("tipo", "desconhecido"),
                        "chunk_indice": chunk.indice,
                        "batch_index": i,
                        **chunk.metadata,
                        **extracao.get("metadados", {})
                    }
                    metadados.append(metadado)
                    chunk_index += 1
            
            processing_time = time.time() - start_time
            self.logger.info(
                f"Lote processado em {processing_time:.2f}s: "
                f"{len(extracoes_validas)}/{len(documentos)} documentos, "
                f"{len(todos_chunks)} chunks, {len(embeddings)} embeddings"
            )
            
            monitor_operation(operation_id, success=True)
            return metadados, embeddings
            
        except Exception as e:
            monitor_operation(operation_id, success=False, error_message=str(e))
            self.logger.error(f"Erro no processamento do lote: {e}")
            raise
    
    def _extract_with_metadata(
        self,
        caminho: str | Path,
        extract_func: Callable,
        tipo_detector: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Extrai texto e metadados de um documento.
        
        Args:
            caminho: Caminho do documento
            extract_func: Função de extração
            tipo_detector: Função de detecção de tipo
            
        Returns:
            Dicionário com extração e metadados
        """
        try:
            # Extrai texto
            paginas = extract_func(caminho)
            
            # Detecta tipo
            tipo = TipoDocumento.DESCONHECIDO
            if tipo_detector:
                texto_completo = " ".join(texto for _, texto in paginas)
                tipo = tipo_detector(texto_completo)
            
            return {
                "caminho": str(caminho),
                "paginas": paginas,
                "tipo": tipo.value,
                "total_paginas": len(paginas),
                "metadados": {
                    "arquivo": Path(caminho).name,
                    "tamanho": Path(caminho).stat().st_size
                }
            }
            
        except Exception as e:
            return {
                "caminho": str(caminho),
                "erro": str(e),
                "paginas": [],
                "tipo": "erro",
                "total_paginas": 0
            }


# Funções utilitárias
def create_optimal_config(
    total_documents: int,
    total_pages: int,
    available_memory_gb: float = 8.0
) -> ParallelConfig:
    """
    Cria configuração ótima baseada nos recursos.
    
    Args:
        total_documents: Número total de documentos
        total_pages: Número total de páginas
        available_memory_gb: Memória disponível em GB
        
    Returns:
        Configuração otimizada
    """
    # Estima uso de memória por documento
    avg_pages_per_doc = total_pages / max(1, total_documents)
    estimated_memory_per_doc_mb = avg_pages_per_doc * 0.5  # Estimativa
    
    # Calcula workers baseados na memória
    max_workers_by_memory = max(
        1,
        int((available_memory_gb * 1024 * 0.7) / estimated_memory_per_doc_mb)
    )
    
    # Calcula workers baseados no CPU
    max_workers_by_cpu = min(mp.cpu_count(), 8)
    
    # Escolhe o menor limitante
    max_workers = min(max_workers_by_memory, max_workers_by_cpu)
    
    # Ajusta chunk size baseado no tamanho
    if total_pages > 1000:
        chunk_size = 200
    elif total_pages > 500:
        chunk_size = 500
    else:
        chunk_size = 1000
    
    return ParallelConfig(
        max_workers=max_workers,
        chunk_size=chunk_size,
        use_processes=total_documents > 5,  # Processos para muitos documentos
        timeout_seconds=max(300, total_pages * 0.1)  # Timeout proporcional
    )


def monitor_parallel_resources():
    """
    Monitora recursos durante processamento paralelo.
    
    Returns:
        Dicionário com informações de recursos
    """
    import psutil
    
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "memory_available_gb": psutil.virtual_memory().available / (1024**3),
        "active_threads": threading.active_count(),
        "process_count": len(psutil.pids()),
    }

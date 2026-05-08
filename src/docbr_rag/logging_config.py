"""
Configuração de logging para o docbr-rag.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> None:
    """
    Configura logging para a aplicação.
    
    Args:
        level: Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Caminho para arquivo de log (opcional)
        format_string: Formato personalizado (opcional)
    """
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )
    
    # Configura nível
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configura formatters
    formatter = logging.Formatter(format_string)
    
    # Remove handlers existentes
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(numeric_level)
    root_logger.addHandler(console_handler)
    
    # File handler (se especificado)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(numeric_level)
        root_logger.addHandler(file_handler)
    
    # Configura nível do logger raiz
    root_logger.setLevel(numeric_level)
    
    # Configura loggers específicos
    _configure_specific_loggers(numeric_level)


def _configure_specific_loggers(level: int) -> None:
    """Configura loggers específicos com níveis apropriados."""
    # Logger para PDF processing
    pdf_logger = logging.getLogger("docbr_rag.extractors.pdf")
    pdf_logger.setLevel(level)
    
    # Logger para core functionality
    core_logger = logging.getLogger("docbr_rag.core")
    core_logger.setLevel(level)
    
    # Logger para CLI
    cli_logger = logging.getLogger("docbr_rag.cli")
    cli_logger.setLevel(level)
    
    # Reduz verbosidade de bibliotecas externas
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("ollama").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Obtém um logger configurado.
    
    Args:
        name: Nome do logger
        
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)


class DocBRLoggerAdapter(logging.LoggerAdapter):
    """
    Adapter para adicionar contexto específico do docbr-rag aos logs.
    """
    
    def __init__(self, logger: logging.Logger, extra: Optional[dict] = None):
        super().__init__(logger, extra or {})
    
    def process(self, msg, kwargs):
        # Adiciona contexto do documento se disponível
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        
        kwargs['extra'].update(self.extra)
        return msg, kwargs


def log_function_call(logger: logging.Logger):
    """
    Decorator para logar chamadas de função.
    
    Args:
        logger: Logger para usar
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(
                f"Chamando {func.__name__} com args={args}, kwargs={kwargs}"
            )
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} executado com sucesso")
                return result
            except Exception as e:
                logger.error(f"Erro em {func.__name__}: {e}", exc_info=True)
                raise
        return wrapper
    return decorator


def log_performance(logger: logging.Logger):
    """
    Decorator para medir performance de funções.
    
    Args:
        logger: Logger para usar
    """
    import time
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(
                    f"{func.__name__} executado em {execution_time:.2f}s"
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"{func.__name__} falhou após {execution_time:.2f}s: {e}"
                )
                raise
        return wrapper
    return decorator

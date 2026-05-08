"""
Exceções customizadas para o docbr-rag.
"""


class DocBRError(Exception):
    """Classe base para exceções do docbr-rag."""
    pass


class DocumentProcessingError(DocBRError):
    """Erro no processamento de documentos."""
    
    def __init__(self, message: str, file_path: str = None, original_error: Exception = None):
        self.file_path = file_path
        self.original_error = original_error
        super().__init__(message)
    
    def __str__(self):
        if self.file_path:
            return f"Erro processando '{self.file_path}': {super().__str__()}"
        return super().__str__()


class PDFExtractionError(DocumentProcessingError):
    """Erro na extração de texto de PDF."""
    pass


class DocumentTypeDetectionError(DocumentProcessingError):
    """Erro na detecção de tipo de documento."""
    pass


class ChunkingError(DocumentProcessingError):
    """Erro no processo de chunking."""
    pass


class EmbeddingGenerationError(DocBRError):
    """Erro na geração de embeddings."""
    pass


class VectorDBError(DocBRError):
    """Erro no banco de dados vetorial."""
    pass


class LLMError(DocBRError):
    """Erro no modelo de linguagem."""
    
    def __init__(self, message: str, model_name: str = None, original_error: Exception = None):
        self.model_name = model_name
        self.original_error = original_error
        super().__init__(message)
    
    def __str__(self):
        if self.model_name:
            return f"Erro no LLM '{self.model_name}': {super().__str__()}"
        return super().__str__()


class ConfigurationError(DocBRError):
    """Erro na configuração do sistema."""
    pass


class ValidationError(DocBRError):
    """Erro de validação de dados."""
    pass


class ModelNotFoundError(DocBRError):
    """Erro quando modelo não é encontrado."""
    
    def __init__(self, model_type: str, model_name: str):
        self.model_type = model_type
        self.model_name = model_name
        super().__init__(f"{model_type} '{model_name}' não encontrado")


class OllamaConnectionError(LLMError):
    """Erro de conexão com Ollama."""
    pass


class ChromaDBConnectionError(VectorDBError):
    """Erro de conexão com ChromaDB."""
    pass

"""
Sistema de configuração para o docbr-rag.
Suporta configuração via arquivo YAML, variáveis de ambiente e valores padrão.
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator

from .exceptions import ConfigurationError
from .logging_config import get_logger


class EmbeddingConfig(BaseModel):
    """Configuração do modelo de embeddings."""
    model_name: str = Field(default="all-MiniLM-L6-v2", description="Nome do modelo de embeddings")
    device: str = Field(default="cpu", description="Dispositivo (cpu/cuda)")
    batch_size: int = Field(default=32, description="Tamanho do batch")
    
    @validator('device')
    def validate_device(cls, v):
        if v not in ['cpu', 'cuda']:
            raise ValueError("Device deve ser 'cpu' ou 'cuda'")
        return v


class LLMConfig(BaseModel):
    """Configuração do modelo de linguagem."""
    model_name: str = Field(default="llama3.2:3b", description="Nome do modelo LLM")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperatura de geração")
    max_tokens: int = Field(default=2048, ge=1, description="Máximo de tokens")
    timeout: int = Field(default=60, ge=1, description="Timeout em segundos")
    
    @validator('temperature')
    def validate_temperature(cls, v):
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperatura deve estar entre 0.0 e 2.0")
        return v


class ChunkingConfig(BaseModel):
    """Configuração do processo de chunking."""
    chunk_size: int = Field(default=500, ge=50, le=2000, description="Tamanho dos chunks")
    chunk_overlap: int = Field(default=100, ge=0, le=500, description="Sobreposição dos chunks")
    
    @validator('chunk_overlap')
    def validate_overlap(cls, v, values):
        if 'chunk_size' in values and v >= values['chunk_size']:
            raise ValueError("Overlap deve ser menor que chunk_size")
        return v


class DatabaseConfig(BaseModel):
    """Configuração do banco de dados."""
    path: str = Field(default="./docbr_db", description="Caminho para o banco de dados")
    collection_name: str = Field(default="documentos_br", description="Nome da collection")
    distance_metric: str = Field(default="cosine", description="Métrica de distância")
    
    @validator('distance_metric')
    def validate_distance_metric(cls, v):
        valid_metrics = ['cosine', 'l2', 'ip']
        if v not in valid_metrics:
            raise ValueError(f"Métrica deve ser uma de: {valid_metrics}")
        return v


class LoggingConfig(BaseModel):
    """Configuração de logging."""
    level: str = Field(default="INFO", description="Nível de log")
    file_path: Optional[str] = Field(default=None, description="Arquivo de log")
    format_string: Optional[str] = Field(default=None, description="Formato do log")
    
    @validator('level')
    def validate_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Nível deve ser um de: {valid_levels}")
        return v.upper()


class DocBRConfig(BaseModel):
    """Configuração principal do DocBR."""
    embeddings: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    model_config = {"extra": "forbid"}  # Não permite campos extras


class ConfigManager:
    """Gerenciador de configuração do DocBR."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Inicializa o gerenciador de configuração.
        
        Args:
            config_file: Caminho para arquivo de configuração YAML
        """
        self.logger = get_logger("docbr_rag.config")
        self.config_file = config_file
        self._config: Optional[DocBRConfig] = None
    
    def load_config(self) -> DocBRConfig:
        """
        Carrega configuração de múltiplas fontes.
        
        Ordem de prioridade:
        1. Variáveis de ambiente
        2. Arquivo de configuração
        3. Valores padrão
        
        Returns:
            Configuração carregada
        """
        try:
            # 1. Carrega valores padrão
            config_dict = {}
            
            # 2. Carrega do arquivo YAML (se existir)
            if self.config_file and Path(self.config_file).exists():
                self.logger.debug(f"Carregando configuração de: {self.config_file}")
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        config_dict.update(file_config)
            
            # 3. Sobrescreve com variáveis de ambiente
            env_config = self._load_from_env()
            config_dict = self._merge_configs(config_dict, env_config)
            
            # 4. Valida e cria objeto de configuração
            self._config = DocBRConfig(**config_dict)
            self.logger.info("Configuração carregada com sucesso")
            
            return self._config
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar configuração: {e}", exc_info=True)
            raise ConfigurationError(f"Falha ao carregar configuração: {e}") from e
    
    def _load_from_env(self) -> Dict[str, Any]:
        """Carrega configuração de variáveis de ambiente."""
        env_config = {}
        
        # Mapeamento de variáveis de ambiente
        env_mappings = {
            'DOCBR_EMBEDDING_MODEL': ('embeddings', 'model_name'),
            'DOCBR_EMBEDDING_DEVICE': ('embeddings', 'device'),
            'DOCBR_EMBEDDING_BATCH_SIZE': ('embeddings', 'batch_size'),
            
            'DOCBR_LLM_MODEL': ('llm', 'model_name'),
            'DOCBR_LLM_TEMPERATURE': ('llm', 'temperature'),
            'DOCBR_LLM_MAX_TOKENS': ('llm', 'max_tokens'),
            'DOCBR_LLM_TIMEOUT': ('llm', 'timeout'),
            
            'DOCBR_CHUNK_SIZE': ('chunking', 'chunk_size'),
            'DOCBR_CHUNK_OVERLAP': ('chunking', 'chunk_overlap'),
            
            'DOCBR_DB_PATH': ('database', 'path'),
            'DOCBR_DB_COLLECTION': ('database', 'collection_name'),
            'DOCBR_DB_DISTANCE': ('database', 'distance_metric'),
            
            'DOCBR_LOG_LEVEL': ('logging', 'level'),
            'DOCBR_LOG_FILE': ('logging', 'file_path'),
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Converte para o tipo apropriado
                converted_value = self._convert_env_value(key, value)
                
                if section not in env_config:
                    env_config[section] = {}
                env_config[section][key] = converted_value
                
                self.logger.debug(f"Variável de ambiente {env_var} -> {section}.{key} = {converted_value}")
        
        return env_config
    
    def _convert_env_value(self, key: str, value: str) -> Any:
        """Converte valor string para tipo apropriado."""
        # Campos que devem ser int
        int_fields = ['batch_size', 'max_tokens', 'timeout', 'chunk_size', 'chunk_overlap']
        if key in int_fields:
            return int(value)
        
        # Campos que devem ser float
        float_fields = ['temperature']
        if key in float_fields:
            return float(value)
        
        # Campos que devem ser bool (se existirem)
        # bool_fields = []
        # if key in bool_fields:
        #     return value.lower() in ('true', '1', 'yes', 'on')
        
        # Demais campos permanecem como string
        return value
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Mescla dois dicionários de configuração."""
        result = base.copy()
        
        for section, values in override.items():
            if section not in result:
                result[section] = {}
            elif not isinstance(result[section], dict):
                result[section] = {}
            
            result[section].update(values)
        
        return result
    
    def save_config(self, config: DocBRConfig, file_path: str) -> None:
        """
        Salva configuração em arquivo YAML.
        
        Args:
            config: Configuração para salvar
            file_path: Caminho do arquivo
        """
        try:
            config_dict = config.dict()
            
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            
            self.logger.info(f"Configuração salva em: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar configuração: {e}", exc_info=True)
            raise ConfigurationError(f"Falha ao salvar configuração: {e}") from e
    
    @property
    def config(self) -> DocBRConfig:
        """Retorna configuração carregada."""
        if self._config is None:
            return self.load_config()
        return self._config


# Instância global do gerenciador
_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_file: Optional[str] = None) -> ConfigManager:
    """
    Obtém instância do gerenciador de configuração.
    
    Args:
        config_file: Caminho para arquivo de configuração
        
    Returns:
        Instância do ConfigManager
    """
    global _config_manager
    
    if _config_manager is None or config_file is not None:
        _config_manager = ConfigManager(config_file)
    
    return _config_manager


def load_config(config_file: Optional[str] = None) -> DocBRConfig:
    """
    Carrega configuração usando o gerenciador global.
    
    Args:
        config_file: Caminho para arquivo de configuração
        
    Returns:
        Configuração carregada
    """
    return get_config_manager(config_file).load_config()


def create_default_config_file(file_path: str) -> None:
    """
    Cria arquivo de configuração com valores padrão.
    
    Args:
        file_path: Caminho do arquivo a ser criado
    """
    default_config = DocBRConfig()
    manager = ConfigManager()
    manager.save_config(default_config, file_path)
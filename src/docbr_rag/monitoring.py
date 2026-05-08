"""
Sistema de monitoramento e métricas para docbr-rag.
Coleta e exibe métricas de performance e uso.
"""

import time
import psutil
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json

from .logging_config import get_logger


@dataclass
class PerformanceMetric:
    """Métrica de performance individual."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """Métricas do sistema."""
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_available_gb: float
    disk_usage_percent: float
    disk_free_gb: float
    timestamp: datetime


@dataclass
class OperationMetrics:
    """Métricas de operação."""
    operation_type: str
    start_time: float
    end_time: float
    duration: float
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor:
    """Monitor de performance para docbr-rag."""
    
    def __init__(self, metrics_file: Optional[str] = None):
        """
        Inicializa o monitor.
        
        Args:
            metrics_file: Arquivo para persistir métricas
        """
        self.logger = get_logger("docbr_rag.monitoring")
        self.metrics_file = metrics_file or "./docbr_metrics.json"
        
        # Métricas em memória
        self.performance_metrics: List[PerformanceMetric] = []
        self.operation_metrics: List[OperationMetrics] = []
        self.system_metrics: List[SystemMetrics] = []
        
        # Contadores
        self._operation_count = 0
        self._error_count = 0
        self._total_processing_time = 0.0
        
        # Lock para thread safety
        self._lock = threading.Lock()
        
        # Carrega métricas persistidas
        self._load_metrics()
        
        # Inicia monitoramento do sistema
        self._start_system_monitoring()
    
    def start_operation(self, operation_type: str, metadata: Optional[Dict] = None) -> str:
        """
        Inicia monitoramento de operação.
        
        Args:
            operation_type: Tipo da operação
            metadata: Metadados adicionais
            
        Returns:
            ID da operação para finalização
        """
        operation_id = f"{operation_type}_{int(time.time() * 1000)}"
        
        with self._lock:
            self._operation_count += 1
        
        self.logger.debug(f"Iniciando operação {operation_id}: {operation_type}")
        
        return operation_id
    
    def end_operation(
        self, 
        operation_id: str, 
        success: bool = True, 
        error_message: Optional[str] = None,
        additional_metadata: Optional[Dict] = None
    ) -> float:
        """
        Finaliza monitoramento de operação.
        
        Args:
            operation_id: ID da operação
            success: Se a operação foi bem-sucedida
            error_message: Mensagem de erro (se aplicável)
            additional_metadata: Metadados adicionais
            
        Returns:
            Duração da operação em segundos
        """
        try:
            # Extrai informações do ID
            parts = operation_id.split('_')
            operation_type = '_'.join(parts[:-1])
            start_timestamp = float(parts[-1]) / 1000.0
            end_time = time.time()
            duration = end_time - start_timestamp
            
            # Cria métrica
            metadata = {"operation_id": operation_id}
            if additional_metadata:
                metadata.update(additional_metadata)
            
            operation_metric = OperationMetrics(
                operation_type=operation_type,
                start_time=start_timestamp,
                end_time=end_time,
                duration=duration,
                success=success,
                error_message=error_message,
                metadata=metadata
            )
            
            with self._lock:
                self.operation_metrics.append(operation_metric)
                self._total_processing_time += duration
                
                if not success:
                    self._error_count += 1
            
            # Registra métrica de performance
            self.record_metric(
                name=f"{operation_type}_duration",
                value=duration,
                unit="seconds",
                metadata={
                    "operation_type": operation_type,
                    "success": success,
                    **metadata
                }
            )
            
            self.logger.debug(
                f"Operação {operation_id} finalizada em {duration:.2f}s "
                f"({'sucesso' if success else 'erro'})"
            )
            
            return duration
            
        except Exception as e:
            self.logger.error(f"Erro ao finalizar operação {operation_id}: {e}")
            return 0.0
    
    def record_metric(
        self,
        name: str,
        value: float,
        unit: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Registra métrica de performance.
        
        Args:
            name: Nome da métrica
            value: Valor da métrica
            unit: Unidade da métrica
            metadata: Metadados adicionais
        """
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        with self._lock:
            self.performance_metrics.append(metric)
        
        # Mantém apenas últimas 1000 métricas em memória
        if len(self.performance_metrics) > 1000:
            with self._lock:
                self.performance_metrics = self.performance_metrics[-1000:]
    
    def get_system_metrics(self) -> SystemMetrics:
        """
        Coleta métricas do sistema.
        
        Returns:
            Métricas atuais do sistema
        """
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memória
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)
            memory_available_gb = memory.available / (1024**3)
            
            # Disco
            disk = psutil.disk_usage(Path.cwd().anchor)
            disk_usage_percent = disk.percent
            disk_free_gb = disk.free / (1024**3)
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_gb=memory_used_gb,
                memory_available_gb=memory_available_gb,
                disk_usage_percent=disk_usage_percent,
                disk_free_gb=disk_free_gb,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao coletar métricas do sistema: {e}")
            return SystemMetrics(
                cpu_percent=0.0, memory_percent=0.0, memory_used_gb=0.0,
                memory_available_gb=0.0, disk_usage_percent=0.0,
                disk_free_gb=0.0, timestamp=datetime.now()
            )
    
    def get_operation_stats(self, operation_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtém estatísticas de operações.
        
        Args:
            operation_type: Tipo específico de operação (opcional)
            
        Returns:
            Estatísticas das operações
        """
        with self._lock:
            operations = self.operation_metrics
            
            if operation_type:
                operations = [op for op in operations if op.operation_type == operation_type]
            
            if not operations:
                return {}
            
            durations = [op.duration for op in operations]
            successful_ops = [op for op in operations if op.success]
            failed_ops = [op for op in operations if not op.success]
            
            return {
                "total_operations": len(operations),
                "successful_operations": len(successful_ops),
                "failed_operations": len(failed_ops),
                "success_rate": len(successful_ops) / len(operations) * 100,
                "avg_duration": sum(durations) / len(durations),
                "min_duration": min(durations),
                "max_duration": max(durations),
                "total_processing_time": sum(durations),
                "operations_per_hour": len(operations) / max(1, (time.time() - operations[0].start_time) / 3600)
            }
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Obtém resumo de performance.
        
        Args:
            hours: Período em horas para análise
            
        Returns:
            Resumo de métricas
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            recent_metrics = [
                m for m in self.performance_metrics 
                if m.timestamp > cutoff_time
            ]
            
            recent_operations = [
                op for op in self.operation_metrics 
                if datetime.fromtimestamp(op.end_time) > cutoff_time
            ]
        
        # Agrupa métricas por nome
        metrics_by_name = {}
        for metric in recent_metrics:
            if metric.name not in metrics_by_name:
                metrics_by_name[metric.name] = []
            metrics_by_name[metric.name].append(metric.value)
        
        # Calcula estatísticas
        summary = {
            "period_hours": hours,
            "total_metrics": len(recent_metrics),
            "total_operations": len(recent_operations),
            "unique_metric_names": len(metrics_by_name),
            "metrics_summary": {}
        }
        
        for name, values in metrics_by_name.items():
            if values:
                summary["metrics_summary"][name] = {
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "latest": values[-1]
                }
        
        return summary
    
    def export_metrics(self, filepath: str) -> None:
        """
        Exporta métricas para arquivo JSON.
        
        Args:
            filepath: Caminho do arquivo de exportação
        """
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "performance_metrics": [
                    {
                        "name": m.name,
                        "value": m.value,
                        "unit": m.unit,
                        "timestamp": m.timestamp.isoformat(),
                        "metadata": m.metadata
                    }
                    for m in self.performance_metrics[-500:]  # Últimas 500
                ],
                "operation_metrics": [
                    {
                        "operation_type": op.operation_type,
                        "start_time": op.start_time,
                        "end_time": op.end_time,
                        "duration": op.duration,
                        "success": op.success,
                        "error_message": op.error_message,
                        "metadata": op.metadata
                    }
                    for op in self.operation_metrics[-100:]  # Últimas 100
                ],
                "system_metrics": [
                    {
                        "cpu_percent": sm.cpu_percent,
                        "memory_percent": sm.memory_percent,
                        "memory_used_gb": sm.memory_used_gb,
                        "memory_available_gb": sm.memory_available_gb,
                        "disk_usage_percent": sm.disk_usage_percent,
                        "disk_free_gb": sm.disk_free_gb,
                        "timestamp": sm.timestamp.isoformat()
                    }
                    for sm in self.system_metrics[-50:]  # Últimas 50
                ]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Métricas exportadas para: {filepath}")
            
        except Exception as e:
            self.logger.error(f"Erro ao exportar métricas: {e}")
    
    def _load_metrics(self) -> None:
        """Carrega métricas persistidas."""
        try:
            if Path(self.metrics_file).exists():
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Carrega métricas de sistema (mais recentes)
                for sm_data in data.get("system_metrics", [])[-20:]:
                    self.system_metrics.append(SystemMetrics(
                        cpu_percent=sm_data["cpu_percent"],
                        memory_percent=sm_data["memory_percent"],
                        memory_used_gb=sm_data["memory_used_gb"],
                        memory_available_gb=sm_data["memory_available_gb"],
                        disk_usage_percent=sm_data["disk_usage_percent"],
                        disk_free_gb=sm_data["disk_free_gb"],
                        timestamp=datetime.fromisoformat(sm_data["timestamp"])
                    ))
                
                self.logger.debug(f"Métricas carregadas de: {self.metrics_file}")
                
        except Exception as e:
            self.logger.warning(f"Não foi possível carregar métricas: {e}")
    
    def _save_metrics(self) -> None:
        """Salva métricas em arquivo."""
        try:
            # Mantém apenas métricas recentes no arquivo
            recent_performance = self.performance_metrics[-200:]
            recent_operations = self.operation_metrics[-50:]
            recent_system = self.system_metrics[-20:]
            
            data = {
                "last_update": datetime.now().isoformat(),
                "performance_metrics": [
                    {
                        "name": m.name,
                        "value": m.value,
                        "unit": m.unit,
                        "timestamp": m.timestamp.isoformat(),
                        "metadata": m.metadata
                    }
                    for m in recent_performance
                ],
                "operation_metrics": [
                    {
                        "operation_type": op.operation_type,
                        "start_time": op.start_time,
                        "end_time": op.end_time,
                        "duration": op.duration,
                        "success": op.success,
                        "error_message": op.error_message,
                        "metadata": op.metadata
                    }
                    for op in recent_operations
                ],
                "system_metrics": [
                    {
                        "cpu_percent": sm.cpu_percent,
                        "memory_percent": sm.memory_percent,
                        "memory_used_gb": sm.memory_used_gb,
                        "memory_available_gb": sm.memory_available_gb,
                        "disk_usage_percent": sm.disk_usage_percent,
                        "disk_free_gb": sm.disk_free_gb,
                        "timestamp": sm.timestamp.isoformat()
                    }
                    for sm in recent_system
                ]
            }
            
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Erro ao salvar métricas: {e}")
    
    def _start_system_monitoring(self) -> None:
        """Inicia monitoramento do sistema em background."""
        def monitor_system():
            while True:
                try:
                    metrics = self.get_system_metrics()
                    with self._lock:
                        self.system_metrics.append(metrics)
                    
                    # Mantém apenas últimas 100 métricas do sistema
                    if len(self.system_metrics) > 100:
                        self.system_metrics = self.system_metrics[-100:]
                    
                    # Salva métricas periodicamente
                    self._save_metrics()
                    
                except Exception as e:
                    self.logger.error(f"Erro no monitoramento do sistema: {e}")
                
                time.sleep(30)  # Coleta a cada 30 segundos
        
        # Inicia thread de monitoramento
        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()
        
        self.logger.info("Monitoramento do sistema iniciado")


# Instância global do monitor
_global_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor(metrics_file: Optional[str] = None) -> PerformanceMonitor:
    """
    Obtém instância global do monitor de performance.
    
    Args:
        metrics_file: Arquivo para métricas
        
    Returns:
        Instância do PerformanceMonitor
    """
    global _global_monitor
    
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor(metrics_file)
    
    return _global_monitor


def monitor_operation(operation_type: str):
    """
    Decorator para monitorar operações automaticamente.
    
    Args:
        operation_type: Tipo da operação
        
    Returns:
        Decorator configurado
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            
            # Inicia monitoramento
            operation_id = monitor.start_operation(
                operation_type=operation_type,
                metadata={
                    "function": func.__name__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys())
                }
            )
            
            try:
                # Executa função
                result = func(*args, **kwargs)
                
                # Finaliza com sucesso
                monitor.end_operation(operation_id, success=True)
                
                return result
                
            except Exception as e:
                # Finaliza com erro
                monitor.end_operation(
                    operation_id, 
                    success=False, 
                    error_message=str(e)
                )
                raise
        
        return wrapper
    return decorator

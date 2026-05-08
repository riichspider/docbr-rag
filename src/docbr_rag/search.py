"""
Busca avançada com filtros para docbr-rag.
Implementa busca semântica com filtros estruturados.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from .models import TipoDocumento, Chunk, DocumentoInfo
from .logging_config import get_logger


class SearchType(Enum):
    """Tipos de busca."""
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


class FilterOperator(Enum):
    """Operadores de filtro."""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    GREATER_EQUAL = "gte"
    LESS_EQUAL = "lte"
    IN = "in"
    NOT_IN = "not_in"
    BETWEEN = "between"


@dataclass
class SearchFilter:
    """Filtro de busca."""
    field: str
    operator: FilterOperator
    value: Any
    case_sensitive: bool = False


@dataclass
class SearchQuery:
    """Consulta de busca avançada."""
    query: str
    search_type: SearchType = SearchType.SEMANTIC
    filters: List[SearchFilter] = None
    date_range: Optional[Tuple[datetime, datetime]] = None
    document_types: List[TipoDocumento] = None
    metadata_filters: Dict[str, Any] = None
    max_results: int = 10
    min_confidence: float = 0.0


@dataclass
class SearchResult:
    """Resultado de busca."""
    chunk: Chunk
    score: float
    document_info: DocumentoInfo
    matched_filters: List[str]
    explanation: str


class AdvancedSearch:
    """Motor de busca avançada para docbr-rag."""
    
    def __init__(self, collection, embedding_model):
        """
        Inicializa motor de busca avançada.
        
        Args:
            collection: Collection do ChromaDB
            embedding_model: Modelo de embeddings
        """
        self.collection = collection
        self.embedding_model = embedding_model
        self.logger = get_logger("docbr_rag.search")
    
    def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        Executa busca avançada com filtros.
        
        Args:
            query: Consulta de busca configurada
            
        Returns:
            Lista de resultados ordenados por relevância
        """
        self.logger.info(f"Executando busca: {query.query[:50]}...")
        
        # Gera embedding da query se necessário
        query_embedding = None
        if query.search_type in [SearchType.SEMANTIC, SearchType.HYBRID]:
            query_embedding = self.embedding_model.encode([query.query])
        
        # Constrói where clause para ChromaDB
        where_clause = self._build_where_clause(query)
        
        # Executa busca baseada no tipo
        if query.search_type == SearchType.SEMANTIC:
            results = self._semantic_search(query_embedding, where_clause, query)
        elif query.search_type == SearchType.KEYWORD:
            results = self._keyword_search(query.query, where_clause, query)
        else:  # HYBRID
            results = self._hybrid_search(
                query.query, query_embedding, where_clause, query
            )
        
        # Aplica filtros adicionais
        filtered_results = self._apply_filters(results, query)
        
        # Ordena e limita resultados
        sorted_results = sorted(
            filtered_results,
            key=lambda x: x.score,
            reverse=True
        )[:query.max_results]
        
        self.logger.info(f"Busca concluída: {len(sorted_results)} resultados")
        return sorted_results
    
    def _build_where_clause(self, query: SearchQuery) -> Dict[str, Any]:
        """
        Constrói where clause para ChromaDB.
        
        Args:
            query: Consulta de busca
            
        Returns:
            Dicionário com where clause
        """
        where_conditions = []
        
        # Filtros de tipo de documento
        if query.document_types:
            type_values = [t.value for t in query.document_types]
            where_conditions.append({
                "tipo_documento": {"$in": type_values}
            })
        
        # Filtros de data
        if query.date_range:
            start_date, end_date = query.date_range
            where_conditions.append({
                "data_criacao": {
                    "$gte": start_date.isoformat(),
                    "$lte": end_date.isoformat()
                }
            })
        
        # Filtros de metadados
        if query.metadata_filters:
            for field, value in query.metadata_filters.items():
                if isinstance(value, list):
                    where_conditions.append({field: {"$in": value}})
                else:
                    where_conditions.append({field: {"$eq": value}})
        
        # Combina todas as condições
        if len(where_conditions) == 1:
            return where_conditions[0]
        elif len(where_conditions) > 1:
            return {"$and": where_conditions}
        else:
            return {}
    
    def _semantic_search(
        self,
        query_embedding: List[float],
        where_clause: Dict[str, Any],
        query: SearchQuery
    ) -> List[SearchResult]:
        """
        Executa busca semântica.
        
        Args:
            query_embedding: Embedding da query
            where_clause: Filtros Where
            query: Consulta original
            
        Returns:
            Resultados da busca semântica
        """
        try:
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=query.max_results * 2,  # Busca mais para filtrar
                where=where_clause if where_clause else None,
                include=["metadatas", "documents", "distances"]
            )
            
            search_results = []
            
            for i, (doc, metadata, distance) in enumerate(zip(
                results["documents"][0],
                results["metadados"][0],
                results["distances"][0]
            )):
                # Calcula score (1 - distância normalizada)
                score = max(0, 1 - distance)
                
                # Verifica confiança mínima
                if score >= query.min_confidence:
                    # Cria chunk mockado
                    chunk = Chunk(
                        texto=doc,
                        pagina=metadata.get("pagina", 1),
                        indice=metadata.get("chunk_indice", i),
                        metadata=metadata
                    )
                    
                    # Cria info do documento
                    doc_info = DocumentoInfo(
                        tipo=TipoDocumento(metadata.get("tipo_documento", "desconhecido")),
                        caminho=metadata.get("documento", ""),
                        total_paginas=metadata.get("total_paginas", 1),
                        total_chunks=metadata.get("total_chunks", 1),
                        campos=metadata.get("campos", {}),
                        indexado=True
                    )
                    
                    result = SearchResult(
                        chunk=chunk,
                        score=score,
                        document_info=doc_info,
                        matched_filters=[],
                        explanation=f"Similaridade semântica: {score:.3f}"
                    )
                    
                    search_results.append(result)
            
            return search_results
            
        except Exception as e:
            self.logger.error(f"Erro na busca semântica: {e}")
            return []
    
    def _keyword_search(
        self,
        keyword: str,
        where_clause: Dict[str, Any],
        query: SearchQuery
    ) -> List[SearchResult]:
        """
        Executa busca por palavra-chave.
        
        Args:
            keyword: Palavra-chave
            where_clause: Filtros Where
            query: Consulta original
            
        Returns:
            Resultados da busca por palavra-chave
        """
        try:
            # Prepara termo de busca
            search_term = keyword if query.case_sensitive else keyword.lower()
            
            # Busca no ChromaDB
            results = self.collection.query(
                query_texts=[search_term],
                n_results=query.max_results * 2,
                where=where_clause if where_clause else None,
                include=["metadatas", "documents", "distances"]
            )
            
            search_results = []
            
            for i, (doc, metadata, distance) in enumerate(zip(
                results["documents"][0],
                results["metadados"][0],
                results["distances"][0]
            )):
                # Verifica se a palavra-chave realmente está no documento
                document_text = doc if query.case_sensitive else doc.lower()
                
                if search_term.lower() in document_text:
                    # Calcula score baseado na frequência e posição
                    score = self._calculate_keyword_score(document_text, search_term)
                    
                    if score >= query.min_confidence:
                        chunk = Chunk(
                            texto=doc,
                            pagina=metadata.get("pagina", 1),
                            indice=metadata.get("chunk_indice", i),
                            metadata=metadata
                        )
                        
                        doc_info = DocumentoInfo(
                            tipo=TipoDocumento(metadata.get("tipo_documento", "desconhecido")),
                            caminho=metadata.get("documento", ""),
                            total_paginas=metadata.get("total_paginas", 1),
                            total_chunks=metadata.get("total_chunks", 1),
                            campos=metadata.get("campos", {}),
                            indexado=True
                        )
                        
                        result = SearchResult(
                            chunk=chunk,
                            score=score,
                            document_info=doc_info,
                            matched_filters=["keyword"],
                            explanation=f"Palavra-chave encontrada: score {score:.3f}"
                        )
                        
                        search_results.append(result)
            
            return search_results
            
        except Exception as e:
            self.logger.error(f"Erro na busca por palavra-chave: {e}")
            return []
    
    def _hybrid_search(
        self,
        keyword: str,
        query_embedding: List[float],
        where_clause: Dict[str, Any],
        query: SearchQuery
    ) -> List[SearchResult]:
        """
        Executa busca híbrida (semântica + palavra-chave).
        
        Args:
            keyword: Palavra-chave
            query_embedding: Embedding da query
            where_clause: Filtros Where
            query: Consulta original
            
        Returns:
            Resultados da busca híbrida
        """
        # Executa ambos os tipos de busca
        semantic_results = self._semantic_search(query_embedding, where_clause, query)
        keyword_results = self._keyword_search(keyword, where_clause, query)
        
        # Combina resultados
        combined_results = {}
        
        # Adiciona resultados semânticos
        for result in semantic_results:
            key = f"{result.document_info.caminho}_{result.chunk.indice}"
            combined_results[key] = result
        
        # Adiciona resultados de palavra-chave
        for result in keyword_results:
            key = f"{result.document_info.caminho}_{result.chunk.indice}"
            if key in combined_results:
                # Combina scores (média ponderada)
                existing = combined_results[key]
                combined_score = (existing.score * 0.7 + result.score * 0.3)
                existing.score = combined_score
                existing.matched_filters.extend(result.matched_filters)
                existing.explanation = f"Híbrido: semântico {existing.score:.3f} + keyword {result.score:.3f}"
            else:
                result.matched_filters.append("keyword")
                result.explanation = f"Híbrido: keyword {result.score:.3f}"
                combined_results[key] = result
        
        return list(combined_results.values())
    
    def _apply_filters(
        self,
        results: List[SearchResult],
        query: SearchQuery
    ) -> List[SearchResult]:
        """
        Aplica filtros adicionais aos resultados.
        
        Args:
            results: Resultados da busca
            query: Consulta com filtros
            
        Returns:
            Resultados filtrados
        """
        if not query.filters:
            return results
        
        filtered_results = []
        
        for result in results:
            matched_filters = []
            all_filters_match = True
            
            for filter_obj in query.filters:
                if self._evaluate_filter(result, filter_obj):
                    matched_filters.append(filter_obj.field)
                else:
                    all_filters_match = False
                    break
            
            if all_filters_match:
                result.matched_filters = matched_filters
                filtered_results.append(result)
        
        return filtered_results
    
    def _evaluate_filter(
        self,
        result: SearchResult,
        filter_obj: SearchFilter
    ) -> bool:
        """
        Avalia se um resultado satisfaz um filtro.
        
        Args:
            result: Resultado da busca
            filter_obj: Filtro a avaliar
            
        Returns:
            True se o filtro for satisfeito
        """
        # Obtém valor do campo
        field_value = self._get_field_value(result, filter_obj.field)
        
        if field_value is None:
            return False
        
        # Aplica operador
        if filter_obj.operator == FilterOperator.EQUALS:
            return self._compare_values(field_value, filter_obj.value, "eq", filter_obj.case_sensitive)
        elif filter_obj.operator == FilterOperator.NOT_EQUALS:
            return not self._compare_values(field_value, filter_obj.value, "eq", filter_obj.case_sensitive)
        elif filter_obj.operator == FilterOperator.CONTAINS:
            return self._compare_values(field_value, filter_obj.value, "contains", filter_obj.case_sensitive)
        elif filter_obj.operator == FilterOperator.NOT_CONTAINS:
            return not self._compare_values(field_value, filter_obj.value, "contains", filter_obj.case_sensitive)
        elif filter_obj.operator == FilterOperator.GREATER_THAN:
            return self._compare_values(field_value, filter_obj.value, "gt")
        elif filter_obj.operator == FilterOperator.LESS_THAN:
            return self._compare_values(field_value, filter_obj.value, "lt")
        elif filter_obj.operator == FilterOperator.GREATER_EQUAL:
            return self._compare_values(field_value, filter_obj.value, "gte")
        elif filter_obj.operator == FilterOperator.LESS_EQUAL:
            return self._compare_values(field_value, filter_obj.value, "lte")
        elif filter_obj.operator == FilterOperator.IN:
            return field_value in filter_obj.value
        elif filter_obj.operator == FilterOperator.NOT_IN:
            return field_value not in filter_obj.value
        elif filter_obj.operator == FilterOperator.BETWEEN:
            min_val, max_val = filter_obj.value
            return min_val <= field_value <= max_val
        
        return False
    
    def _get_field_value(self, result: SearchResult, field: str) -> Any:
        """
        Obtém valor de um campo do resultado.
        
        Args:
            result: Resultado da busca
            field: Nome do campo
            
        Returns:
            Valor do campo
        """
        if field == "pagina":
            return result.chunk.pagina
        elif field == "tipo_documento":
            return result.document_info.tipo.value
        elif field == "documento":
            return result.document_info.caminho
        elif field == "total_paginas":
            return result.document_info.total_paginas
        elif field == "total_chunks":
            return result.document_info.total_chunks
        elif field in result.chunk.metadata:
            return result.chunk.metadata[field]
        else:
            return None
    
    def _compare_values(
        self,
        value1: Any,
        value2: Any,
        operation: str,
        case_sensitive: bool = False
    ) -> bool:
        """
        Compara dois valores baseado na operação.
        
        Args:
            value1: Primeiro valor
            value2: Segundo valor
            operation: Operação de comparação
            case_sensitive: Se diferencia maiúsculas/minúsculas
            
        Returns:
            Resultado da comparação
        """
        # Converte para strings se necessário
        if isinstance(value1, str) and isinstance(value2, str) and not case_sensitive:
            value1 = value1.lower()
            value2 = value2.lower()
        
        if operation == "eq":
            return value1 == value2
        elif operation == "contains":
            if isinstance(value1, str) and isinstance(value2, str):
                return value2 in value1
            return False
        elif operation == "gt":
            return value1 > value2
        elif operation == "lt":
            return value1 < value2
        elif operation == "gte":
            return value1 >= value2
        elif operation == "lte":
            return value1 <= value2
        
        return False
    
    def _calculate_keyword_score(self, text: str, keyword: str) -> float:
        """
        Calcula score de relevância para palavra-chave.
        
        Args:
            text: Texto do documento
            keyword: Palavra-chave
            
        Returns:
            Score de relevância (0-1)
        """
        # Frequência da palavra-chave
        keyword_lower = keyword.lower()
        text_lower = text.lower()
        
        frequency = text_lower.count(keyword_lower)
        text_length = len(text_lower.split())
        
        # Score baseado na frequência normalizada
        frequency_score = min(1.0, frequency / text_length)
        
        # Bônus se a palavra-chave aparece no início
        position_bonus = 0.0
        if keyword_lower in text_lower[:200]:  # Primeiros 200 caracteres
            position_bonus = 0.2
        
        # Bônus se for termo exato
        exact_match_bonus = 0.0
        if f" {keyword_lower} " in text_lower or text_lower.startswith(keyword_lower):
            exact_match_bonus = 0.1
        
        total_score = frequency_score + position_bonus + exact_match_bonus
        return min(1.0, total_score)
    
    def suggest_filters(self, query: str) -> List[SearchFilter]:
        """
        Sugere filtros baseados na query.
        
        Args:
            query: Query do usuário
            
        Returns:
            Lista de filtros sugeridos
        """
        suggestions = []
        
        # Detecta padrões de data
        date_patterns = [
            r'\d{2}/\d{2}/\d{4}',
            r'\d{4}-\d{2}-\d{2}',
            r'\d{2}/\d{2}/\d{2}'
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, query):
                suggestions.append(SearchFilter(
                    field="data_criacao",
                    operator=FilterOperator.CONTAINS,
                    value=re.findall(pattern, query)[0]
                ))
        
        # Detecta padrões monetários
        if re.search(r'R?\$\s*\d+', query):
            suggestions.append(SearchFilter(
                field="valor",
                operator=FilterOperator.GREATER_THAN,
                value=0
            ))
        
        # Detecta tipos de documento
        for tipo in TipoDocumento:
            if tipo.value.lower() in query.lower():
                suggestions.append(SearchFilter(
                    field="tipo_documento",
                    operator=FilterOperator.EQUALS,
                    value=tipo.value
                ))
        
        return suggestions

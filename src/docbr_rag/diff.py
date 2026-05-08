"""
Sistema de comparação e diff para documentos no docbr-rag.
Compara versões de documentos e destaca diferenças.
"""

import difflib
from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import re

from .models import DocumentoInfo, TipoDocumento
from .logging_config import get_logger


@dataclass
class DiffResult:
    """Resultado da comparação de documentos."""
    documento1: str
    documento2: str
    similaridade: float
    diferencas: List[Dict[str, Any]]
    timestamp: datetime
    metadados: Dict[str, Any] = None


@dataclass
class DocumentVersion:
    """Versão de um documento."""
    versao: str
    timestamp: datetime
    caminho: str
    tipo: TipoDocumento
    metadados: Dict[str, Any]
    checksum: str


class DocumentComparator:
    """Comparador de documentos com diff inteligente."""
    
    def __init__(self):
        """Inicializa comparador de documentos."""
        self.logger = get_logger("docbr_rag.diff")
    
    def compare_documents(
        self,
        doc1_path: str,
        doc2_path: str,
        extract_func1: callable,
        extract_func2: Optional[callable] = None
    ) -> DiffResult:
        """
        Compara dois documentos completos.
        
        Args:
            doc1_path: Caminho do primeiro documento
            doc2_path: Caminho do segundo documento
            extract_func1: Função de extração para doc1
            extract_func2: Função de extração para doc2 (opcional)
            
        Returns:
            Resultado da comparação
        """
        self.logger.info(f"Comparando documentos: {doc1_path} vs {doc2_path}")
        
        try:
            # Extrai textos
            if extract_func2 is None:
                extract_func2 = extract_func1
            
            paginas1 = extract_func1(doc1_path)
            paginas2 = extract_func2(doc2_path)
            
            # Converte para texto completo
            texto1 = self._paginas_para_texto(paginas1)
            texto2 = self._paginas_para_texto(paginas2)
            
            # Calcula similaridade
            similaridade = self._calcular_similaridade(texto1, texto2)
            
            # Gera diff
            diferencas = self._gerar_diff_paginas(paginas1, paginas2)
            
            # Metadados da comparação
            metadados = {
                "doc1_paginas": len(paginas1),
                "doc2_paginas": len(paginas2),
                "doc1_caracteres": len(texto1),
                "doc2_caracteres": len(texto2),
                "metodo_comparacao": "texto_completo"
            }
            
            result = DiffResult(
                documento1=doc1_path,
                documento2=doc2_path,
                similaridade=similaridade,
                diferencas=diferencas,
                timestamp=datetime.now(),
                metadados=metadados
            )
            
            self.logger.info(f"Comparação concluída: similaridade {similaridade:.2f}")
            return result
            
        except Exception as e:
            self.logger.error(f"Erro na comparação: {e}")
            raise
    
    def compare_chunks(
        self,
        chunks1: List[str],
        chunks2: List[str],
        threshold: float = 0.8
    ) -> DiffResult:
        """
        Compara listas de chunks de texto.
        
        Args:
            chunks1: Chunks do primeiro documento
            chunks2: Chunks do segundo documento
            threshold: Limiar de similaridade
            
        Returns:
            Resultado da comparação
        """
        self.logger.info(f"Comparando {len(chunks1)} vs {len(chunks2)} chunks")
        
        try:
            texto1 = "\n".join(chunks1)
            texto2 = "\n".join(chunks2)
            
            similaridade = self._calcular_similaridade(texto1, texto2)
            
            # Gera diff por chunks
            diferencas = self._gerar_diff_chunks(chunks1, chunks2, threshold)
            
            metadados = {
                "doc1_chunks": len(chunks1),
                "doc2_chunks": len(chunks2),
                "threshold": threshold,
                "metodo_comparacao": "chunks"
            }
            
            return DiffResult(
                documento1="chunks1",
                documento2="chunks2",
                similaridade=similaridade,
                diferencas=diferencas,
                timestamp=datetime.now(),
                metadados=metadados
            )
            
        except Exception as e:
            self.logger.error(f"Erro na comparação de chunks: {e}")
            raise
    
    def compare_structured_data(
        self,
        data1: Dict[str, Any],
        data2: Dict[str, Any],
        keys_importantes: Optional[List[str]] = None
    ) -> DiffResult:
        """
        Compara dados estruturados (metadados, campos extraídos).
        
        Args:
            data1: Dados do primeiro documento
            data2: Dados do segundo documento
            keys_importantes: Chaves importantes para comparar
            
        Returns:
            Resultado da comparação
        """
        self.logger.info("Comparando dados estruturados")
        
        try:
            # Se não especificar, usa todas as chaves
            if keys_importantes is None:
                keys_importantes = list(set(data1.keys()) | set(data2.keys()))
            
            diferencas = []
            campos_iguais = 0
            
            for key in keys_importantes:
                val1 = data1.get(key)
                val2 = data2.get(key)
                
                if val1 == val2:
                    campos_iguais += 1
                else:
                    diferencas.append({
                        "campo": key,
                        "valor1": val1,
                        "valor2": val2,
                        "tipo_diferenca": self._classificar_diferenca(val1, val2)
                    })
            
            # Calcula similaridade baseada em campos iguais
            similaridade = campos_iguais / len(keys_importantes) if keys_importantes else 1.0
            
            metadados = {
                "campos_comparados": len(keys_importantes),
                "campos_iguais": campos_iguais,
                "campos_diferentes": len(diferencas),
                "metodo_comparacao": "dados_estruturados"
            }
            
            return DiffResult(
                documento1="data1",
                documento2="data2",
                similaridade=similaridade,
                diferencas=diferencas,
                timestamp=datetime.now(),
                metadados=metadados
            )
            
        except Exception as e:
            self.logger.error(f"Erro na comparação estruturada: {e}")
            raise
    
    def _paginas_para_texto(self, paginas: List[Tuple[int, str]]) -> str:
        """
        Converte lista de páginas para texto único.
        
        Args:
            paginas: Lista de tuplas (número, texto)
            
        Returns:
            Texto completo com marcadores de página
        """
        texto_completo = []
        
        for num_pagina, texto in paginas:
            if texto.strip():
                texto_completo.append(f"[PÁGINA {num_pagina}]")
                texto_completo.append(texto)
                texto_completo.append("")
        
        return "\n".join(texto_completo)
    
    def _calcular_similaridade(self, texto1: str, texto2: str) -> float:
        """
        Calcula similaridade entre dois textos.
        
        Args:
            texto1: Primeiro texto
            texto2: Segundo texto
            
        Returns:
            Similaridade entre 0 e 1
        """
        # Usa SequenceMatcher do difflib
        matcher = difflib.SequenceMatcher(None, texto1, texto2)
        similaridade = matcher.ratio()
        
        # Ajuste fino para documentos brasileiros
        # Considera similaridade de termos importantes
        termos_br = [
            "contrato", "cláusula", "vigência", "foro",
            "nota fiscal", "cnpj", "chave de acesso",
            "boleto", "vencimento", "nosso número",
            "laudo", "perito", "conclusão",
            "certidão", "cartório", "registro civil",
            "holerite", "inss", "fgts"
        ]
        
        # Bônus para termos brasileiros similares
        bonus = 0.0
        for termo in termos_br:
            if termo in texto1.lower() and termo in texto2.lower():
                bonus += 0.01
        
        return min(1.0, similaridade + bonus)
    
    def _gerar_diff_paginas(
        self,
        paginas1: List[Tuple[int, str]],
        paginas2: List[Tuple[int, str]]
    ) -> List[Dict[str, Any]]:
        """
        Gera diff página por página.
        
        Args:
            paginas1: Páginas do primeiro documento
            paginas2: Páginas do segundo documento
            
        Returns:
            Lista de diferenças por página
        """
        diferencas = []
        max_paginas = max(len(paginas1), len(paginas2))
        
        for i in range(max_paginas):
            texto1 = paginas1[i][1] if i < len(paginas1) else ""
            texto2 = paginas2[i][1] if i < len(paginas2) else ""
            
            if texto1.strip() or texto2.strip():
                diff_info = self._gerar_diff_texto(texto1, texto2)
                
                if diff_info["tem_diferencas"]:
                    diferencas.append({
                        "pagina": i + 1,
                        "tipo": "pagina",
                        "diff_unified": diff_info["diff_unified"],
                        "diff_html": diff_info["diff_html"],
                        "estatisticas": diff_info["estatisticas"],
                        "texto1": texto1[:200] + "..." if len(texto1) > 200 else texto1,
                        "texto2": texto2[:200] + "..." if len(texto2) > 200 else texto2
                    })
        
        return diferencas
    
    def _gerar_diff_chunks(
        self,
        chunks1: List[str],
        chunks2: List[str],
        threshold: float
    ) -> List[Dict[str, Any]]:
        """
        Gera diff para chunks com limiar de similaridade.
        
        Args:
            chunks1: Chunks do primeiro documento
            chunks2: Chunks do segundo documento
            threshold: Limiar de similaridade
            
        Returns:
            Lista de diferenças
        """
        diferencas = []
        max_chunks = max(len(chunks1), len(chunks2))
        
        for i in range(max_chunks):
            chunk1 = chunks1[i] if i < len(chunks1) else ""
            chunk2 = chunks2[i] if i < len(chunks2) else ""
            
            if chunk1.strip() or chunk2.strip():
                # Calcula similaridade do chunk
                similaridade = self._calcular_similaridade(chunk1, chunk2)
                
                if similaridade < threshold:
                    diff_info = self._gerar_diff_texto(chunk1, chunk2)
                    
                    diferencas.append({
                        "chunk": i + 1,
                        "tipo": "chunk",
                        "similaridade": similaridade,
                        "diff_unified": diff_info["diff_unified"],
                        "diff_html": diff_info["diff_html"],
                        "estatisticas": diff_info["estatisticas"],
                        "texto1": chunk1,
                        "texto2": chunk2
                    })
        
        return diferencas
    
    def _gerar_diff_texto(self, texto1: str, texto2: str) -> Dict[str, Any]:
        """
        Gera diff entre dois textos.
        
        Args:
            texto1: Primeiro texto
            texto2: Segundo texto
            
        Returns:
            Dicionário com informações do diff
        """
        # Diff unificado
        diff_unified = list(difflib.unified_diff(
            texto1.splitlines(),
            texto2.splitlines(),
            fromfile="Documento 1",
            tofile="Documento 2",
            lineterm=""
        ))
        
        # Diff HTML
        differ = difflib.HtmlDiff()
        diff_html = differ.make_file(
            texto1.splitlines(),
            texto2.splitlines()
        )
        
        # Estatísticas do diff
        linhas1 = set(texto1.splitlines())
        linhas2 = set(texto2.splitlines())
        
        estatisticas = {
            "linhas_adicionadas": len(linhas2 - linhas1),
            "linhas_removidas": len(linhas1 - linhas2),
            "linhas_modificadas": len(linhas1 & linhas2) - len(
                set(line.strip() for line in texto1.splitlines()) & 
                set(line.strip() for line in texto2.splitlines())
            ),
            "total_linhas_doc1": len(texto1.splitlines()),
            "total_linhas_doc2": len(texto2.splitlines()),
            "caracteres_adicionados": len(texto2) - len(texto1) if len(texto2) > len(texto1) else 0,
            "caracteres_removidos": len(texto1) - len(texto2) if len(texto1) > len(texto2) else 0
        }
        
        tem_diferencas = (
            estatisticas["linhas_adicionadas"] > 0 or
            estatisticas["linhas_removidas"] > 0 or
            estatisticas["linhas_modificadas"] > 0
        )
        
        return {
            "diff_unified": "\n".join(diff_unified),
            "diff_html": diff_html,
            "estatisticas": estatisticas,
            "tem_diferencas": tem_diferencas
        }
    
    def _classificar_diferenca(self, valor1: Any, valor2: Any) -> str:
        """
        Classifica o tipo de diferença entre dois valores.
        
        Args:
            valor1: Primeiro valor
            valor2: Segundo valor
            
        Returns:
            Tipo da diferença
        """
        if valor1 is None and valor2 is not None:
            return "adicionado"
        elif valor1 is not None and valor2 is None:
            return "removido"
        elif str(valor1) != str(valor2):
            # Tenta classificar por tipo de dado
            if isinstance(valor1, (int, float)) and isinstance(valor2, (int, float)):
                if valor2 > valor1:
                    return "valor_aumentado"
                else:
                    return "valor_diminuido"
            elif isinstance(valor1, str) and isinstance(valor2, str):
                if len(valor2) > len(valor1):
                    return "texto_expandido"
                elif len(valor2) < len(valor1):
                    return "texto_reduzido"
                else:
                    return "texto_modificado"
            else:
                return "tipo_modificado"
        
        return "igual"


class DocumentVersionManager:
    """Gerenciador de versões de documentos."""
    
    def __init__(self, storage_path: str = "./document_versions"):
        """
        Inicializa gerenciador de versões.
        
        Args:
            storage_path: Caminho para armazenar versões
        """
        self.storage_path = storage_path
        self.logger = get_logger("docbr_rag.versioning")
        
        # Cria diretório de armazenamento
        import os
        os.makedirs(storage_path, exist_ok=True)
    
    def save_version(
        self,
        documento_path: str,
        versao: str,
        tipo: TipoDocumento,
        metadados: Dict[str, Any]
    ) -> DocumentVersion:
        """
        Salva uma nova versão do documento.
        
        Args:
            documento_path: Caminho do documento
            versao: Número da versão
            tipo: Tipo do documento
            metadados: Metadados do documento
            
        Returns:
            Informações da versão salva
        """
        import hashlib
        import json
        
        try:
            # Calcula checksum do documento
            with open(documento_path, 'rb') as f:
                checksum = hashlib.md5(f.read()).hexdigest()
            
            # Cria objeto de versão
            version_info = DocumentVersion(
                versao=versao,
                timestamp=datetime.now(),
                caminho=documento_path,
                tipo=tipo,
                metadados=metadados,
                checksum=checksum
            )
            
            # Salva em arquivo JSON
            version_file = f"{self.storage_path}/{Path(documento_path).stem}_versions.json"
            
            # Carrega versões existentes
            versions = []
            if Path(version_file).exists():
                with open(version_file, 'r', encoding='utf-8') as f:
                    versions = json.load(f)
            
            # Adiciona nova versão
            versions.append({
                "versao": versao,
                "timestamp": version_info.timestamp.isoformat(),
                "caminho": documento_path,
                "tipo": tipo.value,
                "metadados": metadados,
                "checksum": checksum
            })
            
            # Salva todas as versões
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(versions, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Versão {versao} salva para {documento_path}")
            return version_info
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar versão: {e}")
            raise
    
    def get_versions(self, documento_path: str) -> List[DocumentVersion]:
        """
        Obtém todas as versões de um documento.
        
        Args:
            documento_path: Caminho do documento
            
        Returns:
            Lista de versões
        """
        import json
        
        version_file = f"{self.storage_path}/{Path(documento_path).stem}_versions.json"
        
        if not Path(version_file).exists():
            return []
        
        try:
            with open(version_file, 'r', encoding='utf-8') as f:
                versions_data = json.load(f)
            
            versions = []
            for version_data in versions_data:
                version = DocumentVersion(
                    versao=version_data["versao"],
                    timestamp=datetime.fromisoformat(version_data["timestamp"]),
                    caminho=version_data["caminho"],
                    tipo=TipoDocumento(version_data["tipo"]),
                    metadados=version_data["metadados"],
                    checksum=version_data["checksum"]
                )
                versions.append(version)
            
            # Ordena por timestamp
            versions.sort(key=lambda x: x.timestamp)
            return versions
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar versões: {e}")
            return []
    
    def compare_versions(
        self,
        documento_path: str,
        versao1: str,
        versao2: str,
        comparator: DocumentComparator
    ) -> DiffResult:
        """
        Compara duas versões de um documento.
        
        Args:
            documento_path: Caminho do documento
            versao1: Primeira versão
            versao2: Segunda versão
            comparator: Comparador de documentos
            
        Returns:
            Resultado da comparação
        """
        versions = self.get_versions(documento_path)
        
        # Encontra as versões solicitadas
        version1_info = next((v for v in versions if v.versao == versao1), None)
        version2_info = next((v for v in versions if v.versao == versao2), None)
        
        if not version1_info or not version2_info:
            raise ValueError(f"Versões não encontradas: {versao1}, {versao2}")
        
        # Compara os documentos
        return comparator.compare_documents(
            version1_info.caminho,
            version2_info.caminho
        )

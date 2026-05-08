"""
Exemplo de processamento em lote de múltiplos documentos.
Demonstra como indexar vários PDFs e fazer consultas cruzadas.
"""

from pathlib import Path
from typing import List
from src.docbr_rag import DocBR
from src.docbr_rag.models import TipoDocumento

def encontrar_pdfs(diretorio: str) -> List[Path]:
    """Encontra todos os PDFs em um diretório."""
    path = Path(diretorio)
    return list(path.glob("*.pdf"))

def main():
    # Inicializa o sistema
    docbr = DocBR(
        model_name="all-MiniLM-L6-v2",
        llm_model="llama3.2:3b",
        db_path="./lote_db",
        chunk_size=600,  # Maior para documentos complexos
        chunk_overlap=150
    )
    
    # Diretório com documentos
    diretorio_documentos = "./documentos"  # Crie este diretório
    
    # Encontra todos os PDFs
    pdfs = encontrar_pdfs(diretorio_documentos)
    
    if not pdfs:
        print(f"❌ Nenhum PDF encontrado em: {diretorio_documentos}")
        print("Crie o diretório e coloque alguns PDFs brasileiros para testar.")
        return
    
    print(f"📁 Encontrados {len(pdfs)} PDFs para processar")
    print("=" * 50)
    
    # Indexa cada documento
    documentos_indexados = []
    
    for pdf in pdfs:
        try:
            print(f"📄 Processando: {pdf.name}")
            doc_info = docbr.indexar_documento(pdf)
            documentos_indexados.append(doc_info)
            
            print(f"   ✅ {doc_info.tipo.value.upper()} - {doc_info.total_paginas} páginas")
            
        except Exception as e:
            print(f"   ❌ Erro: {e}")
    
    print(f"\n🎯 Total de {len(documentos_indexados)} documentos indexados")
    
    # Estatísticas por tipo
    tipos = {}
    for doc in documentos_indexados:
        tipos[doc.tipo.value] = tipos.get(doc.tipo.value, 0) + 1
    
    print("\n📊 Estatísticas por tipo:")
    for tipo, quantidade in tipos.items():
        print(f"   {tipo}: {quantidade} documento(s)")
    
    # Consultas cruzadas
    print("\n🔍 Consultas cruzadas entre documentos:")
    print("=" * 50)
    
    consultas = [
        "Quais contratos têm cláusula de confidencialidade?",
        "Existem boletos com vencimento em atraso?",
        "Quais laudos mencionam análise estrutural?",
        "Quais documentos têm valor financeiro acima de R$ 10.000?",
        "Existem certidões emitidas nos últimos 30 dias?"
    ]
    
    for consulta in consultas:
        print(f"\n❓ {consulta}")
        resposta = docbr.consultar(consulta, n_resultados=8)  # Mais resultados para consultas cruzadas
        
        print(f"📝 {resposta.texto}")
        if resposta.paginas_referenciadas:
            print(f"📄 Fontes: {len(resposta.paginas_referenciadas)} páginas")
        if resposta.confianca:
            print(f"🎯 Confiança: {resposta.confianca:.2f}")
        print("-" * 40)
    
    # Lista todos os documentos indexados
    print("\n📋 Todos os documentos indexados:")
    todos = docbr.listar_documentos()
    for i, doc in enumerate(todos, 1):
        print(f"{i:2d}. {doc.tipo.value:12s} - {Path(doc.caminho).name}")

if __name__ == "__main__":
    main()

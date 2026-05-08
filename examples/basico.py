"""
Exemplo básico de uso do docbr-rag.
Indexa um documento e faz consultas simples.
"""

from pathlib import Path
from src.docbr_rag import DocBR

def main():
    # Inicializa o sistema RAG
    docbr = DocBR(
        model_name="all-MiniLM-L6-v2",  # Modelo de embeddings
        llm_model="llama3.2:3b",         # Modelo de linguagem local
        db_path="./exemplo_db"           # Banco de dados local
    )
    
    # Caminho para um documento PDF brasileiro
    caminho_documento = "contrato_exemplo.pdf"  # Substitua com seu arquivo
    
    if Path(caminho_documento).exists():
        print(f"📄 Indexando documento: {caminho_documento}")
        
        # Indexa o documento
        doc_info = docbr.indexar_documento(caminho_documento)
        
        print(f"✅ Documento indexado!")
        print(f"   Tipo: {doc_info.tipo.value}")
        print(f"   Páginas: {doc_info.total_paginas}")
        print(f"   Chunks: {doc_info.total_chunks}")
        
        # Exemplos de consultas
        perguntas = [
            "Qual o objeto principal deste documento?",
            "Quais são as partes envolvidas?",
            "Existem cláusulas de penalidade?",
            "Qual é a vigência do contrato?"
        ]
        
        print("\n🔍 Realizando consultas:")
        print("=" * 50)
        
        for pergunta in perguntas:
            print(f"\n❓ {pergunta}")
            resposta = docbr.consultar(pergunta)
            
            print(f"📝 {resposta.texto}")
            if resposta.paginas_referenciadas:
                print(f"📄 Páginas: {', '.join(map(str, resposta.paginas_referenciadas))}")
            if resposta.confianca:
                print(f"🎯 Confiança: {resposta.confianca:.2f}")
            print("-" * 30)
    else:
        print(f"❌ Arquivo não encontrado: {caminho_documento}")
        print("Coloque um arquivo PDF brasileiro no mesmo diretório e atualize o nome do arquivo.")

if __name__ == "__main__":
    main()

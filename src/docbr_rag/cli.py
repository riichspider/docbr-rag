"""
Interface de linha de comando para docbr-rag.
"""

import typer
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .core import DocBR

app = typer.Typer(help="docbr-rag: RAG especializado em documentos brasileiros")
console = Console()


@app.command()
def indexar(
    arquivo: str = typer.Argument(..., help="Caminho para o arquivo PDF a ser indexado"),
    modelo_embeddings: str = typer.Option("all-MiniLM-L6-v2", help="Modelo de embeddings"),
    modelo_llm: str = typer.Option("llama3.2:3b", help="Modelo de linguagem"),
    db_path: str = typer.Option("./docbr_db", help="Caminho para o banco de dados"),
):
    """Indexa um documento PDF para consulta."""
    caminho = Path(arquivo)
    
    if not caminho.exists():
        console.print(f"[red]Erro: Arquivo não encontrado: {arquivo}[/red]")
        raise typer.Exit(1)
    
    if not caminho.suffix.lower() == ".pdf":
        console.print(f"[red]Erro: Arquivo deve ser PDF: {arquivo}[/red]")
        raise typer.Exit(1)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Inicializando sistema...", total=None)
        
        docbr = DocBR(
            model_name=modelo_embeddings,
            llm_model=modelo_llm,
            db_path=db_path
        )
        
        progress.update(task, description="Indexando documento...")
        
        try:
            doc_info = docbr.indexar_documento(caminho)
            
            console.print("[green]✓[/green] Documento indexado com sucesso!")
            console.print(f"  • Tipo: {doc_info.tipo.value}")
            console.print(f"  • Páginas: {doc_info.total_paginas}")
            console.print(f"  • Chunks: {doc_info.total_chunks}")
            
        except Exception as e:
            console.print(f"[red]Erro ao indexar documento: {e}[/red]")
            raise typer.Exit(1)


@app.command()
def consultar(
    pergunta: str = typer.Argument(..., help="Pergunta sobre os documentos"),
    modelo_embeddings: str = typer.Option("all-MiniLM-L6-v2", help="Modelo de embeddings"),
    modelo_llm: str = typer.Option("llama3.2:3b", help="Modelo de linguagem"),
    db_path: str = typer.Option("./docbr_db", help="Caminho para o banco de dados"),
    n_resultados: int = typer.Option(5, help="Número de resultados"),
):
    """Consulta os documentos indexados."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Inicializando sistema...", total=None)
        
        docbr = DocBR(
            model_name=modelo_embeddings,
            llm_model=modelo_llm,
            db_path=db_path
        )
        
        progress.update(task, description="Buscando informações...")
        
        try:
            resposta = docbr.consultar(pergunta, n_resultados=n_resultados)
            
            console.print(f"\n[bold]Pergunta:[/bold] {pergunta}")
            console.print(f"\n[bold]Resposta:[/bold] {resposta.texto}")
            
            if resposta.paginas_referenciadas:
                console.print(f"\n[dim]Páginas referenciadas: {', '.join(map(str, resposta.paginas_referenciadas))}[/dim]")
            
            if resposta.confianca is not None:
                console.print(f"[dim]Confiança: {resposta.confianca:.2f}[/dim]")
                
        except Exception as e:
            console.print(f"[red]Erro ao consultar: {e}[/red]")
            raise typer.Exit(1)


@app.command()
def listar(
    db_path: str = typer.Option("./docbr_db", help="Caminho para o banco de dados"),
):
    """Lista todos os documentos indexados."""
    try:
        docbr = DocBR(db_path=db_path)
        documentos = docbr.listar_documentos()
        
        if not documentos:
            console.print("[yellow]Nenhum documento indexado encontrado.[/yellow]")
            return
        
        console.print(f"[bold]Documentos indexados ({len(documentos)}):[/bold]")
        for doc in documentos:
            status = "✓" if doc.indexado else "✗"
            console.print(f"  {status} {doc.tipo.value.upper()} - {Path(doc.caminho).name}")
            console.print(f"    Páginas: {doc.total_paginas} | Chunks: {doc.total_chunks}")
            
    except Exception as e:
        console.print(f"[red]Erro ao listar documentos: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def limpar(
    db_path: str = typer.Option("./docbr_db", help="Caminho para o banco de dados"),
    confirmar: bool = typer.Option(False, "--confirmar", help="Confirma a limpeza"),
):
    """Remove todos os documentos do banco de dados."""
    if not confirmar:
        console.print("[red]Use --confirmar para realmente limpar o banco de dados.[/red]")
        raise typer.Exit(1)
    
    try:
        docbr = DocBR(db_path=db_path)
        docbr.limpar_database()
        console.print("[green]✓[/green] Banco de dados limpo com sucesso!")
        
    except Exception as e:
        console.print(f"[red]Erro ao limpar banco de dados: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
